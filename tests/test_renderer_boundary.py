from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RendererBoundaryTests(unittest.TestCase):
    def test_package_has_no_desktop_animation_dependency(self) -> None:
        project = (ROOT / "pyproject.toml").read_text().lower()
        self.assertNotIn("manimgl", project)
        self.assertNotIn("manimlib", project)

    def test_active_workflows_do_not_invoke_retired_renderer(self) -> None:
        workflows = "\n".join(
            path.read_text()
            for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        ).lower()
        self.assertNotIn("manimgl", workflows)
        self.assertNotIn("src/analytic_continuation/scene.py", workflows)
        self.assertNotIn("prepare_android_movies", workflows)

    def test_android_launches_only_the_native_explorer(self) -> None:
        manifest = (
            ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
        ).read_text()
        self.assertIn("ExplorerActivity", manifest)
        self.assertNotIn("MainActivity", manifest)

    def test_flow_is_analytic_and_has_no_reduction_path(self) -> None:
        shader = (
            ROOT / "android" / "app" / "src" / "main" / "assets" /
            "continuation.frag.in"
        ).read_text()
        native_build = (
            ROOT / "android" / "app" / "src" / "main" / "cpp" / "CMakeLists.txt"
        ).read_text()
        self.assertIn("flowing_descriptor", shader)
        self.assertIn("flow_log_multiplier.x", shader)
        self.assertIn("flow_log_multiplier.y", shader)
        self.assertNotIn("dFdx", shader)
        self.assertNotIn("dFdy", shader)
        self.assertNotIn("holomorphic_walk.c", native_build)


if __name__ == "__main__":
    unittest.main()
