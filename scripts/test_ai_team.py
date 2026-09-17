from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("team_check", ROOT / "scripts/check-ai-team.py")
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class TeamDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "agents/team-register.json").read_text(encoding="utf-8"))

    def test_register_and_links_are_valid(self):
        self.assertEqual(checker.validate(ROOT, self.data), [])

    def test_sixteen_roles_include_seven_new(self):
        self.assertEqual(len(self.data["members"]), 16)
        self.assertEqual(sum(m["new"] for m in self.data["members"]), 7)

    def test_duplicate_role_is_rejected(self):
        self.data["members"].append(copy.deepcopy(self.data["members"][0]))
        self.assertTrue(any("Duplicate role ID" in e for e in checker.validate(ROOT, self.data)))

    def test_missing_definition_is_rejected(self):
        self.data["members"][-1]["definitionPath"] = "agents/nonexistent-role.md"
        self.assertTrue(any("Missing file" in e for e in checker.validate(ROOT, self.data)))

    def test_path_escape_is_rejected(self):
        self.data["members"][-1]["definitionPath"] = "../../not-allowed.md"
        self.assertTrue(any("escapes repository" in e for e in checker.validate(ROOT, self.data)))

    def test_external_actions_cannot_be_enabled(self):
        self.data["newRoleRuntime"]["externalActionsAllowed"] = True
        self.assertTrue(any("externalActionsAllowed" in e for e in checker.validate(ROOT, self.data)))

    def test_scheduling_cannot_be_silently_enabled(self):
        self.data["newRoleRuntime"]["scheduledTasksCreated"] = True
        self.assertTrue(any("scheduledTasksCreated" in e for e in checker.validate(ROOT, self.data)))

    def test_ai_cannot_be_final_approver(self):
        self.data["finalApprover"] = "coo"
        self.assertIn("finalApprover must be owner", checker.validate(ROOT, self.data))

    def test_private_destination_is_not_disclosed(self):
        self.data["privateOutputRoot"] = "private-location-placeholder"
        self.assertTrue(any("private workspace" in e for e in checker.validate(ROOT, self.data)))

    def test_invalid_payload_does_not_crash(self):
        self.assertEqual(checker.validate(ROOT, []), ["Register must be an object"])


if __name__ == "__main__":
    unittest.main()
