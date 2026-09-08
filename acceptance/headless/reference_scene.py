"""Validate the fixed headless scene and render verified direct-x86 output.

This module is a host-side acceptance oracle.  It is not the implementation of
complex arithmetic used by a generated program.  The direct x86 backend owns
that implementation; this repository owns the scene and rendering boundary it
must consume.
"""

from __future__ import annotations

import argparse
import cmath
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from typing import Any, Iterable


SCHEMA = "analytic-continuation/headless-complex-reference/v1"
OUTPUT_MAGIC = b"ACPHF32\0"
OUTPUT_VERSION = 1
OUTPUT_HEADER = struct.Struct("<8s8I32s32s24s24s8s")
OUTPUT_HEADER_BYTES = OUTPUT_HEADER.size
OUTPUT_SAMPLE = struct.Struct("<ff")
OUTPUT_SAMPLE_BYTES = OUTPUT_SAMPLE.size
F32_WORD = re.compile(r"0x[0-9a-f]{8}\Z")
WEGERT_CORE_RELATIVE = Path("android/app/src/main/assets/wegert_color.glsl")
WEGERT_TAU = 6.28318530717958647692
WEGERT_LOG_10 = 2.30258509299404568402
PPM_MAX_VALUE = 255

# The generated v1 scene is a scalar-SSE binary32 program.  These are not
# fitted tolerances: the operation counts below are obtained directly from the
# closed lowering described in acceptance/headless/README.md.  The factor
# product contribution is added from the scene's declared multiplicities.
F32_UNIT_ROUNDOFF = 2.0**-24
F32_FIXED_ROUNDED_OPERATIONS = {
    "pixel_coordinates": 2,
    "q_horner": 40,
    "complex_exponential": 39,
    "numerator_exponential_product": 6,
    "projective_rescaling": 12,
    "homogeneous_zero_checks": 6,
    "scaled_affine_division": 15,
    "affine_squared_magnitude": 3,
    "logarithm": 17,
    "atan2": 18,
}
# A real component path is counted once above.  Paying the count once more is
# the normwise projection allowance for a two-component complex value.
F32_COMPLEX_PROJECTION_FACTOR = 2
F32_LN2 = struct.unpack(">f", bytes.fromhex("3f317218"))[0]
F32_PI_OVER_4 = struct.unpack(">f", bytes.fromhex("3f490fdb"))[0]
F32_PI_OVER_2 = struct.unpack(">f", bytes.fromhex("3fc90fdb"))[0]
F32_PI = struct.unpack(">f", bytes.fromhex("40490fdb"))[0]


class ContractError(ValueError):
    """The scene or a purported runner result violates the closed contract."""


@dataclass(frozen=True)
class NumericErrorBudget:
    """Derived absolute error bounds for one phase/log sample.

    ``relative_value`` bounds the perturbation of the computed nonzero complex
    affine value.  ``phase`` and ``log_magnitude`` additionally include the
    emitted atan/log approximation and reduction-constant errors.
    """

    rounded_operations: int
    gamma: float
    q_absolute_bound: float
    transcendental_argument_bound: float
    relative_value: float
    phase: float
    log_magnitude: float


