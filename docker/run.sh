#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"
image="ccpp-benchmark:local"
mode="${1:-}"
project_timeout="${BENCH_TIMEOUT:-1200}"

if [[ "$mode" == build ]]; then
  docker build -t "$image" docker
  exit
fi

mkdir -p results
container=(docker run --rm --network none --security-opt no-new-privileges
  --cap-drop ALL --user "$(id -u):$(id -g)"
  --mount "type=bind,source=$root_dir,target=/workspace"
  --workdir /workspace "$image")

case "$mode" in
  castle)
    "${container[@]}" python3 scripts/run_clang_castle.py --results results/docker-clang-castle
    ;;
  cppcheck-castle)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py \
      --manifest labels/castle.jsonl --scope target-files \
      --results results/docker-cppcheck-castle
    ;;
  projects)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py \
      --max-configs 1 --timeout "$project_timeout" \
      --results results/docker-cppcheck-projects
    ;;
  projects-small)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py \
      --manifest labels/ready-small-projects.jsonl \
      --results results/docker-cppcheck-projects-small
    ;;
  clang-projects-small-target)
    "${container[@]}" python3 scripts/run_clang_castle.py \
      --manifest labels/ready-small-projects.jsonl --include-source-root \
      --results results/docker-clang-projects-small-target --timeout 300
    ;;
  clang-exiv2-project)
    "${container[@]}" cmake -G Ninja \
      -S workloads/reposvul_projects/rv-cpp-5659-exiv2/source \
      -B results/exiv2-build-ninja -DCMAKE_CXX_COMPILER=clang++ \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DEXIV2_ENABLE_XMP=OFF \
      -DEXIV2_ENABLE_PNG=OFF -DEXIV2_BUILD_SAMPLES=OFF \
      -DEXIV2_BUILD_EXIV2_COMMAND=OFF -DEXIV2_BUILD_DOC=OFF \
      -DEXIV2_BUILD_UNIT_TESTS=OFF
    "${container[@]}" python3 scripts/run_clang_castle.py \
      --manifest labels/ready-exiv2-target.jsonl \
      --compile-db results/exiv2-build-ninja/compile_commands.json \
      --results results/docker-clang-exiv2-project --timeout 300
    ;;
  clang-file-project)
    mkdir -p results/file-build
    sed 's/X.YY/516/' \
      workloads/reposvul_projects/rv-c-566-file/source/src/magic.h.in \
      > results/file-build/magic.h
    "${container[@]}" python3 scripts/run_clang_castle.py \
      --manifest labels/ready-file-target.jsonl --include-source-root \
      --include-path results/file-build --preinclude stdint.h \
      --define HAVE_STRERROR --define HAVE_STRTOUL --define HAVE_LOCALE_H \
      --results results/docker-clang-file-project --timeout 300
    ;;
  projects-v8)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py \
      --case-id sec-v8-472139305 --max-configs 1 --timeout "$project_timeout" \
      --results results/docker-cppcheck-v8
    ;;
  projects-linux)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py \
      --case-id sec-linux-CVE-2022-0185 --max-configs 1 --timeout "$project_timeout" \
      --results results/docker-cppcheck-linux
    ;;
  target-files)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py --scope target-files \
      --results results/docker-cppcheck-target-files
    ;;
  reposvul-files)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py \
      --manifest labels/reposvul-files.jsonl --scope target-files \
      --max-configs 1 --timeout 300 --results results/docker-cppcheck-reposvul-files
    ;;
  clang-reposvul-files)
    "${container[@]}" python3 scripts/run_clang_castle.py \
      --manifest labels/reposvul-files.jsonl --results results/docker-clang-reposvul-files \
      --timeout 120
    ;;
  cppcheck-sec-target)
    "${container[@]}" python3 scripts/run_cppcheck_projects.py \
      --manifest labels/ready-projects.jsonl --scope target-files \
      --case-id sec-linux-CVE-2022-0185 --case-id sec-v8-472139305 \
      --results results/docker-cppcheck-sec-target
    ;;
  clang-sec-target)
    "${container[@]}" python3 scripts/run_clang_castle.py \
      --manifest labels/ready-projects.jsonl --include-source-root \
      --case-id sec-linux-CVE-2022-0185 --case-id sec-v8-472139305 \
      --results results/docker-clang-sec-target --timeout 300
    ;;
  score-castle)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/castle.jsonl \
      --results results/docker-clang-castle --output results/docker-clang-castle-score
    ;;
  score-cppcheck-castle)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/castle.jsonl \
      --results results/docker-cppcheck-castle --output results/docker-cppcheck-castle-score
    ;;
  score-clang-reposvul-files)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/reposvul-files.jsonl \
      --results results/docker-clang-reposvul-files --output results/docker-clang-reposvul-files-score
    ;;
  score-clang-exiv2-project)
    "${container[@]}" python3 scripts/evaluate_sarif.py \
      --manifest labels/ready-exiv2-target.jsonl \
      --results results/docker-clang-exiv2-project \
      --output results/docker-clang-exiv2-project-score
    ;;
  score-clang-file-project)
    "${container[@]}" python3 scripts/evaluate_sarif.py \
      --manifest labels/ready-file-target.jsonl \
      --results results/docker-clang-file-project \
      --output results/docker-clang-file-project-score
    ;;
  score-cppcheck-sec-target)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/ready-sec-target-files.jsonl \
      --results results/docker-cppcheck-sec-target --output results/docker-cppcheck-sec-target-score \
      --exclude-rule unknownMacro --exclude-rule syntaxError \
      --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
    ;;
  score-clang-sec-target)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/ready-sec-target-files.jsonl \
      --results results/docker-clang-sec-target --output results/docker-clang-sec-target-score
    ;;
  score-projects)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/ready-projects.jsonl \
      --results results/docker-cppcheck-projects --output results/docker-cppcheck-projects-score \
      --exclude-rule unknownMacro --exclude-rule syntaxError \
      --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
    ;;
  score-projects-small)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/ready-small-projects.jsonl \
      --results results/docker-cppcheck-projects-small --output results/docker-cppcheck-projects-small-score \
      --exclude-rule unknownMacro --exclude-rule syntaxError \
      --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
    ;;
  score-projects-v8)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/ready-sec-v8.jsonl \
      --results results/docker-cppcheck-v8 --output results/docker-cppcheck-v8-score \
      --exclude-rule unknownMacro --exclude-rule syntaxError \
      --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
    ;;
  score-projects-linux)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/ready-sec-linux.jsonl \
      --results results/docker-cppcheck-linux --output results/docker-cppcheck-linux-score \
      --exclude-rule unknownMacro --exclude-rule syntaxError \
      --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
    ;;
  score-target-files)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/ready-target-files.jsonl \
      --results results/docker-cppcheck-target-files --output results/docker-cppcheck-target-files-score \
      --exclude-rule unknownMacro --exclude-rule syntaxError \
      --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
    ;;
  score-reposvul-files)
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest labels/reposvul-files.jsonl \
      --results results/docker-cppcheck-reposvul-files \
      --output results/docker-cppcheck-reposvul-files-filtered-score \
      --exclude-rule unknownMacro --exclude-rule syntaxError \
      --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
    ;;
  score)
    if [[ $# -ne 4 ]]; then
      echo "Usage: docker/run.sh score MANIFEST RESULT_DIR OUTPUT_PREFIX" >&2
      exit 2
    fi
    "${container[@]}" python3 scripts/evaluate_sarif.py --manifest "$2" \
      --results "$3" --output "$4"
    ;;
  *)
    echo "Usage: docker/run.sh {build|castle|cppcheck-castle|projects|projects-small|projects-v8|projects-linux|target-files|reposvul-files|clang-reposvul-files|clang-projects-small-target|clang-file-project|clang-exiv2-project|cppcheck-sec-target|clang-sec-target|score-castle|score-cppcheck-castle|score-clang-reposvul-files|score-clang-file-project|score-clang-exiv2-project|score-cppcheck-sec-target|score-clang-sec-target|score-projects|score-projects-small|score-projects-v8|score-projects-linux|score-target-files|score-reposvul-files|score MANIFEST RESULT_DIR OUTPUT_PREFIX}" >&2
    exit 2
    ;;
esac
