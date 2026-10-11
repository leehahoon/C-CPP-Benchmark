#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$root_dir"

mode="${1:-all}"
if [[ $# -gt 1 ]] || [[ "$mode" != all && "$mode" != prepare && "$mode" != smoke ]]; then
  echo "Usage: bash docker_build.sh [all|prepare|smoke]" >&2
  exit 2
fi

echo '[1/3] Docker 이미지 빌드'
bash docker/run.sh build

echo '[2/3] 컨테이너에서 원본 다운로드, 해시 검증, 압축 해제, 라벨 생성'
docker run --rm --security-opt no-new-privileges --cap-drop ALL \
  --user "$(id -u):$(id -g)" --env HOME=/tmp \
  --mount "type=bind,source=$root_dir,target=/workspace" \
  --workdir /workspace ccpp-benchmark:local \
  bash scripts/fetch_data.sh

if [[ "$mode" == prepare ]]; then
  echo '데이터 준비 완료. 전체 평가는 bash docker_build.sh all 로 실행하세요.'
  exit
fi

run_case() {
  echo "[3/3] 평가: $1"
  bash docker/run.sh "$1"
}

run_case castle
run_case score-castle
run_case cppcheck-castle
run_case score-cppcheck-castle

if [[ "$mode" == smoke ]]; then
  echo 'CASTLE 검증 완료. 전체 평가는 bash docker_build.sh all 로 실행하세요.'
  exit
fi

run_case reposvul-files
run_case score-reposvul-files
run_case clang-reposvul-files
run_case score-clang-reposvul-files
run_case projects-small
run_case score-projects-small
run_case clang-file-project
run_case score-clang-file-project
run_case clang-exiv2-project
run_case score-clang-exiv2-project
run_case cppcheck-sec-target
run_case score-cppcheck-sec-target
run_case clang-sec-target
run_case score-clang-sec-target

echo '[3/3] 평가: V8 전체 소스 (시간 제한 없음)'
BENCH_TIMEOUT=0 bash docker/run.sh projects-v8
run_case score-projects-v8

echo '[3/3] 평가: Linux 전체 소스 (기본 제한 1,200초)'
BENCH_TIMEOUT="${BENCH_LINUX_TIMEOUT:-1200}" bash docker/run.sh projects-linux
run_case score-projects-linux

echo '전체 평가 완료. README.md와 results/에서 결과를 확인하세요.'
