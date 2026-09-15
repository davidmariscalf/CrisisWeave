from __future__ import annotations

import unittest

import production_check


class ProductionGateTests(unittest.TestCase):
    def test_component_lock_is_complete(self) -> None:
        self.assertEqual(production_check.check_component_lock(), 11)

    def test_event_schema_is_parseable(self) -> None:
        production_check.check_json_schema()

    def test_python_sources_compile(self) -> None:
        production_check.check_python_sources()

    def test_workflow_actions_are_immutable(self) -> None:
        self.assertGreater(production_check.check_workflow_pins(), 0)

    def test_demo_launchers_use_locked_runner(self) -> None:
        production_check.check_launchers()


if __name__ == "__main__":
    unittest.main()
