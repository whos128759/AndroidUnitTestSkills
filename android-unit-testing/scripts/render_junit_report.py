"""Render a standalone HTML report from JUnit XML written by one test run."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import shutil
from urllib.parse import quote
import xml.etree.ElementTree as ET


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def case_status(test):
    tags = {local_name(child.tag) for child in test}
    return "错误" if "error" in tags else "失败" if "failure" in tags else "跳过" if "skipped" in tags else "通过"


def validate_counts(root, path):
    differences = []
    for suite in root.iter():
        if local_name(suite.tag) not in {"testsuite", "testsuites"}:
            continue
        counts = Counter(case_status(test) for test in suite.iter() if local_name(test.tag) == "testcase")
        actual = {"tests": sum(counts.values()), "failures": counts["失败"], "errors": counts["错误"], "skipped": counts["跳过"]}
        for field, count in actual.items():
            value = suite.get(field)
            if value is None:
                continue
            try:
                declared = int(value)
            except ValueError:
                declared = -1
            if declared != count:
                differences.append(f"{suite.get('name', local_name(suite.tag))}: {field}={value}, testcase count={count}")
    if differences:
        raise ValueError(f"JUnit count mismatch in {path}:\n" + "\n".join(differences))


def read_cases(xml_root, started_at):
    source = Path(xml_root)
    if not source.exists():
        raise ValueError(f"JUnit XML path does not exist: {source}")
    if not source.is_file() and not source.is_dir():
        raise ValueError(f"JUnit XML path is not a file or directory: {source}")
    files = [source] if source.is_file() else sorted(source.glob("*.xml"))
    if not files:
        raise ValueError(f"No XML files in {source}; supply one test task's exact XML directory or file.")
    files = [path for path in files if path.stat().st_mtime >= started_at]
    if not files:
        raise ValueError("No JUnit XML from this run; HTML report not generated.")

    cases = []
    used_files = []
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            raise ValueError(f"Invalid JUnit XML: {path}: {exc}") from exc
        if local_name(root.tag) not in {"testsuite", "testsuites"}:
            continue
        validate_counts(root, path)
        used_files.append(path)
        for test in root.iter():
            if local_name(test.tag) != "testcase":
                continue
            problems = [child for child in test if local_name(child.tag) in {"failure", "error"}]
            skips = [child for child in test if local_name(child.tag) == "skipped"]
            detail = "\n\n".join(
                f"{local_name(item.tag)}: {item.get('message', '')}\n{''.join(item.itertext()).strip()}"
                for item in problems + skips
            )
            cases.append({
                "name": f"{test.get('classname') or root.get('name') or path.stem}#{test.get('name') or '(unnamed)'}",
                "status": case_status(test),
                "seconds": test.get("time", ""),
                "detail": detail,
                "source": str(path),
            })
    if not cases:
        raise ValueError("JUnit XML contains no test cases; HTML report not generated.")
    return cases, used_files


def annotate_cases(cases, metadata_path):
    try:
        metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid case metadata: {metadata_path}: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("Case metadata must be a JSON object keyed by TestClass#method.")
    fields = ("module", "target_class", "feature", "purpose")
    unplanned = []
    incomplete = []
    for case in cases:
        if case["name"] not in metadata:
            unplanned.append(f"{case['name']} ({case.get('source', 'source unknown')})")
            continue
        details = metadata.get(case["name"])
        if not isinstance(details, dict) or any(
            not isinstance(details.get(field), str) or not details[field].strip()
            for field in fields
        ):
            incomplete.append(case["name"])
    errors = []
    if unplanned:
        errors.append("Cases absent from approved metadata; check task directory and scope before adding descriptions:\n" + "\n".join(unplanned))
    if incomplete:
        errors.append("Missing module, target_class, feature, or purpose for:\n" + "\n".join(incomplete))
    if errors:
        raise ValueError("\n".join(errors))
    for case in cases:
        details = metadata[case["name"]]
        case.update({field: details[field].strip() for field in fields})
    return cases


def file_link(path, output):
    path = Path(path).resolve()
    try:
        relative = Path(os.path.relpath(path, Path(output).resolve().parent)).as_posix()
        url = quote(relative, safe="/")
    except ValueError:
        relative, url = str(path), path.as_uri()
    return f'<a href="{escape(url)}">{escape(relative)}</a>'


def archive_inputs(files, args):
    archive = args.output.with_name(args.output.stem + "-artifacts")
    if args.output.exists() or archive.exists():
        raise ValueError(f"Output or evidence archive already exists; choose a new report path: {args.output}")
    for report in (args.native_report, args.coverage_report):
        if report and archive.resolve().is_relative_to(report.resolve().parent):
            raise ValueError(f"Report output must be outside the source report directory: {report.parent}")
    archive.mkdir(parents=True, exist_ok=False)
    xml_dir = archive / "xml"
    xml_dir.mkdir()
    for path in files:
        shutil.copy2(path, xml_dir / path.name)
    shutil.copy2(args.case_metadata, archive / "case-metadata.json")
    args.case_metadata = archive / "case-metadata.json"
    if args.run_log:
        shutil.copy2(args.run_log, archive / "run.log")
        args.run_log = archive / "run.log"
    for field, directory in (("native_report", "native-report"), ("coverage_report", "coverage-report")):
        report = getattr(args, field)
        if report:
            shutil.copytree(report.parent, archive / directory)
            setattr(args, field, archive / directory / report.name)
    return xml_dir


def render(cases, files, args):
    counts = Counter(case["status"] for case in cases)
    overall = "命令失败" if args.exit_code else (
        "测试失败" if counts["失败"] or counts["错误"] else
        "全部跳过" if counts["跳过"] == len(cases) else "通过"
    )
    entries = []
    for case in cases:
        detail = (
            f"<details><summary>查看详情</summary><pre>{escape(case['detail'])}</pre></details>"
            if case["detail"] else ""
        )
        entries.append(
            f"<article class=\"case\" data-status=\"{escape(case['status'])}\">"
            f"<div class=\"case-head\"><h3>{escape(case['name'])}</h3><strong>{escape(case['status'])}</strong></div>"
            "<dl class=\"case-meta\">"
            f"<dt>测试目的</dt><dd>{escape(case['purpose'])}</dd>"
            f"<dt>针对功能</dt><dd>{escape(case['feature'])}</dd>"
            f"<dt>模块</dt><dd>{escape(case['module'])}</dd>"
            f"<dt>被测类</dt><dd>{escape(case['target_class'])}</dd>"
            f"<dt>耗时</dt><dd>{escape(case['seconds'] + ' 秒' if case['seconds'] else '未记录')}</dd>"
            f"<dt>JUnit XML</dt><dd>{file_link(case['source'], args.output)}</dd>"
            "</dl>"
            f"{detail}</article>"
        )
    duration = f"{args.duration_seconds:.2f} 秒" if args.duration_seconds is not None else "未记录"
    sources = "<br>".join(file_link(path, args.output) for path in files)
    module_classes = "<br>".join(
        escape(f"{module} / {target_class}")
        for module, target_class in sorted({(case["module"], case["target_class"]) for case in cases})
    )
    run_log = f"<dt>运行日志</dt><dd>{file_link(args.run_log, args.output)}</dd>" if args.run_log else ""
    native_report = f"<dt>原生测试报告</dt><dd>{file_link(args.native_report, args.output)}</dd>" if args.native_report else ""
    coverage = (
        file_link(args.coverage_report, args.output)
        if args.coverage_report else "未采集或未提供；不计入结论"
    )
    generated = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Android 单元测试报告</title>
<style>
body{{font:16px/1.6 system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#18212b}}
h1{{line-height:1.2}} .summary{{display:flex;flex-wrap:wrap;gap:.6rem}}
.summary span{{background:#eef3f8;padding:.45rem .7rem;border-radius:.4rem}}
code,pre{{white-space:pre-wrap;overflow-wrap:anywhere}} pre{{background:#f5f7fa;padding:.7rem}}
dt{{font-weight:700;margin-top:.7rem}} .case{{border:1px solid #cbd5df;border-left:5px solid #64748b;border-radius:.4rem;padding:1rem;margin:1rem 0}}
.case[data-status="通过"]{{border-left-color:#15803d}} .case[data-status="失败"],.case[data-status="错误"]{{border-left-color:#b42318}}
.case-head{{display:flex;justify-content:space-between;gap:1rem;align-items:start}} .case-head h3{{margin:0;overflow-wrap:anywhere}}
.case-meta{{display:grid;grid-template-columns:6rem 1fr;gap:.25rem .7rem;margin:.5rem 0}}
.case-meta dt{{margin:0}} .case-meta dd{{margin:0;min-width:0;overflow-wrap:anywhere}}
@media(max-width:600px){{.case-meta{{grid-template-columns:1fr}}.case-meta dt{{margin-top:.45rem}}}}
</style>
</head>
<body>
<h1>Android 单元测试报告</h1>
<div class="summary">
<span>结论：{escape(overall)}</span><span>总数：{len(cases)}</span>
<span>通过：{counts['通过']}</span><span>失败：{counts['失败']}</span>
<span>错误：{counts['错误']}</span><span>跳过：{counts['跳过']}</span>
<span>命令耗时：{escape(duration)}</span>
</div>
<dl>
<dt>测试范围</dt><dd>{escape(args.scope)}</dd>
<dt>本次测试模块与被测类</dt><dd>{module_classes}</dd>
<dt>执行命令</dt><dd><code>{escape(args.command)}</code></dd>
<dt>测试任务状态</dt><dd>{escape(args.task_outcome)}</dd>
<dt>命令退出码</dt><dd>{args.exit_code}</dd>
<dt>环境</dt><dd>{escape(args.environment)}</dd>
<dt>覆盖率报告</dt><dd>{coverage}</dd>
{run_log}
{native_report}
<dt>生成时间</dt><dd>{generated}</dd>
<dt>原始 JUnit XML</dt><dd>{sources}</dd>
<dt>用例说明</dt><dd>{file_link(args.case_metadata, args.output)}</dd>
</dl>
<h2>用例结果</h2>
{''.join(entries)}
</body></html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-root", required=True, type=Path, help="JUnit XML file or exact directory for one approved test task; not recursive")
    parser.add_argument("--case-metadata", required=True, type=Path, help="JSON mapping each TestClass#method to module, target_class, feature, and purpose")
    parser.add_argument("--output", required=True, type=Path, help="HTML report path")
    parser.add_argument("--scope", required=True, help="Approved module or test scope")
    parser.add_argument("--command", required=True, help="Exact test command executed")
    parser.add_argument("--environment", required=True, help="Observed OS/JDK/Gradle/Android environment")
    parser.add_argument("--started-at", required=True, type=float, help="Unix timestamp captured before test command")
    parser.add_argument("--exit-code", required=True, type=int, help="Actual test command exit code")
    parser.add_argument("--task-outcome", required=True, choices=("EXECUTED", "FAILED", "UP-TO-DATE", "FROM-CACHE", "SKIPPED", "NO-SOURCE"), help="Observed outcome of the scoped Gradle test task")
    parser.add_argument("--duration-seconds", type=float, help="Measured wall-clock duration of test command")
    parser.add_argument("--run-log", type=Path, help="Existing log from the test command")
    parser.add_argument("--coverage-report", type=Path, help="Existing coverage report, if collected")
    parser.add_argument("--native-report", type=Path, help="Existing native report index.html; its directory is archived with assets")
    args = parser.parse_args(argv)
    if args.task_outcome not in {"EXECUTED", "FAILED"}:
        parser.exit(1, f"Test task {args.task_outcome}; no tests executed in this run. HTML report not generated.\n")
    for path in (args.run_log, args.coverage_report, args.native_report):
        if path is not None and not path.is_file():
            parser.exit(1, f"Referenced report file does not exist: {path}\n")
    try:
        cases, files = read_cases(args.xml_root, args.started_at)
        annotate_cases(cases, args.case_metadata)
        xml_dir = archive_inputs(files, args)
        cases, files = read_cases(xml_dir, args.started_at)
        annotate_cases(cases, args.case_metadata)
        with args.output.open("x", encoding="utf-8") as output:
            output.write(render(cases, files, args))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    print(args.output)


if __name__ == "__main__":
    main()
