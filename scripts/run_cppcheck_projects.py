#!/usr/bin/env python3
"""Run Cppcheck on full project snapshots or target files; save per-case SARIF."""

import argparse
import json
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def to_sarif(xml_text, source_root):
    root = ET.fromstring(xml_text)
    results = []
    rules = {}
    for error in root.findall(".//error"):
        rule = error.get("id", "cppcheck")
        rules[rule] = {"id": rule, "name": rule}
        locations = []
        for location in error.findall("location"):
            file_name = location.get("file")
            if not file_name:
                continue
            file_path = Path(file_name)
            try:
                file_name = str(file_path.resolve().relative_to(source_root.resolve()))
            except ValueError:
                file_name = file_path.as_posix()
            physical = {"artifactLocation": {"uri": file_name}}
            if location.get("line"):
                physical["region"] = {"startLine": int(location.get("line"))}
            locations.append({"physicalLocation": physical})
        if locations:
            results.append({
                "ruleId": rule,
                "level": "error" if error.get("severity") == "error" else "warning",
                "message": {"text": error.get("msg", "")},
                "locations": locations,
            })
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{"tool": {"driver": {"name": "Cppcheck", "rules": list(rules.values())}}, "results": results}],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("labels/ready-projects.jsonl"))
    parser.add_argument("--results", type=Path, default=Path("results/docker-cppcheck-projects"))
    parser.add_argument("--scope", choices=("full", "target-files"), default="full")
    parser.add_argument("--case-id", action="append", help="Run only this case; repeat for more cases")
    parser.add_argument("--timeout", type=int, default=1200,
                        help="Seconds per case; 0 disables the time limit")
    parser.add_argument("--max-configs", type=int, help="Limit Cppcheck configurations per file")
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    cases = [json.loads(line) for line in args.manifest.open()]
    if args.case_id:
        cases = [case for case in cases if case["id"] in args.case_id]
    failures = []
    timings = []
    for number, case in enumerate(cases, 1):
        started = time.perf_counter()
        source_root = Path(case["source_dir"])
        output = args.results / f"{case['id']}.sarif"
        output.unlink(missing_ok=True)
        paths = ([str(source_root)] if args.scope == "full" else
                 [str(source_root / case["source_file"])] if case.get("source_file") else
                 [str(source_root / label["path"]) for label in case["labels"]])
        cmd = ["cppcheck", "--xml", "--xml-version=2", "--enable=warning",
               "--suppress=missingIncludeSystem", "--quiet"]
        if args.max_configs:
            cmd.append(f"--max-configs={args.max_configs}")
        cmd.extend(paths)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=args.timeout or None)
            if result.returncode != 0:
                failures.append({"id": case["id"], "returncode": result.returncode, "stderr": result.stderr[-2000:]})
            else:
                sarif = to_sarif(result.stderr, source_root)
                output.write_text(json.dumps(sarif, indent=2))
                if len(cases) <= 10:
                    print(f"{case['id']}: {len(sarif['runs'][0]['results'])} findings")
        except (subprocess.TimeoutExpired, ET.ParseError) as exc:
            failures.append({"id": case["id"], "error": str(exc)})
        timings.append({"id": case["id"], "seconds": round(time.perf_counter() - started, 3),
                        "completed": output.exists()})
        if len(cases) > 10 and (number % 50 == 0 or number == len(cases)):
            print(f"{number}/{len(cases)} files analyzed; failures: {len(failures)}", flush=True)
    (args.results / "failures.json").write_text(json.dumps(failures, indent=2))
    (args.results / "timings.json").write_text(json.dumps({
        "total_seconds": round(sum(item["seconds"] for item in timings), 3),
        "cases": timings,
    }, indent=2))
    print(f"Failed cases: {len(failures)}")


if __name__ == "__main__":
    main()
