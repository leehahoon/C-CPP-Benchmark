#!/usr/bin/env python3
"""Select locally downloaded full-project cases and verify their labels."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "rv-c-566-447558595a36-0": "workloads/reposvul_projects/rv-c-566-file/source",
    "rv-cpp-5659-d639e45c2cdc-0": "workloads/reposvul_projects/rv-cpp-5659-exiv2/source",
    "sec-linux-CVE-2022-0185": "workloads/sec/sec-linux-CVE-2022-0185/source",
    "sec-v8-472139305": "workloads/sec/sec-v8-472139305/source",
}
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def removed_lines(text):
    """Map path and old line to the literal line removed by a fix patch."""
    result = {}
    path = None
    old_line = None
    old_left = new_left = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            match = re.match(r"diff --git a/(.+) b/(.+)$", line)
            path = match.group(1) if match else None
            old_line = None
            continue
        match = HUNK.match(line)
        if match:
            old_line = int(match.group(1))
            old_left = int(match.group(2) or 1)
            new_left = int(match.group(4) or 1)
            continue
        if old_line is None:
            continue
        if line.startswith("-") and not line.startswith("---"):
            result.setdefault(path, {})[old_line] = line[1:]
            old_line += 1
            old_left -= 1
        elif line.startswith("+") and not line.startswith("+++"):
            new_left -= 1
        elif line.startswith(" "):
            old_line += 1
            old_left -= 1
            new_left -= 1
        elif not line.startswith("\\ No newline"):
            old_line = None
        if old_left == 0 and new_left == 0:
            old_line = None
    return result


def sec_patch_texts(case):
    base = ROOT / "sources/sec-bench-pro" / case["case_dir"]
    meta = json.loads((base / "meta.json").read_text())
    texts = {}
    for fix in meta.get("fixes", []):
        if fix.get("kind") == "patch_file" and fix.get("role") in (None, "primary"):
            patch = base / fix.get("path", "")
            if patch.is_file():
                for path, lines in removed_lines(patch.read_text(errors="replace")).items():
                    texts.setdefault(path, {}).update(lines)
    return texts


def main():
    cases = {}
    for name in ("reposvul-c", "reposvul-cpp", "sec-bench-pro"):
        with (ROOT / "labels" / f"{name}.jsonl").open() as source:
            cases.update((case["id"], case) for case in map(json.loads, source))
    output = ROOT / "labels/ready-projects.jsonl"
    with output.open("w") as out:
        for case_id, relative_source in PROJECTS.items():
            case = dict(cases[case_id])
            root = ROOT / relative_source
            if not root.is_dir():
                raise FileNotFoundError(root)
            case["source_dir"] = relative_source
            case["source_scope"] = "full_project_snapshot"
            case["source_status"] = "downloaded_full_snapshot"
            case["ground_truth"] = "positive"
            if case["dataset"] == "reposvul":
                import hashlib
                path = root / case["labels"][0]["path"]
                actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual_hash != case["source_sha256"]:
                    raise ValueError(f"Project revision differs from embedded vulnerable file: {case_id}")
                case["source_verification"] = "matches_embedded_code_before_sha256"
            else:
                texts = sec_patch_texts(case)
                for label in case["labels"]:
                    path = root / label["path"]
                    if not path.exists():
                        raise FileNotFoundError(path)
                    code = path.read_text(errors="replace").splitlines()
                    removed = texts.get(label["path"], {})
                    matched = sum(1 for n, text in removed.items() if 1 <= n <= len(code) and code[n - 1] == text)
                    if not removed or matched != len(removed):
                        label["line_candidates"] = []
                        label["line_status"] = "fix_patch_not_aligned_to_snapshot"
                    else:
                        label["line_candidates"] = [x for x in label["line_candidates"] if x["basis"] == "fix_patch_deleted_lines"]
                        label["line_status"] = "fix_patch_deleted_lines_verified_in_snapshot"
                    label["patch_removed_lines_checked"] = len(removed)
                    label["patch_removed_lines_matched"] = matched
                case["source_verification"] = "target_files_exist;_patch_lines_checked"
            out.write(json.dumps(case, ensure_ascii=False) + "\n")
    print(f"Prepared {len(PROJECTS)} full-project cases in {output}")


if __name__ == "__main__":
    main()
