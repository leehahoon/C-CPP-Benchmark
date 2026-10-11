#!/usr/bin/env python3
"""Extract ReposVul's positive C/C++ files and conservative location labels."""

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from index_sec_bench import patch_locations


HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}


def safe_path(name):
    path = PurePosixPath(name or "")
    if not name or path.is_absolute() or ".." in path.parts or path.suffix.lower() not in SUFFIXES:
        return None
    return path


def patch_matches_code(patch, code):
    """Check old-side context and deletions against the embedded pre-fix file."""
    lines = code.splitlines()
    old_line = None
    checked = 0
    for line in (patch or "").splitlines():
        match = HUNK.match(line)
        if match:
            old_line = int(match.group(1))
            continue
        if old_line is None:
            continue
        if line.startswith((" ", "-")) and not line.startswith("---"):
            if old_line < 1 or old_line > len(lines) or lines[old_line - 1] != line[1:]:
                return False, checked
            checked += 1
            old_line += 1
        elif line.startswith("+") or line.startswith("\\ No newline"):
            continue
        else:
            old_line = None
    return checked > 0, checked


def positive_detail(value):
    # Upstream's 1/0/-1 labels are retained; only 1 is treated as positive.
    return value == 1 or value == "1"


def build(inputs, output, files_root):
    counts = {"records": 0, "positives": 0, "materialized": 0, "unaligned": 0, "skipped": 0}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as out:
        for source in inputs:
            with source.open(encoding="utf-8") as stream:
                for record in stream:
                    data = json.loads(record)
                    counts["records"] += 1
                    language = data.get("cve_language")
                    if language not in ("C", "C++"):
                        continue
                    fix_commit = data.get("commit_id") or "unknown"
                    index = str(data.get("index", counts["records"]))
                    if not index.isdigit():
                        index = str(counts["records"])
                    for detail_index, detail in enumerate(data.get("details") or []):
                        if not positive_detail(detail.get("target")):
                            continue
                        counts["positives"] += 1
                        path = safe_path(detail.get("file_name"))
                        code = detail.get("code_before")
                        if path is None or not isinstance(code, str) or not code:
                            counts["skipped"] += 1
                            continue
                        kind = "c" if language == "C" else "cpp"
                        case_id = f"rv-{kind}-{index}-{fix_commit[:12]}-{detail_index}"
                        case_root = files_root / case_id
                        file_path = case_root.joinpath(*path.parts)
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(code)
                        patch = detail.get("patch") or ""
                        aligned, checked = patch_matches_code(patch, code)
                        candidates = patch_locations(f"diff --git a/{path} b/{path}\n{patch}").get(str(path), []) if patch else []
                        if not aligned:
                            candidates = []
                            counts["unaligned"] += 1
                        parents = data.get("parents") or []
                        parent = parents[0].get("commit_id_before") if parents else None
                        item = {
                            "dataset": "reposvul",
                            "id": case_id,
                            "upstream_index": data.get("index"),
                            "project": data.get("project"),
                            "language": language,
                            "cve": data.get("cve_id"),
                            "cwe": data.get("cwe_id"),
                            "fix_commit": fix_commit,
                            "vulnerable_revision_hint": parent,
                            "source_scope": "embedded_vulnerable_file",
                            "source_dir": str(case_root),
                            "source_sha256": hashlib.sha256(code.encode()).hexdigest(),
                            "labels": [{
                                "path": str(path),
                                "file_label": "upstream_target_1",
                                "line_candidates": candidates,
                                "line_status": "aligned_fix_patch_candidates" if aligned and candidates else "unverified_or_no_patch_candidates",
                                "patch_old_lines_checked": checked,
                            }],
                        }
                        out.write(json.dumps(item, ensure_ascii=False) + "\n")
                        counts["materialized"] += 1
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("labels/reposvul.jsonl"))
    parser.add_argument("--files-root", type=Path, default=Path("workloads/reposvul_files"))
    args = parser.parse_args()
    print(build(args.inputs, args.output, args.files_root))


if __name__ == "__main__":
    main()
