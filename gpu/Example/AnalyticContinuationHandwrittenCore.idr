module Example.AnalyticContinuationHandwrittenCore

import Shader.ComplexProjectiveFollower
import Shader.Source

%default total

-- This is a typed re-expression of the mathematical/color core of
-- android/app/src/main/assets/continuation.frag.in.  The interaction marks and
-- placement buttons remain handwritten for this first backend exercise.
--
-- The uniform shapes intentionally match the live fragment: 32 zero slots,
-- 32 pole slots, and five complex coefficients for q(z).

positive_fract : Double -> Double
positive_fract value = value - floorF value

srgb_component : Double -> Double
srgb_component linear_value =
  let value = maxF linear_value 0.0
   in if value <= 0.0031308
         then 12.92 * value
         else 1.055 * powF value (1.0 / 2.4) - 0.055

hcl_to_srgb : Double -> Double -> Double -> SVec 3
hcl_to_srgb hue_degrees chroma lightness =
  let hue = hue_degrees * 3.14159265358979323846 / 180.0
      u_star = chroma * cosF hue
      v_star = chroma * sinF hue
      white_u_prime = 0.19783982482140777
      white_v_prime = 0.46833630293240974
      cie_y =
        if lightness > 8.0
           then powF ((lightness + 16.0) / 116.0) 3.0
           else lightness / 903.2962962962963
      u_prime = u_star / (13.0 * lightness) + white_u_prime
      v_prime = v_star / (13.0 * lightness) + white_v_prime
      cie_x = (9.0 * cie_y * u_prime) / (4.0 * v_prime)
      cie_z = cie_y * (12.0 - 3.0 * u_prime - 20.0 * v_prime) / (4.0 * v_prime)
      linear_r = 3.2404542 * cie_x - 1.5371385 * cie_y - 0.4985314 * cie_z
      linear_g = -0.9692660 * cie_x + 1.8760108 * cie_y + 0.0415560 * cie_z
      linear_b = 0.0556434 * cie_x - 0.2040259 * cie_y + 1.0572252 * cie_z
      red = clampF (srgb_component linear_r) 0.0 1.0
      green = clampF (srgb_component linear_g) 0.0 1.0
      blue = clampF (srgb_component linear_b) 0.0 1.0
   in vec3 red green blue

wegert_color_from_phase_log_modulus : Double -> Double -> SVec 3
wegert_color_from_phase_log_modulus phase log_modulus =
  let hue_degrees = 360.0 * positive_fract (phase / 6.28318530717958647692)
      log_modulus_band = positive_fract (log_modulus / 2.30258509299404568402)
      lightness = 66.0
                + 4.0 * log_modulus_band
                + 3.0 * positive_fract (hue_degrees / 100.0)
   in hcl_to_srgb hue_degrees 45.0 lightness

factor_measure : SVec 2 -> SVec 2 -> SVec 2
factor_measure point factor =
  let delta = vsub point factor
      radius_squared = maxF (dot delta delta) 0.0000000000000001
      phase = atan2F (y delta) (x delta)
      log_modulus = 0.5 * logF radius_squared
   in vec2 phase log_modulus

active_factor_measure : SVec 2 -> Double -> SArray 32 (SVec 2) -> Double -> SVec 2
active_factor_measure point count factors index =
  if index < count
     then factor_measure point (array_at factors index)
     else vec2 0.0 0.0

