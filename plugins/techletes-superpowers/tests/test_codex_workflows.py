"""Offline regression checks for Codex role installation and file handoffs."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
ROLES = PLUGIN / "codex" / "agents"
SCRIPTS = PLUGIN / "skills" / "subagent-driven-development" / "scripts"
SPEC = importlib.util.spec_from_file_location("install_agents", PLUGIN / "codex" / "install-agents.py")
assert SPEC is not None and SPEC.loader is not None
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class RoleTests(unittest.TestCase):
    def test_explicit_routing_and_permission_defaults(self):
        expected = {
            "explorer": ("luna", "medium"),
            "worker-routine": ("luna", "medium"),
            "worker": ("luna", "high"),
            "worker-deep": ("luna", "xhigh"),
            "reviewer": ("terra", "high"),
            "planner": ("sol", "high"),
            "reviewer-critical": ("sol", "high"),
        }
        self.assertEqual(len(list(ROLES.glob("*.toml"))), len(expected))
        for role, (model, effort) in expected.items():
            with self.subTest(role=role):
                data = tomllib.loads((ROLES / f"techletes-{role}.toml").read_text())
                self.assertEqual(data["name"], f"techletes-{role}")
                self.assertEqual(data["model"], f"gpt-5.6-{model}")
                self.assertEqual(data["model_reasoning_effort"], effort)
                self.assertTrue(data["description"])
                self.assertTrue(data["developer_instructions"])
                self.assertNotIn("approval_policy", data)
                self.assertNotIn("mcp_servers", data)
                if role.startswith("worker"):
                    self.assertNotIn("sandbox_mode", data)
                else:
                    self.assertEqual(data["sandbox_mode"], "read-only")


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dest = self.root / "agents"

    def test_dry_run_does_not_create_destination(self):
        result = INSTALLER.install(ROLES, self.dest, dry_run=True)
        self.assertEqual(len(result), 7)
        self.assertFalse(self.dest.exists())

    def test_install_is_idempotent_and_preserves_other_configuration(self):
        config = self.root / "config.toml"
        config.write_text('model = "keep-my-model"\n')
        INSTALLER.install(ROLES, self.dest)
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.dest.iterdir()}
        result = INSTALLER.install(ROLES, self.dest)
        self.assertTrue(all(s.startswith("unchanged:") for s in result))
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.dest.iterdir()})
        self.assertEqual(config.read_text(), 'model = "keep-my-model"\n')

    def test_conflict_preflight_writes_nothing(self):
        self.dest.mkdir()
        conflict = self.dest / "techletes-worker.toml"
        conflict.write_text("customized")
        with self.assertRaisesRegex(ValueError, "Conflicting role"):
            INSTALLER.install(ROLES, self.dest)
        self.assertEqual(list(self.dest.iterdir()), [conflict])
        self.assertEqual(conflict.read_text(), "customized")

    def test_overwrite_preserves_original_backup(self):
        INSTALLER.install(ROLES, self.dest)
        target = self.dest / "techletes-worker.toml"
        target.write_text("customized")
        INSTALLER.install(ROLES, self.dest, overwrite=True)
        backups = list(self.dest.glob("techletes-worker.toml.*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "customized")
        self.assertEqual(target.read_bytes(), (ROLES / target.name).read_bytes())

    def test_invalid_bundle_is_rejected_before_writes(self):
        source = self.root / "source"
        shutil.copytree(ROLES, source)
        (source / "techletes-worker.toml").write_text("not valid toml")
        with self.assertRaises(ValueError):
            INSTALLER.install(source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_symlink_target_is_not_followed(self):
        self.dest.mkdir()
        outside = self.root / "outside"
        outside.write_text("preserve")
        (self.dest / "techletes-worker.toml").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "non-regular"):
            INSTALLER.install(ROLES, self.dest, overwrite=True)
        self.assertEqual(outside.read_text(), "preserve")

    def test_custom_codex_home(self):
        env = dict(os.environ, CODEX_HOME=str(self.root / "custom codex"))
        result = subprocess.run([sys.executable, str(PLUGIN / "codex" / "install-agents.py")],
                                env=env, capture_output=True, text=True, check=True)
        self.assertIn("installed:", result.stdout)
        self.assertEqual(len(list((self.root / "custom codex" / "agents").glob("*.toml"))), 7)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex handoff ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "Workflow Tests")
        self.commit("base", "base")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True,
                              text=True, check=True)

    def commit(self, name, content):
        (self.repo / f"{name}.txt").write_text(content)
        self.git("add", f"{name}.txt")
        self.git("commit", "-qm", name)

    def run_script(self, name, *args, check=True):
        return subprocess.run([str(SCRIPTS / name), *map(str, args)], cwd=self.repo,
                              capture_output=True, text=True, check=check)

    def test_workspace_is_ignored(self):
        result = self.run_script("sdd-workspace")
        path = Path(result.stdout.strip())
        (path / "progress.md").write_text("state")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_task_brief_is_path_only_and_handles_fences_and_phase_boundary(self):
        plan = self.repo / "plan with spaces.md"
        plan.write_text("# Plan\n### Task 1: first\nkeep\n````markdown\n```\n### Task 2: example only\n```\n````\n#### Detail\nkeep too\n## Phase 2\nexclude\n### Task 2: real\nother\n")
        result = self.run_script("task-brief", plan, "1")
        path = Path(result.stdout.strip())
        self.assertTrue(path.is_file())
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertIn("Task 2: example only", path.read_text())
        self.assertIn("keep too", path.read_text())
        self.assertNotIn("Phase 2", path.read_text())
        self.assertIn("wrote", result.stderr)
        second = self.run_script("task-brief", plan, "2")
        self.assertIn("Task 2: real", Path(second.stdout.strip()).read_text())
        self.assertNotIn("example only", Path(second.stdout.strip()).read_text())

    def test_missing_task_preserves_existing_output(self):
        plan = self.repo / "plan.md"
        plan.write_text("### Task 10: tenth\ntext\n")
        out = self.repo / "existing.md"
        out.write_text("preserve")
        result = self.run_script("task-brief", plan, "1", out, check=False)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertEqual(out.read_text(), "preserve")

    def test_invalid_task_and_plan_overwrite_are_rejected(self):
        plan = self.repo / "plan.md"
        plan.write_text("### Task 1: first\nkeep\n")
        for number in ("0", "-1", "1|.*", "../../escape"):
            result = self.run_script("task-brief", plan, number, check=False)
            self.assertEqual(result.returncode, 2)
        result = self.run_script("task-brief", plan, "1", plan, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("keep", plan.read_text())

    def test_review_package_contains_full_multi_commit_range(self):
        self.commit("first", "first addition")
        self.commit("second", "second addition")
        result = self.run_script("review-package", self.base, "HEAD")
        path = Path(result.stdout.strip())
        self.assertTrue(path.is_file())
        self.assertEqual(len(result.stdout.splitlines()), 1)
        package = path.read_text()
        self.assertIn("+first addition", package)
        self.assertIn("+second addition", package)
        self.assertIn("2 commit(s)", result.stderr)

    def test_review_package_rejects_non_commit_without_overwriting(self):
        out = self.repo / "review.diff"
        out.write_text("preserve")
        for ref in ("missing-revision", "HEAD^{tree}", "--all"):
            result = self.run_script("review-package", ref, "HEAD", out, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertEqual(out.read_text(), "preserve")


class WorkflowContractTests(unittest.TestCase):
    def test_routing_document_matches_native_role_settings(self):
        policy = (PLUGIN / "skills/subagent-driven-development/references/model-routing.md").read_text()
        for path in ROLES.glob("*.toml"):
            role = tomllib.loads(path.read_text())
            row = f"| `{role['name']}` | `{role['model']}` | `{role['model_reasoning_effort']}` |"
            self.assertIn(row, policy, path.name)

    def test_changed_workflow_entrypoints_and_local_links(self):
        import re
        names = ("subagent-driven-development", "writing-plans", "executing-plans",
                 "requesting-code-review", "dispatching-parallel-agents",
                 "using-superpowers", "finishing-a-development-branch")
        paths = [PLUGIN / "skills" / name / "SKILL.md" for name in names]
        for path in paths:
            text = path.read_text()
            self.assertRegex(text, rf"\A---\nname: {re.escape(path.parent.name)}\ndescription: [^\n]+\n---")
            self.assertLess(len(text.splitlines()), 500, str(path))
            self.assertNotIn("Every subagent MUST use", text)
        paths += [PLUGIN / "AGENTS.md", PLUGIN / "codex/README.md",
                  PLUGIN / "skills/subagent-driven-development/references/model-routing.md"]
        paths += list((PLUGIN / "agents").glob("*.agent.md"))
        paths += list((PLUGIN / "skills/subagent-driven-development").glob("*-prompt.md"))
        paths += [PLUGIN / "skills/requesting-code-review/code-reviewer.md",
                  PLUGIN / "skills/using-superpowers/references/codex-tools.md"]
        for path in paths:
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", path.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                self.assertTrue((path.parent / target.split("#", 1)[0]).exists(), f"{path}: {target}")


if __name__ == "__main__":
    unittest.main()
