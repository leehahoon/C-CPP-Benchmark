#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/index_sec_bench.py
python3 scripts/index_reposvul.py data/raw/reposvul/reposvul-c.jsonl \
  --output labels/reposvul-c.jsonl
python3 scripts/index_reposvul.py data/raw/reposvul/reposvul-cpp.jsonl \
  --output labels/reposvul-cpp.jsonl
python3 scripts/index_castle.py
python3 scripts/prepare_ready_projects.py
python3 - <<'PY'
import json
from pathlib import Path
source = Path("labels/ready-projects.jsonl")
target = Path("labels/ready-small-projects.jsonl")
target.write_text("".join(line for line in source.open() if json.loads(line)["dataset"] == "reposvul"))
Path("labels/ready-sec-v8.jsonl").write_text(
    "".join(line for line in source.open() if json.loads(line)["id"] == "sec-v8-472139305")
)
Path("labels/ready-sec-linux.jsonl").write_text(
    "".join(line for line in source.open() if json.loads(line)["id"] == "sec-linux-CVE-2022-0185")
)
with Path("labels/ready-target-files.jsonl").open("w") as output:
    for line in source.open():
        case = json.loads(line)
        case["source_scope"] = "target_file_smoke"
        output.write(json.dumps(case, ensure_ascii=False) + "\n")
Path("labels/ready-sec-target-files.jsonl").write_text(
    "".join(line for line in Path("labels/ready-target-files.jsonl").open()
            if json.loads(line)["dataset"] == "sec-bench-pro")
)
Path("labels/ready-reposvul-target-files.jsonl").write_text(
    "".join(line for line in Path("labels/ready-target-files.jsonl").open()
            if json.loads(line)["dataset"] == "reposvul")
)
for short_name, case_id in (("file", "rv-c-566-447558595a36-0"),
                            ("exiv2", "rv-cpp-5659-d639e45c2cdc-0")):
    Path(f"labels/ready-{short_name}-target.jsonl").write_text(
        "".join(line for line in Path("labels/ready-target-files.jsonl").open()
                if json.loads(line)["id"] == case_id)
    )
PY
cat labels/castle.jsonl labels/ready-projects.jsonl > labels/eval-ready.jsonl
cat labels/reposvul-c.jsonl labels/reposvul-cpp.jsonl > labels/reposvul-files.jsonl
python3 - <<'PY'
import json
from pathlib import Path
with Path("labels/eval-all-ready.jsonl").open("w") as output:
    for name in ("castle", "reposvul-files", "ready-projects"):
        for line in Path(f"labels/{name}.jsonl").open():
            if name != "ready-projects" or json.loads(line)["dataset"] == "sec-bench-pro":
                output.write(line)
PY

echo "Ready manifest: labels/eval-ready.jsonl"
