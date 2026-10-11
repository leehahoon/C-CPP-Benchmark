#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

check_sha256() {
  local path="$1" expected="$2" actual
  actual="$(shasum -a 256 "$path" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "SHA-256 불일치: $path ($actual)" >&2
    return 1
  fi
}

download_archive() {
  local url="$1" path="$2" expected="${3:-}" tmp
  mkdir -p "$(dirname "$path")"
  if [[ -f "$path" ]]; then
    if [[ -z "$expected" ]] || check_sha256 "$path" "$expected"; then
      echo "재사용: $path"
      return
    fi
    echo "기존 파일의 해시가 다릅니다. 삭제 후 다시 실행하세요: $path" >&2
    exit 1
  fi
  tmp="${path}.part"
  rm -f "$tmp"
  curl -fL --retry 3 --output "$tmp" "$url"
  if [[ -n "$expected" ]]; then check_sha256 "$tmp" "$expected"; fi
  mv "$tmp" "$path"
}

download_drive() {
  local id="$1" path="$2" expected="$3" tmp
  mkdir -p "$(dirname "$path")"
  if [[ -f "$path" ]]; then
    check_sha256 "$path" "$expected"
    echo "재사용: $path"
    return
  fi
  if ! command -v gdown >/dev/null 2>&1; then
    echo "ReposVul 다운로드에 gdown이 필요합니다. README의 가상환경 설치 명령을 실행하세요." >&2
    exit 1
  fi
  tmp="${path}.part"
  rm -f "$tmp"
  gdown "$id" -O "$tmp"
  check_sha256 "$tmp" "$expected"
  mv "$tmp" "$path"
}

extract_archive() {
  local archive="$1" target="$2"
  if [[ -d "$target" ]] && [[ -n "$(find "$target" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "압축 해제 건너뜀: $target"
    return
  fi
  mkdir -p "$target"
  tar -xzf "$archive" --strip-components=1 -C "$target"
}

fetch_source() {
  local name="$1" repo="$2" commit="$3" target="sources/$1"
  local archive="data/raw/upstream/${name}-${commit}.tar.gz"
  if [[ -d "$target/.git" ]]; then
    if [[ "$(git -C "$target" rev-parse HEAD)" != "$commit" ]]; then
      echo "원본 저장소 버전이 다릅니다: $target" >&2
      exit 1
    fi
    echo "재사용: $target"
    return
  fi
  if [[ -f "$target/.source-revision" ]] && [[ "$(cat "$target/.source-revision")" == "$commit" ]]; then
    echo "재사용: $target"
    return
  fi
  if [[ -d "$target" ]] && [[ -n "$(find "$target" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "버전을 확인할 수 없는 폴더가 있습니다: $target" >&2
    exit 1
  fi
  download_archive "https://codeload.github.com/${repo}/tar.gz/${commit}" "$archive"
  extract_archive "$archive" "$target"
  printf '%s\n' "$commit" > "$target/.source-revision"
}

fetch_source reposvul Eshe0922/ReposVul 67f53000715d0636403261f5f762d9bec13b9b3d
fetch_source sec-bench-pro SEC-bench/SEC-bench-Pro da80928ee20dc417ca6a068a1213e1d9d279df20
fetch_source castle-benchmark CASTLE-Benchmark/CASTLE-Benchmark c7391c9ec5dd944653103fbf55e7ebbf85842d82

download_drive 1UNHKaEU1Hls5fmOFLW2YefGN1FqGeOrA data/raw/reposvul/reposvul-c.jsonl d238394c57e14bedfd4c6cc37617f7beeefddf289642fed75b1f27913d59cac7
download_drive 1jYwIOXJUHhbTA0UkKVLQYyuxKBlv2kKO data/raw/reposvul/reposvul-cpp.jsonl 1789f92c118310ae9fcabb31c1b790afeca56b05c66fe03ecf83ef87eba7f8bb

download_archive https://codeload.github.com/file/file/tar.gz/f40883f736e0e065a8943ee8b7ebb0a536590d06 data/raw/reposvul/file-f40883f736e0.tar.gz 9f2cfc7188afe2ceca74e66a9c3573876379179c6ac50bc470d5063e38d37670
download_archive https://codeload.github.com/Exiv2/exiv2/tar.gz/9fd25fcd4b8f23079c9aebddfceba2a78e401833 data/raw/reposvul/exiv2-9fd25fcd4b8f.tar.gz cd180a89f96f48d101980f72125021616298a6dce441e9f0f0eaca4b127425e9
download_archive https://codeload.github.com/torvalds/linux/tar.gz/8357f6fb3d9a02ac55f0d758b9c79b4647c18bcb data/raw/sec/linux-8357f6fb3d9a.tar.gz 97d0e2ab95ce053f0bb89260a8cddfab5454bb783677fef8803f96c405bed006
download_archive https://codeload.github.com/v8/v8/tar.gz/b5aa4c8b718d75f9cf4d4afd635ffd217f0acb38 data/raw/sec/v8-b5aa4c8b718d.tar.gz b2372e810aa5f202015a8490ffdb4ea05db76481f2a48ad165b9f16cad0ea377

extract_archive data/raw/reposvul/file-f40883f736e0.tar.gz workloads/reposvul_projects/rv-c-566-file/source
extract_archive data/raw/reposvul/exiv2-9fd25fcd4b8f.tar.gz workloads/reposvul_projects/rv-cpp-5659-exiv2/source
extract_archive data/raw/sec/linux-8357f6fb3d9a.tar.gz workloads/sec/sec-linux-CVE-2022-0185/source
extract_archive data/raw/sec/v8-b5aa4c8b718d.tar.gz workloads/sec/sec-v8-472139305/source

bash scripts/rebuild_labels.sh