def _closed_object(value: Any, keys: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{where} must be an object")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        unknown = sorted(actual - keys)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if unknown:
            details.append(f"unknown {', '.join(unknown)}")
        raise ContractError(f"{where}: {'; '.join(details)}")
    return value


def decode_f32(word: Any, where: str) -> float:
    """Decode the fixture's canonical big-endian spelling of F32 bits."""

    if not isinstance(word, str) or F32_WORD.fullmatch(word) is None:
        raise ContractError(f"{where} must be 0x followed by eight lowercase hex digits")
    value = struct.unpack(">f", bytes.fromhex(word[2:]))[0]
    if not math.isfinite(value):
        raise ContractError(f"{where} must be finite")
    return value


def decode_complex(words: Any, where: str) -> complex:
    if not isinstance(words, list) or len(words) != 2:
        raise ContractError(f"{where} must be [real_bits, imaginary_bits]")
    return complex(
        decode_f32(words[0], f"{where}[0]"),
        decode_f32(words[1], f"{where}[1]"),
    )


def _validate_header_id(value: Any, width: int, where: str) -> str:
    if not isinstance(value, str) or not value or "\0" in value:
        raise ContractError(f"{where} must be a nonempty, NUL-free string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ContractError(f"{where} must be UTF-8 encodable") from error
    if len(encoded) >= width:
        raise ContractError(f"{where} must fit a {width}-byte NUL-terminated field")
    return value


def _validate_factor_list(value: Any, where: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ContractError(f"{where} must be a list")
    factors = []
    for index, raw in enumerate(value):
        factor = _closed_object(raw, {"position", "multiplicity"}, f"{where}[{index}]")
        decode_complex(factor["position"], f"{where}[{index}].position")
        multiplicity = factor["multiplicity"]
        if (
            isinstance(multiplicity, bool)
            or not isinstance(multiplicity, int)
            or multiplicity <= 0
        ):
            raise ContractError(f"{where}[{index}].multiplicity must be positive")
        factors.append(factor)
    return factors


def _factor_positions(factors: Iterable[dict[str, Any]], where: str) -> set[complex]:
    return {
        decode_complex(factor["position"], f"{where}[{index}].position")
        for index, factor in enumerate(factors)
    }


def scene_state(scene: dict[str, Any], state_id: str) -> dict[str, Any]:
    for state in scene["states"]:
        if state["id"] == state_id:
            return state
    raise ContractError(f"unknown state id {state_id!r}")


def scene_representative(scene: dict[str, Any], representative_id: str) -> dict[str, Any]:
    for representative in scene["representatives"]:
        if representative["id"] == representative_id:
            return representative
    raise ContractError(f"unknown representative id {representative_id!r}")


def pixel_coordinate(scene: dict[str, Any], x: int, y: int) -> complex:
    viewport = scene["viewport"]
    width = viewport["width"]
    height = viewport["height"]
    if not 0 <= x < width or not 0 <= y < height:
        raise ContractError("pixel coordinate is outside the scene")
    # The v1 dimensions and bounds reduce to dyadic coordinates. Keep the
    # reduced form explicit so every declared Float32 backend starts from the
    # same exactly representable samples.
    return complex((2 * x - 95) / 32.0, (63 - 2 * y) / 32.0)


def q_value(scene: dict[str, Any], state: dict[str, Any], z: complex) -> complex:
    """Binary64 oracle for the polynomial whose inputs are fixed F32 values."""

    scale = decode_f32(scene["function"]["q"]["coordinate_scale"], "q.coordinate_scale")
    u = z / scale
    power = u
    result = 0j
    for index, words in enumerate(state["q_coefficients"]):
        result += decode_complex(words, f"q_coefficients[{index}]") * power
        power *= u
    return result


def _gamma(operation_count: int) -> float:
    """Higham's gamma_n bound for nearest-even binary32 operations."""

    product = operation_count * F32_UNIT_ROUNDOFF
    if product >= 1.0:
        raise ContractError("scene has too many rounded operations for a gamma_n bound")
    return product / (1.0 - product)


def _rounded_operation_count(scene: dict[str, Any]) -> int:
    # Each factor contributes one complex subtraction (two rounded scalar
    # operations), followed by six rounded scalar operations per complex
    # multiplication in the declared multiplicity.
    factor_operations = sum(
        2 + 6 * factor["multiplicity"]
        for kind in ("zeros", "poles")
        for factor in scene["function"][kind]
    )
    scalar_path = sum(F32_FIXED_ROUNDED_OPERATIONS.values()) + factor_operations
    return F32_COMPLEX_PROJECTION_FACTOR * scalar_path


def _q_absolute_bound(scene: dict[str, Any]) -> float:
    """Bound |q(z)| using the coefficient L1 envelope and |z/6| < 1."""

    viewport = scene["viewport"]
    radius = math.hypot(
        max(abs(decode_f32(viewport["minimum_real"], "viewport.minimum_real")),
            abs(decode_f32(viewport["maximum_real"], "viewport.maximum_real"))),
        max(abs(decode_f32(viewport["minimum_imaginary"], "viewport.minimum_imaginary")),
            abs(decode_f32(viewport["maximum_imaginary"], "viewport.maximum_imaginary"))),
    )
    coordinate_scale = decode_f32(
        scene["function"]["q"]["coordinate_scale"], "q.coordinate_scale"
    )
    rho = radius / coordinate_scale
    if not 0.0 <= rho < 1.0:
        raise ContractError("the v1 q bound requires |z / coordinate_scale| < 1")
    envelope = decode_f32(
        scene["function"]["q"]["coefficient_envelope"],
        "q.coefficient_envelope",
    )
    # Since q has no constant term and sum |c_k| <= envelope,
    # sum |c_k| rho^k <= rho * sum |c_k| for rho < 1.
    return envelope * rho


def numeric_error_budget(
    scene: dict[str, Any], expected_log_magnitude: float
) -> NumericErrorBudget:
    """Derive the v1 binary32 acceptance bound for one oracle sample.

    The derivation is deliberately independent of observed backend errors.  It
    combines a gamma_n roundoff bound for the emitted arithmetic path with
    analytic Taylor remainders, binary32 coefficient quantization, and the
    error in the one-word ln(2)/pi reduction constants used by the baseline.
    """

    operations = _rounded_operation_count(scene)
    gamma = _gamma(operations)
    q_bound = _q_absolute_bound(scene)
    argument_bound = q_bound + gamma * (1.0 + q_bound)

    # exp uses a degree-six Taylor polynomial after ln(2) reduction.  Add the
    # gamma allowance to q_bound before using it as a conservative argument
    # radius.  The absolute remainder is converted to relative error with the
    # minimum possible magnitude.  Coefficient quantization is at most u per
    # exact coefficient.
    exp_remainder = (
        math.exp(argument_bound) * argument_bound**7 / math.factorial(7)
    )
    exp_coefficient_error = F32_UNIT_ROUNDOFF * sum(
        argument_bound**power / math.factorial(power) for power in range(7)
    )
    exp_relative_error = (
        exp_remainder + exp_coefficient_error
    ) / math.exp(-argument_bound)
    # |q| < pi/4 forces the scene's sin/cos quadrant to zero, so there is no
    # nonzero pi/2 subtraction.  The degree-nine/eight Taylor remainders and
    # quantized coefficients still contribute a normwise unit-circle error.
    if argument_bound >= math.pi / 4.0:
        raise ContractError("the v1 sin/cos error proof requires |q| < pi/4")
    sine_remainder = argument_bound**11 / math.factorial(11)
    cosine_remainder = argument_bound**10 / math.factorial(10)
    sine_coefficient_error = F32_UNIT_ROUNDOFF * sum(
        argument_bound**power / math.factorial(power) for power in range(1, 10, 2)
    )
    cosine_coefficient_error = F32_UNIT_ROUNDOFF * sum(
        argument_bound**power / math.factorial(power) for power in range(0, 9, 2)
    )
    sincos_error = math.hypot(
        sine_remainder + sine_coefficient_error,
        cosine_remainder + cosine_coefficient_error,
    )
    # The exp exponent k is at most one because |q| < ln(2).  Replacing true
    # ln(2) by its binary32 word therefore perturbs exp by expm1(|delta|).
    if argument_bound >= math.log(2.0):
        raise ContractError("the v1 exp reduction proof requires |q| < ln(2)")
    exp_reduction_error = math.expm1(abs(F32_LN2 - math.log(2.0)))

    # gamma_n controls all rounded arithmetic, including the stable scaled
    # division.  The (1 + |q|) factor pays for the one additive Horner path.
    # The remaining terms are relative errors in exp(q)'s complex value.
    relative_value_error = (
        gamma * (1.0 + q_bound)
        + exp_relative_error
        + sincos_error
        + exp_reduction_error
    )
    if relative_value_error >= 1.0:
        raise ContractError("derived relative error no longer proves a nonzero value")

    # atan reduces to |t| <= tan(pi/8), then uses the alternating degree-eleven
    # series.  Its next term is a rigorous truncation bound.  Add binary32
    # reciprocal-coefficient and worst-path pi-constant quantization errors.
    atan_radius = math.sqrt(2.0) - 1.0
    atan_remainder = atan_radius**13 / 13.0
    atan_coefficient_error = F32_UNIT_ROUNDOFF * sum(
        atan_radius ** (2 * index + 1) / (2 * index + 1)
        for index in range(6)
    )
    atan_constant_error = (
        abs(F32_PI_OVER_4 - math.pi / 4.0)
        + abs(F32_PI_OVER_2 - math.pi / 2.0)
        + abs(F32_PI - math.pi)
    )
    phase_bound = (
        math.asin(relative_value_error)
        + atan_remainder
        + atan_coefficient_error
        + atan_constant_error
    )

    # log(m) uses 2*(y+y^3/3+...+y^9/9), |y| <= 1/3.  Bound the omitted
    # geometric tail, quantized reciprocal coefficients, and the ln(2) word.
    log_radius = 1.0 / 3.0
    log_remainder = (
        2.0
        * log_radius**11
        / (11.0 * (1.0 - log_radius * log_radius))
    )
    log_coefficient_error = 2.0 * F32_UNIT_ROUNDOFF * sum(
        log_radius ** (2 * index + 1) / (2 * index + 1)
        for index in range(5)
    )
    # The logarithm sees |f|^2.  Two extra bins cover a boundary crossing from
    # the already bounded relative perturbation; this is derived per sample.
    binary_exponent_limit = math.ceil(
        abs(2.0 * expected_log_magnitude / math.log(2.0))
    ) + 2
    log_reduction_error = binary_exponent_limit * abs(F32_LN2 - math.log(2.0))
    log_bound = (
        -math.log1p(-relative_value_error)
        + 0.5 * (log_remainder + log_coefficient_error + log_reduction_error)
    )
    return NumericErrorBudget(
        rounded_operations=operations,
        gamma=gamma,
        q_absolute_bound=q_bound,
        transcendental_argument_bound=argument_bound,
        relative_value=relative_value_error,
        phase=phase_bound,
        log_magnitude=log_bound,
    )


def _factor_product(factors: Iterable[dict[str, Any]], z: complex, where: str) -> complex:
    result = 1 + 0j
    for index, factor in enumerate(factors):
        position = decode_complex(factor["position"], f"{where}[{index}].position")
        result *= (z - position) ** factor["multiplicity"]
    return result


def homogeneous_value(
    scene: dict[str, Any], state: dict[str, Any], z: complex
) -> tuple[complex, complex]:
    """Return [Q(z):N_t(z)] so the affine value is N_t/Q."""

    function = scene["function"]
    denominator = _factor_product(function["poles"], z, "function.poles")
    numerator = _factor_product(function["zeros"], z, "function.zeros")
    numerator *= decode_complex(function["gain"], "function.gain")
    numerator *= cmath.exp(q_value(scene, state, z))
    if denominator == 0j and numerator == 0j:
        raise ContractError("[0:0] is not a projective point; reduce common factors first")
    return denominator, numerator


def projective_classification(value: tuple[complex, complex]) -> str:
    denominator, numerator = value
    if denominator == 0j and numerator == 0j:
        raise ContractError("[0:0] is not a projective point")
    if denominator == 0j:
        return "infinity"
    if numerator == 0j:
        return "zero"
    return "finite-nonzero"


def rescale_projective(
    value: tuple[complex, complex], scale: complex
) -> tuple[complex, complex]:
    if scale == 0j:
        raise ContractError("projective representative scale must be nonzero")
    projective_classification(value)
    return scale * value[0], scale * value[1]


def projective_cross_product(
    left: tuple[complex, complex], right: tuple[complex, complex]
) -> complex:
    projective_classification(left)
    projective_classification(right)
    return left[0] * right[1] - left[1] * right[0]


def phase_log(value: tuple[complex, complex]) -> tuple[float, float]:
    denominator, numerator = value
    classification = projective_classification(value)
    if classification != "finite-nonzero":
        raise ContractError(f"phase/log field is undefined at an exact {classification}")
    phase = math.atan2(numerator.imag, numerator.real) - math.atan2(
        denominator.imag, denominator.real
    )
    phase = (phase + math.pi) % (2.0 * math.pi) - math.pi
    log_magnitude = math.log(abs(numerator)) - math.log(abs(denominator))
    return phase, log_magnitude


def _positive_fract(value: float) -> float:
    return value - math.floor(value)


def _srgb_component(linear_value: float) -> float:
    value = max(linear_value, 0.0)
    if value <= 0.0031308:
        return 12.92 * value
    return 1.055 * value ** (1.0 / 2.4) - 0.055


def _hcl_to_srgb(
    hue_degrees: float, chroma: float, lightness: float
) -> tuple[float, float, float]:
    """Mirror wegert_hcl_to_srgb from the digest-locked GLSL core."""

    hue = math.radians(hue_degrees)
    u_star = chroma * math.cos(hue)
    v_star = chroma * math.sin(hue)

    white_u_prime = 0.19783982482140777
    white_v_prime = 0.46833630293240974

    if lightness > 8.0:
        y = ((lightness + 16.0) / 116.0) ** 3.0
    else:
        y = lightness / 903.2962962962963

    u_prime = u_star / (13.0 * lightness) + white_u_prime
    v_prime = v_star / (13.0 * lightness) + white_v_prime

    x = (9.0 * y * u_prime) / (4.0 * v_prime)
    z = y * (12.0 - 3.0 * u_prime - 20.0 * v_prime) / (4.0 * v_prime)

    linear_r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    linear_g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    linear_b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    return tuple(
        min(max(_srgb_component(component), 0.0), 1.0)
        for component in (linear_r, linear_g, linear_b)
    )


def wegert_color_from_phase_log_modulus(
    phase: float, log_modulus: float
) -> tuple[float, float, float]:
    """Apply the digest-locked observational Wegert color mapping."""

    if not math.isfinite(phase) or not math.isfinite(log_modulus):
        raise ContractError("Wegert color inputs must be finite")
    hue_degrees = 360.0 * _positive_fract(phase / WEGERT_TAU)
    log_modulus_band = _positive_fract(log_modulus / WEGERT_LOG_10)
    lightness = (
        66.0
        + 4.0 * log_modulus_band
        + 3.0 * _positive_fract(hue_degrees / 100.0)
    )
    return _hcl_to_srgb(hue_degrees, 45.0, lightness)


def srgb8_channel(value: float) -> int:
    """Clamp sRGB to [0,1], then round 255*c to nearest, ties upward."""

    if not math.isfinite(value):
        raise ContractError("sRGB channel must be finite")
    clamped = min(max(value, 0.0), 1.0)
    return math.floor(PPM_MAX_VALUE * clamped + 0.5)


def validate_scene(scene: dict[str, Any], repository_root: Path | None = None) -> None:
    _closed_object(
        scene,
        {
            "schema",
            "scene_id",
            "scalar",
            "viewport",
            "function",
            "states",
            "projective_codomain",
            "representatives",
            "projective_probes",
            "render",
        },
        "scene",
    )
    if scene["schema"] != SCHEMA:
        raise ContractError(f"scene.schema must be {SCHEMA!r}")
    if scene["scene_id"] != "meromorphic-exp-cp1-f32":
        raise ContractError("unexpected scene_id")
    _validate_header_id(scene["scene_id"], 32, "scene.scene_id")

    scalar = _closed_object(
        scene["scalar"], {"type", "parameter_encoding", "rounding"}, "scalar"
    )
    if scalar != {
        "type": "Float32",
        "parameter_encoding": "ieee-754-binary32-hex",
        "rounding": "round-to-nearest-ties-to-even",
    }:
        raise ContractError("the reference scene has one closed Float32 scalar contract")

    viewport = _closed_object(
        scene["viewport"],
        {
            "width",
            "height",
            "row_order",
            "sample_location",
            "real_sample",
            "imaginary_sample",
            "minimum_real",
            "maximum_real",
            "minimum_imaginary",
            "maximum_imaginary",
        },
        "viewport",
    )
    if viewport["width"] != 96 or viewport["height"] != 64:
        raise ContractError("the v1 scene is exactly 96 by 64 samples")
    if (
        viewport["row_order"] != "top-to-bottom"
        or viewport["sample_location"] != "pixel-centers"
    ):
        raise ContractError("unexpected viewport traversal")
    if viewport["real_sample"] != "(2*x - 95) / 32" or viewport[
        "imaginary_sample"
    ] != "(63 - 2*y) / 32":
        raise ContractError("unexpected pixel-center formula")
    minimum_real = decode_f32(viewport["minimum_real"], "viewport.minimum_real")
    maximum_real = decode_f32(viewport["maximum_real"], "viewport.maximum_real")
    minimum_imaginary = decode_f32(
        viewport["minimum_imaginary"], "viewport.minimum_imaginary"
    )
    maximum_imaginary = decode_f32(
        viewport["maximum_imaginary"], "viewport.maximum_imaginary"
    )
    if (
        minimum_real,
        maximum_real,
        minimum_imaginary,
        maximum_imaginary,
    ) != (-3.0, 3.0, -2.0, 2.0):
        raise ContractError("the v1 viewport bounds are exactly [-3,3] by [-2,2]")

    function = _closed_object(
        scene["function"], {"model", "gain", "zeros", "poles", "q"}, "function"
    )
    if function["model"] != "f_t(z) = R(z) exp(q_t(z))":
        raise ContractError("unexpected function model")
    if decode_complex(function["gain"], "function.gain") == 0j:
        raise ContractError("gain must be nonzero")
    zeros = _validate_factor_list(function["zeros"], "function.zeros")
    poles = _validate_factor_list(function["poles"], "function.poles")
    common = _factor_positions(zeros, "function.zeros") & _factor_positions(
        poles, "function.poles"
    )
    if common:
        raise ContractError("zero/pole common factors must be reduced before this boundary")

    q = _closed_object(
        function["q"],
        {
            "coordinate",
            "coordinate_scale",
            "constant_term",
            "coefficient_envelope",
            "coefficient_order",
        },
        "function.q",
    )
    if q["coordinate"] != "u = z / 6" or decode_f32(
        q["coordinate_scale"], "function.q.coordinate_scale"
    ) != 6.0:
        raise ContractError("the v1 polynomial coordinate is u = z / 6")
    if q["constant_term"] != "omitted":
        raise ContractError("q must retain the q(0)=0 gauge")
    coefficient_envelope = decode_f32(
        q["coefficient_envelope"], "function.q.coefficient_envelope"
    )
    if coefficient_envelope != struct.unpack(">f", bytes.fromhex("3f3851ec"))[0]:
        raise ContractError("the v1 coefficient envelope is the Float32 value 0.72f")
    if q["coefficient_order"] != ["u", "u^2", "u^3", "u^4", "u^5"]:
        raise ContractError("unexpected q coefficient order")

    if not isinstance(scene["states"], list) or len(scene["states"]) != 2:
        raise ContractError("the v1 scene has exactly two mathematical states")
    state_ids: set[str] = set()
    state_times: set[int] = set()
    for index, raw in enumerate(scene["states"]):
        state = _closed_object(raw, {"id", "t", "q_coefficients"}, f"states[{index}]")
        state_id = _validate_header_id(state["id"], 24, f"states[{index}].id")
        if state_id in state_ids:
            raise ContractError(f"duplicate state id {state_id!r}")
        state_ids.add(state_id)
        time_word = state["t"]
        decode_f32(time_word, f"states[{index}].t")
        time_bits = int(time_word[2:], 16)
        if time_bits in state_times:
            raise ContractError("state times must be distinct")
        state_times.add(time_bits)
        coefficients = state["q_coefficients"]
        if not isinstance(coefficients, list) or len(coefficients) != 5:
            raise ContractError(f"states[{index}] must contain five q coefficients")
        budget = sum(
            abs(decode_complex(words, f"states[{index}].q_coefficients[{coefficient}]"))
            for coefficient, words in enumerate(coefficients)
        )
        if budget > coefficient_envelope:
            raise ContractError(
                f"states[{index}] exceeds the current 0.72 coefficient envelope"
            )

    if [state["id"] for state in scene["states"]] != ["still", "deformed"]:
        raise ContractError("v1 state order must be still, deformed")
    if [state["t"] for state in scene["states"]] != [
        "0x00000000",
        "0x3f800000",
    ]:
        raise ContractError("v1 state times must be exact Float32 values 0 and 1")
    if any(
        words != ["0x00000000", "0x00000000"]
        for words in scene_state(scene, "still")["q_coefficients"]
    ):
        raise ContractError("the still state must have an exact zero q polynomial")
    if all(
        decode_complex(words, f"deformed.q_coefficients[{index}]") == 0j
        for index, words in enumerate(
            scene_state(scene, "deformed")["q_coefficients"]
        )
    ):
        raise ContractError("the deformed state must have a nonzero q polynomial")

    projective = _closed_object(
        scene["projective_codomain"],
        {
            "space",
            "affine_embedding",
            "homogeneous_value",
            "numerator",
            "denominator",
            "affine_chart",
            "common_factor_policy",
            "all_zero_policy",
        },
        "projective_codomain",
    )
    required_projective = {
        "space": "CP1",
        "affine_embedding": "f -> [1:f]",
        "homogeneous_value": "[Q(z):N_t(z)]",
        "numerator": "N_t(z) = product_a (z-a)^multiplicity * exp(q_t(z))",
        "denominator": "Q(z) = product_b (z-b)^multiplicity",
        "affine_chart": "N_t(z) / Q(z) when Q(z) is nonzero",
        "common_factor_policy": "reject-unreduced-input",
        "all_zero_policy": "reject",
    }
    if projective != required_projective:
        raise ContractError("unexpected CP1 convention or safety policy")

    representatives = scene["representatives"]
    if not isinstance(representatives, list) or len(representatives) != 2:
        raise ContractError("v1 has identity and one nontrivial projective rescaling")
    representative_ids: set[str] = set()
    has_nontrivial_phase = False
    for index, raw in enumerate(representatives):
        representative = _closed_object(raw, {"id", "scale"}, f"representatives[{index}]")
        representative_id = _validate_header_id(
            representative["id"], 24, f"representatives[{index}].id"
        )
        if representative_id in representative_ids:
            raise ContractError(f"invalid representative id at index {index}")
        representative_ids.add(representative_id)
        scale = decode_complex(representative["scale"], f"representatives[{index}].scale")
        if scale == 0j:
            raise ContractError("projective representative scale must be nonzero")
        has_nontrivial_phase |= scale.imag != 0.0
    if not has_nontrivial_phase:
        raise ContractError("a rescaling with nontrivial complex phase is required")
    if [item["id"] for item in representatives] != ["identity", "times-two-i"]:
        raise ContractError("v1 representative order must be identity, times-two-i")
    if decode_complex(representatives[0]["scale"], "identity.scale") != 1 + 0j:
        raise ContractError("identity representative must use scale 1")
    if decode_complex(representatives[1]["scale"], "times-two-i.scale") != 0 + 2j:
        raise ContractError("times-two-i representative must use scale 2i")

    probes = scene["projective_probes"]
    if not isinstance(probes, list) or not probes:
        raise ContractError("projective probes are required")
    expected_classes = {"finite-nonzero", "zero", "infinity"}
    observed_classes: set[str] = set()
    probe_ids: set[str] = set()
    deformed = scene_state(scene, "deformed")
    for index, raw in enumerate(probes):
        probe = _closed_object(raw, {"id", "z", "expected"}, f"projective_probes[{index}]")
        probe_id = probe["id"]
        if not isinstance(probe_id, str) or not probe_id or probe_id in probe_ids:
            raise ContractError(f"invalid projective probe id at index {index}")
        probe_ids.add(probe_id)
        z = decode_complex(probe["z"], f"projective_probes[{index}].z")
        expected = probe["expected"]
        if expected not in expected_classes:
            raise ContractError(f"unknown projective probe class {expected!r}")
        actual = projective_classification(homogeneous_value(scene, deformed, z))
        if actual != expected:
            raise ContractError(f"probe {probe_id!r}: expected {expected}, got {actual}")
        observed_classes.add(actual)
    if observed_classes != expected_classes:
        raise ContractError("probes must cover finite, zero, and infinity CP1 values")

    factor_positions = _factor_positions(zeros, "function.zeros") | _factor_positions(
        poles, "function.poles"
    )
    for y in range(viewport["height"]):
        for x in range(viewport["width"]):
            if pixel_coordinate(scene, x, y) in factor_positions:
                raise ContractError("a pixel center coincides with an exact zero or pole")

    render = _closed_object(
        scene["render"],
        {
            "field_format",
            "phase",
            "log_magnitude",
            "interaction_overlays",
            "wegert_color_contract",
        },
        "render",
    )
    if (
        render["field_format"] != "phase_log_f32le"
        or render["interaction_overlays"] is not False
    ):
        raise ContractError("v1 emits an overlay-free phase/log Float32 field")
    if render["phase"] != "principal argument of N_t(z) / Q(z)" or render[
        "log_magnitude"
    ] != "log(abs(N_t(z))) - log(abs(Q(z)))":
        raise ContractError("unexpected phase/log field semantics")
    color = _closed_object(
        render["wegert_color_contract"],
        {"repository", "path", "sha256"},
        "wegert color contract",
    )
    if (
        color["repository"] != "isomorphismes/wegert"
        or color["path"] != "code/wegert_color.glsl"
    ):
        raise ContractError("unexpected Wegert color owner")
    if re.fullmatch(r"[0-9a-f]{64}", color["sha256"]) is None:
        raise ContractError("Wegert color digest must be lowercase SHA-256")
    if repository_root is not None:
        core = repository_root / WEGERT_CORE_RELATIVE
        actual_digest = hashlib.sha256(core.read_bytes()).hexdigest()
        if actual_digest != color["sha256"]:
            raise ContractError("local Wegert color core does not match the scene contract")


def load_scene(path: Path, repository_root: Path | None = None) -> dict[str, Any]:
    scene = json.loads(path.read_text())
    validate_scene(scene, repository_root)
    return scene


@dataclass(frozen=True)
class OutputEnvelope:
    width: int
    height: int
    state_index: int
    representative_index: int
    scene_sha256: bytes
    scene_id: str
    state_id: str
    representative_id: str
    samples: tuple[tuple[float, float], ...]


def _decode_header_text(raw: bytes, where: str) -> str:
    value, separator, padding = raw.partition(b"\0")
    if not separator or any(padding):
        raise ContractError(f"{where} must be NUL-terminated with zero padding")
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(f"{where} must be UTF-8") from error


def parse_output(data: bytes) -> OutputEnvelope:
    if len(data) < OUTPUT_HEADER_BYTES:
        raise ContractError("runner output is shorter than its fixed header")
    unpacked = OUTPUT_HEADER.unpack_from(data)
    (
        magic,
        version,
        header_bytes,
        width,
        height,
        state_index,
        representative_index,
        sample_bytes,
        flags,
        scene_sha256,
        scene_id_raw,
        state_id_raw,
        representative_id_raw,
        reserved,
    ) = unpacked
    if magic != OUTPUT_MAGIC:
        raise ContractError("runner output has the wrong magic")
    if version != OUTPUT_VERSION or header_bytes != OUTPUT_HEADER_BYTES:
        raise ContractError("runner output has an unsupported version or header size")
    if sample_bytes != OUTPUT_SAMPLE_BYTES:
        raise ContractError("runner output does not contain interleaved Float32 pairs")
    if flags != 0 or any(reserved):
        raise ContractError("runner output reserved fields must be zero")
    expected_bytes = OUTPUT_HEADER_BYTES + width * height * OUTPUT_SAMPLE_BYTES
    if len(data) != expected_bytes:
        raise ContractError(f"runner output has {len(data)} bytes; expected {expected_bytes}")
    samples = tuple(OUTPUT_SAMPLE.iter_unpack(data[OUTPUT_HEADER_BYTES:]))
    if any(not math.isfinite(item) for sample in samples for item in sample):
        raise ContractError("phase/log payload contains a non-finite value")
    if any(phase < -math.pi or phase > math.pi for phase, _ in samples):
        raise ContractError("phase/log payload contains a phase outside [-pi, pi]")
    return OutputEnvelope(
        width=width,
        height=height,
        state_index=state_index,
        representative_index=representative_index,
        scene_sha256=scene_sha256,
        scene_id=_decode_header_text(scene_id_raw, "scene_id"),
        state_id=_decode_header_text(state_id_raw, "state_id"),
        representative_id=_decode_header_text(representative_id_raw, "representative_id"),
        samples=samples,
    )


def verify_output(
    scene_path: Path,
    state_id: str,
    representative_id: str,
    output_path: Path,
    repository_root: Path | None = None,
) -> OutputEnvelope:
    scene_bytes = scene_path.read_bytes()
    scene = load_scene(scene_path, repository_root)
    state_index = next(
        (index for index, state in enumerate(scene["states"]) if state["id"] == state_id),
        None,
    )
    representative_index = next(
        (
            index
            for index, representative in enumerate(scene["representatives"])
            if representative["id"] == representative_id
        ),
        None,
    )
    if state_index is None:
        raise ContractError(f"unknown state id {state_id!r}")
    if representative_index is None:
        raise ContractError(f"unknown representative id {representative_id!r}")
    envelope = parse_output(output_path.read_bytes())
    expected = {
        "width": scene["viewport"]["width"],
        "height": scene["viewport"]["height"],
        "state_index": state_index,
        "representative_index": representative_index,
        "scene_sha256": hashlib.sha256(scene_bytes).digest(),
        "scene_id": scene["scene_id"],
        "state_id": state_id,
        "representative_id": representative_id,
    }
    for field, wanted in expected.items():
        actual = getattr(envelope, field)
        if actual != wanted:
            raise ContractError(f"output {field} is {actual!r}; expected {wanted!r}")

    # Framing and provenance are necessary but not sufficient: compare every
    # emitted sample with the application-owned Binary64 R(z)*exp(q_t(z))
    # oracle.  Phase is circular; log magnitude is ordinary absolute error.
    # Bounds come only from the declared binary32 execution path and analytic
    # approximation remainders, never from a previously observed run.
    state = scene_state(scene, state_id)
    for index, (actual_phase, actual_log) in enumerate(envelope.samples):
        x = index % envelope.width
        y = index // envelope.width
        expected_phase, expected_log = phase_log(
            homogeneous_value(scene, state, pixel_coordinate(scene, x, y))
        )
        budget = numeric_error_budget(scene, expected_log)
        phase_error = abs(math.remainder(actual_phase - expected_phase, 2.0 * math.pi))
        log_error = abs(actual_log - expected_log)
        if phase_error > budget.phase:
            raise ContractError(
                f"sample ({x},{y}) phase differs from the Binary64 R*exp(q) "
                f"oracle by {phase_error:.9g}; derived F32 bound is "
                f"{budget.phase:.9g}"
            )
        if log_error > budget.log_magnitude:
            raise ContractError(
                f"sample ({x},{y}) log magnitude differs from the Binary64 "
                f"R*exp(q) oracle by {log_error:.9g}; derived F32 bound is "
                f"{budget.log_magnitude:.9g}"
            )
    return envelope


def ppm_bytes(envelope: OutputEnvelope) -> bytes:
    """Encode an already verified phase/log envelope as deterministic P6."""

    header = f"P6\n{envelope.width} {envelope.height}\n{PPM_MAX_VALUE}\n".encode(
        "ascii"
    )
    pixels = bytearray()
    for phase, log_modulus in envelope.samples:
        color = wegert_color_from_phase_log_modulus(phase, log_modulus)
        pixels.extend(srgb8_channel(channel) for channel in color)
    return header + bytes(pixels)


def render_ppm(
    scene_path: Path,
    state_id: str,
    representative_id: str,
    field_path: Path,
    ppm_path: Path,
    repository_root: Path,
) -> bytes:
    """Verify a backend field, then write its observational Wegert P6 image."""

    envelope = verify_output(
        scene_path,
        state_id,
        representative_id,
        field_path,
        repository_root,
    )
    image = ppm_bytes(envelope)
    ppm_path.write_bytes(image)
    return image


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-scene")
    validate.add_argument("scene", type=Path)
    validate.add_argument("--repository-root", type=Path)
    verify = subparsers.add_parser("verify-output")
    verify.add_argument("scene", type=Path)
    verify.add_argument("state_id")
    verify.add_argument("representative_id")
    verify.add_argument("output", type=Path)
    verify.add_argument("--repository-root", type=Path)
    render = subparsers.add_parser("render-ppm")
    render.add_argument("scene", type=Path)
    render.add_argument("state_id")
    render.add_argument("representative_id")
    render.add_argument("field", type=Path)
    render.add_argument("ppm", type=Path)
    render.add_argument("--repository-root", type=Path, required=True)
    arguments = parser.parse_args()

    if arguments.command == "validate-scene":
        load_scene(arguments.scene, arguments.repository_root)
        print(f"valid scene: sha256={hashlib.sha256(arguments.scene.read_bytes()).hexdigest()}")
        return 0

    if arguments.command == "render-ppm":
        image = render_ppm(
            arguments.scene,
            arguments.state_id,
            arguments.representative_id,
            arguments.field,
            arguments.ppm,
            arguments.repository_root,
        )
        print(
            f"wrote deterministic P6 PPM: bytes={len(image)} "
            f"sha256={hashlib.sha256(image).hexdigest()}"
        )
        return 0

    envelope = verify_output(
        arguments.scene,
        arguments.state_id,
        arguments.representative_id,
        arguments.output,
        arguments.repository_root,
    )
    phases = [sample[0] for sample in envelope.samples]
    logs = [sample[1] for sample in envelope.samples]
    print(
        f"valid phase/log envelope: samples={len(envelope.samples)} "
        f"phase=[{min(phases):.9g},{max(phases):.9g}] "
        f"log_magnitude=[{min(logs):.9g},{max(logs):.9g}] "
        "oracle=Binary64-R*exp(q) tolerance=derived-F32"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
