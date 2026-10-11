#!/usr/bin/env python3
"""Run the locally installed Clang analyzer on all CASTLE source files."""

import argparse
import json
import shlex
import shutil
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("labels/castle.jsonl"))
    parser.add_argument("--results", type=Path, default=Path("results/clang-castle"))
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--include-source-root", action="store_true")
    parser.add_argument("--include-path", action="append", default=[])
    parser.add_argument("--preinclude", action="append", default=[])
    parser.add_argument("--define", action="append", default=[])
    parser.add_argument("--compile-db", type=Path,
                        help="Use exact translation-unit flags from compile_commands.json")
    args = parser.parse_args()
    compiler = shutil.which(args.clang) if not args.compile_db else None
    if not args.compile_db and not compiler:
        raise SystemExit(f"Clang not found: {args.clang}")
    compile_commands = {}
    if args.compile_db:
        for entry in json.loads(args.compile_db.read_text()):
            compile_commands[str(Path(entry["file"]).resolve())] = entry
    args.results.mkdir(parents=True, exist_ok=True)
    cases = [json.loads(line) for line in args.manifest.open()]
    if args.case_id:
        cases = [case for case in cases if case["id"] in args.case_id]
    failures = []
    timings = []
    for number, case in enumerate(cases, 1):
        started = time.perf_counter()
        source_file = case.get("source_file") or case["labels"][0]["path"]
        source = Path(case["source_dir"]) / source_file
        includes = (["-I", case["source_dir"], "-I", str(Path(case["source_dir"]) / "include")]
                    if args.include_source_root else [])
        for path in args.include_path:
            includes.extend(["-I", path])
        for header in args.preinclude:
            includes.extend(["-include", header])
        includes.extend(f"-D{definition}" for definition in args.define)
        output = args.results / f"{case['id']}.sarif"
        output.unlink(missing_ok=True)
        cwd = None
        if args.compile_db:
            entry = compile_commands.get(str(source.resolve()))
            if entry is None:
                failures.append({"id": case["id"], "error": "source absent from compile database"})
                timings.append({"id": case["id"], "seconds": round(time.perf_counter() - started, 3),
                                "completed": False})
                continue
            original = entry.get("arguments") or shlex.split(entry["command"])
            command = []
            skip_next = False
            for arg in original:
                if skip_next:
                    skip_next = False
                    continue
                if arg == "-o":
                    skip_next = True
                elif arg != "-c":
                    command.append(arg)
            command.extend(["--analyze", "--analyzer-output", "sarif", "-o", str(output.resolve())])
            cwd = entry["directory"]
        else:
            command = [compiler, "--analyze", "--analyzer-output", "sarif",
                       "-x", "c" if case["language"] == "C" else "c++",
                       "-Wno-error=int-conversion",
                       "-Wno-error=implicit-function-declaration",
                       *includes, "-o", str(output), str(source)]
        try:
            result = subprocess.run(
                command, cwd=cwd, capture_output=True, text=True, timeout=args.timeout,
            )
            valid_output = False
            if result.returncode == 0 and output.exists():
                try:
                    valid_output = json.loads(output.read_text()).get("version") == "2.1.0"
                except (UnicodeError, json.JSONDecodeError):
                    pass
            if not valid_output:
                output.unlink(missing_ok=True)
                failures.append({"id": case["id"], "returncode": result.returncode, "stderr": result.stderr[-2000:]})
        except subprocess.TimeoutExpired:
            output.unlink(missing_ok=True)
            failures.append({"id": case["id"], "error": "timeout"})
        timings.append({"id": case["id"], "seconds": round(time.perf_counter() - started, 3),
                        "completed": output.exists()})
        if number % 50 == 0 or number == len(cases):
            print(f"{number}/{len(cases)} files analyzed")
    (args.results / "failures.json").write_text(json.dumps(failures, indent=2))
    (args.results / "timings.json").write_text(json.dumps({
        "total_seconds": round(sum(item["seconds"] for item in timings), 3),
        "cases": timings,
    }, indent=2))
    print(f"Completed {len(cases) - len(failures)} of {len(cases)} cases; failures: {len(failures)}")


if __name__ == "__main__":
    main()
