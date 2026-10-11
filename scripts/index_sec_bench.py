#!/usr/bin/env python3
"""Create static-analysis labels from SEC-bench-Pro metadata and fix patches.

Patch locations are candidates in the vulnerable revision, not manually
validated flaw lines. The upstream benchmark grades exploit/repair behavior.
"""

import argparse
import json
import re
from pathlib import Path


HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def patch_locations(text):
    """Return old-side changed lines by path, preserving deletion groups."""
    locations = {}
    path = None
    old_line = None
    old_remaining = new_remaining = 0
    group = []

    def flush():
        if path and group:
            locations.setdefault(path, []).append({
                "start": group[0], "end": group[-1],
                "basis": "fix_patch_deleted_lines",
            })
            group.clear()

    for line in text.splitlines():
        if line.startswith("diff --git "):
            flush()
            match = re.match(r"diff --git a/(.+) b/(.+)$", line)
            path = match.group(1) if match else None
            old_line = None
        elif line.startswith("@@ "):
            flush()
            match = HUNK.match(line)
            if match:
                old_line = int(match.group(1))
                old_remaining = int(match.group(2) or 1)
                new_remaining = int(match.group(4) or 1)
                # Pure insertions have no old-side changed line. Their
                # adjacent line is a weaker candidate anchor.
                if old_remaining == 0:
                    locations.setdefault(path, []).append({
                        "start": max(1, old_line), "end": max(1, old_line),
                        "basis": "fix_patch_insertion_anchor",
                    })
        elif old_line is not None:
            if line.startswith("-") and not line.startswith("---"):
                group.append(old_line)
                old_line += 1
                old_remaining -= 1
            elif line.startswith("+") and not line.startswith("+++"):
                flush()
                new_remaining -= 1
            elif line.startswith(" "):
                flush()
                old_line += 1
                old_remaining -= 1
                new_remaining -= 1
            elif line.startswith("\\ No newline"):
                continue
            else:
                flush()
                old_line = None
            if old_remaining == 0 and new_remaining == 0:
                flush()
                old_line = None
    flush()
    return locations


def vulnerable_revision(project, meta, dockerfile):
    if project == "linux":
        return meta.get("kernel", {}).get("build_commit")
    text = dockerfile.read_text(errors="replace") if dockerfile.exists() else ""
    match = re.search(r"\bgit checkout\s+(?:--detach\s+)?([^\s;&]+)", text)
    if not match:
        return None
    revision = match.group(1)
    if revision == "FETCH_HEAD":
        fetch = re.search(r"\bgit fetch[^\n]*\borigin\s+([0-9a-f]{40})", text)
        return fetch.group(1) if fetch else None
    return revision


def build(source):
    cases = []
    for meta_path in sorted((source / "projects").glob("*/*/meta.json")):
        project = meta_path.parent.parent.name
        case_id = meta_path.parent.name
        meta = json.loads(meta_path.read_text())
        locations = {}
        for fix in meta.get("fixes", []):
            if fix.get("kind") != "patch_file" or fix.get("role") not in (None, "primary"):
                continue
            patch = meta_path.parent / fix.get("path", "")
            if not patch.is_file():
                continue
            for path, spans in patch_locations(patch.read_text(errors="replace")).items():
                locations.setdefault(path, []).extend(spans)
        labels = []
        for target in meta.get("target_source_files", []):
            spans = locations.get(target, [])
            labels.append({
                "path": target,
                "file_label": "upstream_target_source_file",
                "line_candidates": spans,
                "line_status": "patch_derived_candidates" if spans else "no_patch_line_candidates",
            })
        cases.append({
            "dataset": "sec-bench-pro",
            "id": f"sec-{project}-{case_id}",
            "upstream_id": case_id,
            "project": project,
            "language": "C" if project == "linux" else "C++",
            "vulnerable_revision": vulnerable_revision(project, meta, meta_path.parent / "Dockerfile"),
            "image": meta.get("image_name"),
            "vulnerability_type": meta.get("target_vulnerability_type"),
            "cve": meta.get("cve_id"),
            "case_dir": str(meta_path.parent.relative_to(source)),
            "labels": labels,
            "source_status": "upstream_docker_image_or_checkout_required",
        })
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("sources/sec-bench-pro"))
    parser.add_argument("--output", type=Path, default=Path("labels/sec-bench-pro.jsonl"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cases = build(args.source)
    with args.output.open("w") as output:
        for case in cases:
            output.write(json.dumps(case, ensure_ascii=False) + "\n")
    print(f"Indexed {len(cases)} SEC-bench-Pro cases in {args.output}")


if __name__ == "__main__":
    main()
