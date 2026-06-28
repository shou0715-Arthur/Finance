from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import unittest

from workflow.execution_log import ExecutionLog, load_execution_log
from workflow.pipeline import Pipeline, WorkflowContext, ensure_context
from workflow.registry import clear_workflows, get_workflow, list_workflows, register_workflow
from workflow.scheduler import ScheduledWorkflow
from workflow.steps import BranchStep, FunctionStep, RequiredKeysStep


TEST_TMP_ROOT = Path("tmp_tests")


class WorkflowEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_TMP_ROOT.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if TEST_TMP_ROOT.exists():
            shutil.rmtree(TEST_TMP_ROOT)

    def test_workflow_context_with_value_and_metadata_are_immutable(self) -> None:
        context = WorkflowContext().with_value("ticker", "2330").with_metadata("source", "test")
        self.assertEqual(context.data["ticker"], "2330")
        self.assertEqual(context.metadata["source"], "test")
        self.assertNotIn("ticker", WorkflowContext().data)

    def test_step_execution_duration_is_non_negative(self) -> None:
        result = Pipeline([FunctionStep("noop", lambda context: context)]).run()
        self.assertGreaterEqual(result.executions[0].duration_seconds, 0)

    def test_pipeline_result_ok_and_errors(self) -> None:
        def fail(_: WorkflowContext) -> WorkflowContext:
            raise ValueError("boom")

        result = Pipeline([FunctionStep("fail", fail)]).run()
        self.assertFalse(result.ok)
        self.assertTrue(result.errors)

    def test_ensure_context_accepts_none_mapping_and_context(self) -> None:
        self.assertEqual(ensure_context().data, {})
        self.assertEqual(ensure_context({"a": 1}).data["a"], 1)
        existing = WorkflowContext({"b": 2})
        self.assertIs(ensure_context(existing), existing)

    def test_pipeline_runs_steps_in_order(self) -> None:
        pipeline = Pipeline(
            [
                FunctionStep("one", lambda context: context.with_value("x", 1)),
                FunctionStep("two", lambda context: context.with_value("y", context.data["x"] + 1)),
            ]
        )
        result = pipeline.run()
        self.assertTrue(result.ok)
        self.assertEqual(result.context.data["y"], 2)

    def test_function_step_runs_callable(self) -> None:
        step = FunctionStep("add", lambda context: context.with_value("ok", True))
        self.assertTrue(step.run(WorkflowContext()).data["ok"])

    def test_required_keys_step_passes_and_fails(self) -> None:
        step = RequiredKeysStep("required", ("ticker",))
        self.assertEqual(step.run(WorkflowContext({"ticker": "2330"})).data["ticker"], "2330")
        with self.assertRaises(KeyError):
            step.run(WorkflowContext())

    def test_branch_step_selects_true_and_false_paths(self) -> None:
        true_step = FunctionStep("true", lambda context: context.with_value("branch", "true"))
        false_step = FunctionStep("false", lambda context: context.with_value("branch", "false"))
        branch = BranchStep("branch", lambda context: bool(context.data.get("flag")), [true_step], [false_step])
        self.assertEqual(branch.run(WorkflowContext({"flag": True})).data["branch"], "true")
        self.assertEqual(branch.run(WorkflowContext({"flag": False})).data["branch"], "false")

    def test_registry_register_get_list_clear(self) -> None:
        clear_workflows()
        register_workflow("demo", lambda: Pipeline([]))
        self.assertEqual(list_workflows(), ["demo"])
        self.assertIsInstance(get_workflow("demo"), Pipeline)
        with self.assertRaises(KeyError):
            register_workflow("demo", lambda: Pipeline([]))
        clear_workflows()
        self.assertEqual(list_workflows(), [])

    def test_execution_log_append_json_save_and_load(self) -> None:
        result = Pipeline([FunctionStep("noop", lambda context: context)]).run()
        log = ExecutionLog()
        record = log.append_result("demo", result)
        self.assertTrue(record.ok)
        self.assertEqual(log.to_jsonable()[0]["workflow_name"], "demo")
        path = TEST_TMP_ROOT / "log.json"
        log.save_json(path)
        loaded = load_execution_log(path)
        self.assertEqual(loaded.records[0].workflow_name, "demo")

    def test_load_execution_log_missing_file_returns_empty_log(self) -> None:
        log = load_execution_log(TEST_TMP_ROOT / "missing.json")
        self.assertEqual(log.records, [])

    def test_scheduled_workflow_due_and_mark_run(self) -> None:
        now = datetime(2026, 6, 24, tzinfo=timezone.utc)
        scheduled = ScheduledWorkflow("demo", interval_seconds=60)
        self.assertTrue(scheduled.is_due(now))
        scheduled.mark_run(now)
        self.assertFalse(scheduled.is_due(now + timedelta(seconds=30)))
        self.assertTrue(scheduled.is_due(now + timedelta(seconds=61)))


if __name__ == "__main__":
    unittest.main()
