#!/usr/bin/env python3
"""Convert per-case cov-format-errors --json-output-v10 files to SARIF 2.1.0."""

import argparse
import json
from pathlib import Path


def convert(document):
    if document.get("error"):
        raise ValueError(f"Coverity reported an error: {document['error']}")
    issues = document.get("issues")
    if not isinstance(issues, list):
        raise ValueError("Coverity JSON must contain an issues array")

    results = []
    rules = set()
    for issue in issues:
        if issue.get("localStatus") == "missing":
            continue
        rule = issue.get("checkerName")
        path = issue.get("mainEventFilePathname") or issue.get("strippedMainEventFilePathname")
        line = issue.get("mainEventLineNumber")
        if not rule or not path or not isinstance(line, int) or line < 1:
            raise ValueError("Coverity issue lacks a checker, source path, or valid line")
        rules.add(rule)
        uri = Path(path).as_uri() if Path(path).is_absolute() else path.replace("\\", "/")
        main_event = next((event for event in issue.get("events", []) if event.get("main")), {})
        results.append({
            "ruleId": rule,
            "message": {"text": main_event.get("eventDescription") or rule},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": uri},
                "region": {"startLine": line},
            }}],
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "Coverity Analysis",
                                        "rules": [{"id": rule} for rule in sorted(rules)]}},
                  "results": results}],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    converted = 0
    missing = []
    for line in args.manifest.open():
        case = json.loads(line)
        source = args.input_dir / f"{case['id']}.json"
        if not source.exists():
            missing.append(case["id"])
            continue
        sarif = convert(json.loads(source.read_text()))
        (args.output_dir / f"{case['id']}.sarif").write_text(json.dumps(sarif, indent=2))
        converted += 1
    print(f"Converted {converted} cases; missing Coverity JSON: {len(missing)}")


if __name__ == "__main__":
    main()
