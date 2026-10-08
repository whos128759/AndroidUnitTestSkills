from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import re
import shutil
from types import SimpleNamespace
import time
import unittest
from urllib.parse import unquote
from uuid import uuid4

from render_junit_report import annotate_cases, main, read_cases, render

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "TEST-Sample.xml"
CASE_METADATA = Path(__file__).resolve().parents[1] / "references" / "case-metadata.json"


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.base = Path.cwd().resolve()
        self.directory = self.base / (".report-test-" + uuid4().hex)
        self.directory.mkdir()

    def tearDown(self):
        if self.directory.resolve().parent != self.base:
            raise ValueError("Unexpected test cleanup path")
        shutil.rmtree(self.directory)

    def arguments(self, **overrides):
        values = {
            "xml-root": FIXTURE, "case-metadata": CASE_METADATA,
            "output": self.directory / "report.html", "scope": "app",
            "command": "gradlew testDebugUnitTest --offline", "environment": "synthetic fixture",
            "started-at": 0, "exit-code": 1, "task-outcome": "FAILED",
        }
        values.update(overrides)
        return [argument for key, value in values.items() for argument in ("--" + key, str(value))]

    def test_report_uses_actual_cases_and_escapes_xml_text(self):
        cases, files = read_cases(FIXTURE, 0)
        annotate_cases(cases, CASE_METADATA)
        args = SimpleNamespace(
            scope="app", command="gradlew testDebugUnitTest", environment="JDK 17",
            exit_code=1, task_outcome="FAILED", duration_seconds=3.5, run_log=None, coverage_report=None,
            case_metadata=CASE_METADATA,
            output=self.directory / "report.html", native_report=None,
        )
        html = render(cases, files, args)
        for expected in ("总数：3", "通过：1", "失败：1", "跳过：1", "命令失败", "3.50 秒"):
            self.assertIn(expected, html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("本次测试模块与被测类</dt><dd>:feature:login / LoginViewModel", html)
        self.assertIn("验证有效凭据返回成功状态", html)
        self.assertIn("登录错误处理", html)
        self.assertIn("测试任务状态</dt><dd>FAILED", html)

    def test_old_xml_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "No JUnit XML from this run"):
            read_cases(FIXTURE, time.time() + 1)

    def test_all_skipped_is_not_reported_as_passed(self):
        cases = [{"name": "com.example.login.LoginViewModelTest#loginPending", "status": "跳过", "seconds": "", "detail": "", "source": "TEST.xml"}]
        annotate_cases(cases, CASE_METADATA)
        args = SimpleNamespace(
            scope="app", command="gradlew testDebugUnitTest", environment="JDK 17",
            exit_code=0, task_outcome="EXECUTED", duration_seconds=None, run_log=None, coverage_report=None,
            case_metadata=CASE_METADATA,
            output=self.directory / "report.html", native_report=None,
        )
        html = render(cases, [FIXTURE], args)
        self.assertIn("结论：全部跳过", html)

    def test_missing_case_description_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Cases absent from approved metadata"):
            annotate_cases([{"name": "A#unknown"}], CASE_METADATA)

    def test_cached_task_cannot_generate_fresh_report(self):
        for outcome in ("UP-TO-DATE", "FROM-CACHE", "SKIPPED", "NO-SOURCE"):
            with self.subTest(outcome=outcome), redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
                main(self.arguments(**{"task-outcome": outcome, "exit-code": 0}))
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(list(self.directory.iterdir()), [])

    def test_inconsistent_suite_counts_cannot_produce_passing_report(self):
        xml = self.directory / "invalid.xml"
        xml.write_text('<testsuite tests="9" failures="4" errors="2" skipped="1"><testcase classname="A" name="ok"/></testsuite>', encoding="utf-8")
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit):
            main(self.arguments(**{"xml-root": xml, "exit-code": 0, "task-outcome": "EXECUTED"}))
        for field in ("tests=9", "failures=4", "errors=2", "skipped=1"):
            self.assertIn(field, error.getvalue())
        self.assertFalse((self.directory / "report.html").exists())
        self.assertFalse((self.directory / "report-artifacts").exists())

    def test_nested_counts_are_validated_without_double_counting(self):
        xml = self.directory / "nested.xml"
        xml.write_text('<testsuites tests="2" failures="1"><testsuite tests="2" failures="1"><testsuite tests="2"><testcase classname="A" name="ok"/><testcase classname="A" name="bad"><failure/></testcase></testsuite></testsuite></testsuites>', encoding="utf-8")
        cases, _ = read_cases(xml, 0)
        self.assertEqual([case["status"] for case in cases], ["通过", "失败"])
        xml.write_text(xml.read_text(encoding="utf-8").replace('failures="1"', 'failures="0"', 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JUnit count mismatch"):
            read_cases(xml, 0)

    def test_missing_path_and_wrong_task_directory_are_distinct(self):
        with self.assertRaisesRegex(ValueError, "path does not exist"):
            read_cases(self.directory / "missing.xml", 0)
        task = self.directory / "other-task"
        task.mkdir()
        shutil.copy2(FIXTURE, task / FIXTURE.name)
        with self.assertRaisesRegex(ValueError, "one test task's exact XML directory"):
            read_cases(self.directory, 0)

    def test_all_unknown_and_incomplete_descriptions_are_reported_together(self):
        metadata = self.directory / "metadata.json"
        metadata.write_text(json.dumps({"A#known": {}, "B#known": {"module": "app"}}), encoding="utf-8")
        names = ("A#known", "B#known", "Foreign#a", "Foreign#b")
        cases = [{"name": name, "source": "TEST.xml"} for name in names]
        with self.assertRaises(ValueError) as error:
            annotate_cases(cases, metadata)
        for name in names:
            self.assertIn(name, str(error.exception))
        self.assertIn("check task directory and scope", str(error.exception))
        self.assertIn("Missing module", str(error.exception))

    def test_report_archives_inputs_and_native_assets_without_overwriting(self):
        source = self.directory / "original.xml"
        shutil.copy2(FIXTURE, source)
        native = self.directory / "native"
        native.mkdir()
        (native / "index.html").write_text('<link rel="stylesheet" href="style.css">', encoding="utf-8")
        (native / "style.css").write_text("body {color:black}", encoding="utf-8")
        log = self.directory / "test.log"
        log.write_text("historical fixture log", encoding="utf-8")
        output = self.directory / "run 1" / "报告.html"
        arguments = self.arguments(**{"xml-root": source, "output": output, "native-report": native / "index.html", "run-log": log})
        with redirect_stdout(StringIO()):
            main(arguments)
        html = output.read_text(encoding="utf-8")
        archive = output.with_name("报告-artifacts")
        source.write_text("overwritten by a later run", encoding="utf-8")
        (native / "index.html").write_text("later native report", encoding="utf-8")
        log.write_text("later log", encoding="utf-8")
        self.assertEqual((archive / "xml" / source.name).read_bytes(), FIXTURE.read_bytes())
        self.assertEqual((archive / "run.log").read_text(encoding="utf-8"), "historical fixture log")
        self.assertIn("style.css", (archive / "native-report" / "index.html").read_text(encoding="utf-8"))
        self.assertTrue((archive / "native-report" / "style.css").is_file())
        self.assertIn("原生测试报告", html)
        for href in re.findall(r'href="([^"]+)"', html):
            self.assertFalse(Path(unquote(href)).is_absolute())
            self.assertTrue((output.parent / unquote(href)).is_file(), href)
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            main(self.arguments(**{"output": output}))
        self.assertEqual(output.read_text(encoding="utf-8"), html)

    def test_archive_inside_native_report_is_rejected(self):
        native = self.directory / "index.html"
        native.write_text("source", encoding="utf-8")
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit):
            main(self.arguments(**{"native-report": native}))
        self.assertIn("outside the source report directory", error.getvalue())
        self.assertFalse((self.directory / "report.html").exists())


if __name__ == "__main__":
    unittest.main()