factor_sum_32 : SVec 2 -> Double -> SArray 32 (SVec 2) -> SVec 2
factor_sum_32 point count factors =
  let sum_0 = active_factor_measure point count factors 0.0
      sum_1 = complex_add sum_0 (active_factor_measure point count factors 1.0)
      sum_2 = complex_add sum_1 (active_factor_measure point count factors 2.0)
      sum_3 = complex_add sum_2 (active_factor_measure point count factors 3.0)
      sum_4 = complex_add sum_3 (active_factor_measure point count factors 4.0)
      sum_5 = complex_add sum_4 (active_factor_measure point count factors 5.0)
      sum_6 = complex_add sum_5 (active_factor_measure point count factors 6.0)
      sum_7 = complex_add sum_6 (active_factor_measure point count factors 7.0)
      sum_8 = complex_add sum_7 (active_factor_measure point count factors 8.0)
      sum_9 = complex_add sum_8 (active_factor_measure point count factors 9.0)
      sum_10 = complex_add sum_9 (active_factor_measure point count factors 10.0)
      sum_11 = complex_add sum_10 (active_factor_measure point count factors 11.0)
      sum_12 = complex_add sum_11 (active_factor_measure point count factors 12.0)
      sum_13 = complex_add sum_12 (active_factor_measure point count factors 13.0)
      sum_14 = complex_add sum_13 (active_factor_measure point count factors 14.0)
      sum_15 = complex_add sum_14 (active_factor_measure point count factors 15.0)
      sum_16 = complex_add sum_15 (active_factor_measure point count factors 16.0)
      sum_17 = complex_add sum_16 (active_factor_measure point count factors 17.0)
      sum_18 = complex_add sum_17 (active_factor_measure point count factors 18.0)
      sum_19 = complex_add sum_18 (active_factor_measure point count factors 19.0)
      sum_20 = complex_add sum_19 (active_factor_measure point count factors 20.0)
      sum_21 = complex_add sum_20 (active_factor_measure point count factors 21.0)
      sum_22 = complex_add sum_21 (active_factor_measure point count factors 22.0)
      sum_23 = complex_add sum_22 (active_factor_measure point count factors 23.0)
      sum_24 = complex_add sum_23 (active_factor_measure point count factors 24.0)
      sum_25 = complex_add sum_24 (active_factor_measure point count factors 25.0)
      sum_26 = complex_add sum_25 (active_factor_measure point count factors 26.0)
      sum_27 = complex_add sum_26 (active_factor_measure point count factors 27.0)
      sum_28 = complex_add sum_27 (active_factor_measure point count factors 28.0)
      sum_29 = complex_add sum_28 (active_factor_measure point count factors 29.0)
      sum_30 = complex_add sum_29 (active_factor_measure point count factors 30.0)
      sum_31 = complex_add sum_30 (active_factor_measure point count factors 31.0)
   in sum_31

holomorphic_q : SVec 2 -> SArray 5 (SVec 2) -> SVec 2
holomorphic_q point coefficients =
  let u = scale (1.0 / 3.0) point
      power_1 = u
      term_1 = complex_multiply (array_at coefficients 0.0) power_1
      power_2 = complex_multiply power_1 u
      term_2 = complex_multiply (array_at coefficients 1.0) power_2
      power_3 = complex_multiply power_2 u
      term_3 = complex_multiply (array_at coefficients 2.0) power_3
      power_4 = complex_multiply power_3 u
      term_4 = complex_multiply (array_at coefficients 3.0) power_4
      power_5 = complex_multiply power_4 u
      term_5 = complex_multiply (array_at coefficients 4.0) power_5
   in complex_add term_1
        (complex_add term_2
          (complex_add term_3
            (complex_add term_4 term_5)))

%export "glsles:fragment|v_ndc=in,u_resolution=uniform,u_zero_count=uniform,u_pole_count=uniform,u_zero_positions=uniform,u_pole_positions=uniform,u_holomorphic_coefficients=uniform,u_zoom=uniform"
analytic_continuation_handwritten_core :
  SVec 2 -> SVec 2 -> Int -> Int ->
  SArray 32 (SVec 2) -> SArray 32 (SVec 2) ->
  SArray 5 (SVec 2) -> Double -> SVec 4
analytic_continuation_handwritten_core
  ndc resolution zero_count pole_count zero_positions pole_positions coefficients zoom =
  let shortest_side = minF (x resolution) (y resolution)
      pixel_radius = 0.42 * shortest_side * zoom
      point = vec2
        (x ndc * 0.5 * x resolution / pixel_radius)
        (y ndc * 0.5 * y resolution / pixel_radius)
      zero_measure = factor_sum_32 point (int_to_double zero_count) zero_positions
      pole_measure = factor_sum_32 point (int_to_double pole_count) pole_positions
      divisor_measure = complex_subtract zero_measure pole_measure
      q = holomorphic_q point coefficients
      phase = x divisor_measure + y q
      log_modulus = y divisor_measure + x q
      color = wegert_color_from_phase_log_modulus phase log_modulus
   in vec4 (x color) (y color) (z color) 1.0

main : IO ()
main = pure ()
