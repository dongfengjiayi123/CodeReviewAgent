import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import review
from hello_agents import ToolRegistry
from hello_agents.tools.response import ToolStatus
from hello_agents.core.llm_response import LLMToolResponse, ToolCall


class ReviewTests(unittest.TestCase):
    def test_real_agent_loop_executes_tools_with_offline_model(self):
        test_case = self

        class OfflineModel:
            model = "offline-test"

            def invoke_with_tools(self, messages, **kwargs):
                results = [m for m in messages if m["role"] == "tool"]
                if not results:
                    return LLMToolResponse(None, [
                        ToolCall("analysis", "code_analysis", json.dumps({"code": "value = 1\n"})),
                        ToolCall("style", "style_check", json.dumps({"code": "value = 1\n"})),
                    ], self.model)
                test_case.assertEqual(len(results), 2)
                for result in results:
                    test_case.assertEqual(json.loads(result["content"])["status"], "success")
                return LLMToolResponse("offline review completed", [], self.model)

        with patch("review.HelloAgentsLLM", return_value=OfflineModel()):
            agent = review.create_agent()
        self.assertEqual(agent.run("review value = 1"), "offline review completed")
        self.assertEqual(agent.last_run.status, "completed")
        self.assertEqual(agent.last_run.tool_calls, 2)

    def test_registry_executes_both_tools(self):
        registry = ToolRegistry()
        registry.register_tool(review.CodeAnalysisTool())
        registry.register_tool(review.StyleCheckTool())
        code = "class A:\n    async def run(self):\n        pass  \n"
        result = registry.execute_tool("code_analysis", {"code": code})
        self.assertEqual(result.status, ToolStatus.SUCCESS)
        self.assertEqual(result.data["函数数量"], 1)
        self.assertEqual(result.data["类数量"], 1)
        self.assertIn("time_ms", result.stats)
        style = registry.execute_tool("style_check", {"code": code})
        self.assertEqual(style.status, ToolStatus.SUCCESS)
        self.assertEqual(style.data["issue_count"], 1)

    def test_registry_rejects_invalid_code(self):
        registry = ToolRegistry()
        registry.register_tool(review.CodeAnalysisTool())
        for code in ["def broken(:", "", 123]:
            with self.subTest(code=code):
                result = registry.execute_tool("code_analysis", {"code": code})
                self.assertEqual(result.status, ToolStatus.ERROR)

    def test_static_cli_needs_no_credentials(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            source = Path(folder) / "source.py"
            output = Path(folder) / "nested/report.md"
            source.write_text("value = 1\n", encoding="utf-8")
            with patch("review.create_agent") as create:
                review.main([str(source), "--static-only", "--output", str(output)])
                create.assert_not_called()
            self.assertIn("未调用大模型", output.read_text(encoding="utf-8"))

    def test_cli_protects_source_and_previous_report(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.py"
            output = Path(folder) / "report.md"
            source.write_text("def broken(:", encoding="utf-8")
            output.write_text("previous", encoding="utf-8")
            for target in [source, output]:
                with self.subTest(target=target), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as exc:
                        review.main([str(source), "--static-only", "--output", str(target)])
                    self.assertEqual(exc.exception.code, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous")
            self.assertEqual(source.read_text(encoding="utf-8"), "def broken(:")

    def test_ai_cli_saves_completed_response_and_closes_client(self):
        agent = Mock()
        agent.run.return_value = "AI findings"
        agent.last_run = SimpleNamespace(status="completed", model_calls=1, tool_calls=2)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.py"
            output = Path(folder) / "report.md"
            source.write_text("value = 1\n", encoding="utf-8")
            with patch("review.load_settings"), patch.dict(os.environ, {"LLM_MODEL_ID": "test"}), patch("review.create_agent", return_value=agent):
                review.main([str(source), "--output", str(output)])
            self.assertIn("AI findings", output.read_text(encoding="utf-8"))
            self.assertIn("代码结构分析", output.read_text(encoding="utf-8"))
            agent.llm.close.assert_called_once()

    def test_ai_failure_preserves_report_and_redacts_key(self):
        agent = Mock()
        secret = "test-private-key-123"
        agent.run.side_effect = RuntimeError("request failed " + secret)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.py"
            output = Path(folder) / "report.md"
            source.write_text("value = 1\n", encoding="utf-8")
            output.write_text("previous", encoding="utf-8")
            error = io.StringIO()
            with patch("review.load_settings"), patch.dict(os.environ, {"LLM_MODEL_ID": "test", "LLM_API_KEY": secret}), patch("review.create_agent", return_value=agent), contextlib.redirect_stderr(error):
                with self.assertRaises(SystemExit):
                    review.main([str(source), "--output", str(output)])
            self.assertNotIn(secret, error.getvalue())
            self.assertEqual(output.read_text(encoding="utf-8"), "previous")
            agent.llm.close.assert_called_once()

    def test_explicit_env_file_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"LLM_MODEL_ID": "external"}, clear=True):
            config = Path(folder) / "config.env"
            config.write_text("LLM_MODEL_ID=file\nLLM_API_KEY=test\nLLM_BASE_URL=https://example.invalid\n", encoding="utf-8")
            review.load_settings(config)
            self.assertEqual(os.environ["LLM_MODEL_ID"], "external")
            self.assertEqual(os.environ["LLM_API_KEY"], "test")


if __name__ == "__main__":
    unittest.main()
