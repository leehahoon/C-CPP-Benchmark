#!/usr/bin/env python3
"""Score one SARIF file per case against the prepared static-analysis labels."""

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import unquote, urlparse


def normalized_path(uri):
    parsed = urlparse(uri or "")
    path = unquote(parsed.path if parsed.scheme else uri or "")
    return path.replace("\\", "/").removeprefix("./")


def same_file(found, expected):
    found = normalized_path(found)
    expected = expected.replace("\\", "/").removeprefix("./")
    return found == expected or found.endswith("/" + expected)


def findings(path, excluded_rules=()):
    document = json.loads(path.read_text())
    if document.get("version") != "2.1.0" or not isinstance(document.get("runs"), list):
        raise ValueError(f"Not SARIF 2.1.0: {path}")
    found = []
    for run_index, run in enumerate(document["runs"]):
        artifacts = run.get("artifacts", [])
        for result_index, result in enumerate(run.get("results", [])):
            if result.get("ruleId") in excluded_rules:
                continue
            for location in result.get("locations", []):
                physical = location.get("physicalLocation") or {}
                artifact = physical.get("artifactLocation") or {}
                uri = artifact.get("uri")
                if uri is None and isinstance(artifact.get("index"), int):
                    index = artifact["index"]
                    if 0 <= index < len(artifacts):
                        uri = (artifacts[index].get("location") or {}).get("uri")
                if not uri:
                    continue
                region = physical.get("region") or {}
                found.append({"path": normalized_path(uri), "line": region.get("startLine"),
                              "rule": result.get("ruleId"), "result_id": f"{run_index}:{result_index}"})
    return found


def score_case(case, alerts):
    labels = case.get("labels") or []
    target_paths = [label["path"] for label in labels]
    if case.get("ground_truth") == "negative" and case.get("source_file"):
        target_paths = [case["source_file"]]
    target_alerts = [a for a in alerts if any(same_file(a["path"], path) for path in target_paths)]
    exact = any(
        same_file(a["path"], label["path"])
        and isinstance(a["line"], int)
        and any(span["start"] <= a["line"] <= span["end"] for span in label.get("line_candidates", []))
        for a in alerts for label in labels
    )
    return {
        "id": case["id"], "dataset": case["dataset"],
        "source_scope": case.get("source_scope"),
        "ground_truth": case.get("ground_truth", "positive"),
        "alerts": len({a["result_id"] for a in alerts}),
        "target_file_alerts": len({a["result_id"] for a in target_alerts}),
        "file_hit": bool(target_alerts), "candidate_line_hit": exact,
        "has_line_candidates": any(label.get("line_candidates") for label in labels),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("labels/eval-ready.jsonl"))
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/score"))
    parser.add_argument("--exclude-rule", action="append", default=[],
                        help="Ignore a SARIF rule ID, e.g. a parser diagnostic; repeat as needed")
    args = parser.parse_args()
    cases = [json.loads(line) for line in args.manifest.open()]
    rows = []
    missing = []
    for case in cases:
        path = args.results / f"{case['id']}.sarif"
        if not path.exists():
            alt = args.results / case["id"] / "results.sarif"
            path = alt if alt.exists() else path
        if not path.exists():
            missing.append(case["id"])
            continue
        rows.append(score_case(case, findings(path, set(args.exclude_rule))))
    castle = [row for row in rows if row["dataset"] == "castle"]
    positives = [row for row in castle if row["ground_truth"] == "positive"]
    negatives = [row for row in castle if row["ground_truth"] == "negative"]
    projects = [row for row in rows if row["dataset"] != "castle"]
    full_projects = [row for row in projects if row["source_scope"] == "full_project_snapshot"]
    embedded_files = [row for row in projects if row["source_scope"] == "embedded_vulnerable_file"]
    target_file_smoke = [row for row in projects if row["source_scope"] == "target_file_smoke"]
    summary = {
        "manifest_cases": len(cases), "scored_cases": len(rows),
        "excluded_rules": args.exclude_rule,
        "missing_cases": len(missing), "missing_ids": missing,
        "castle_positive_scored": len(positives),
        "castle_exact_line_hits": sum(row["candidate_line_hit"] for row in positives),
        "castle_file_hits": sum(row["file_hit"] for row in positives),
        "castle_negative_scored": len(negatives),
        "castle_negative_cases_with_alerts": sum(row["target_file_alerts"] > 0 for row in negatives),
        "non_castle_cases_scored": len(projects),
        "non_castle_target_file_hits": sum(row["file_hit"] for row in projects),
        "non_castle_line_candidate_cases_scored": sum(row["has_line_candidates"] for row in projects),
        "non_castle_patch_candidate_line_hits": sum(row["candidate_line_hit"] for row in projects),
        "full_project_cases_scored": len(full_projects),
        "full_project_target_file_hits": sum(row["file_hit"] for row in full_projects),
        "embedded_file_cases_scored": len(embedded_files),
        "embedded_file_target_file_hits": sum(row["file_hit"] for row in embedded_files),
        "embedded_file_line_candidate_cases_scored": sum(row["has_line_candidates"] for row in embedded_files),
        "target_file_smoke_cases_scored": len(target_file_smoke),
        "target_file_smoke_hits": sum(row["file_hit"] for row in target_file_smoke),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    (args.output.with_suffix(".json")).write_text(json.dumps(summary, indent=2))
    with args.output.with_suffix(".csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]) if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({key: value for key, value in summary.items() if key != "missing_ids"}, indent=2))


if __name__ == "__main__":
    main()
