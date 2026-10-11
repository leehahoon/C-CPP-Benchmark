#!/usr/bin/env python3
"""Prepare CASTLE C250 source files and its direct positive/negative labels."""

import argparse
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("sources/castle-benchmark"))
    parser.add_argument("--output", type=Path, default=Path("labels/castle.jsonl"))
    parser.add_argument("--workload", type=Path, default=Path("workloads/castle/source"))
    args = parser.parse_args()
    dataset = json.loads((args.source / "datasets/CASTLE-C250.min.json").read_text())
    original = args.source / "datasets/CASTLE-C250"
    shutil.copytree(original, args.workload, dirs_exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as out:
        for test in dataset["tests"]:
            path = args.workload / test["name"]
            code = path.read_text()
            if code.rstrip("\n") != test["code"].rstrip("\n"):
                raise ValueError(f"Source differs from JSON label: {test['name']}")
            lines = test.get("lines") or []
            if any(not isinstance(n, int) or n < 1 or n > len(code.splitlines()) for n in lines):
                raise ValueError(f"Invalid line label: {test['name']}")
            if not test["vulnerable"] and lines:
                raise ValueError(f"Negative test has line labels: {test['name']}")
            item = {
                "dataset": "castle",
                "id": f"castle-{test['id']}",
                "language": "C",
                "source_scope": "single_file_microbenchmark",
                "source_dir": str(args.workload),
                "source_file": test["name"],
                "ground_truth": "positive" if test["vulnerable"] else "negative",
                "cwe": f"CWE-{test['cwe']}",
                "labels": [{
                    "path": test["name"],
                    "file_label": "upstream_positive",
                    "line_candidates": [{"start": n, "end": n, "basis": "upstream_exact_line"} for n in lines],
                    "line_status": "upstream_exact",
                }] if test["vulnerable"] else [],
            }
            out.write(json.dumps(item) + "\n")
    print(f"Prepared {len(dataset['tests'])} CASTLE cases in {args.workload}")


if __name__ == "__main__":
    main()
