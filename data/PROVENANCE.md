# 다운로드 출처와 고정 버전

2026-10-10에 다운로드한 공개 자료입니다. 원본 Git 저장소는 `sources/`에 보관하고, 평가용 파일과 라벨만 별도 생성했습니다.

| 원본 저장소 | 고정 커밋 |
|---|---|
| [ReposVul](https://github.com/Eshe0922/ReposVul) | `67f53000715d0636403261f5f762d9bec13b9b3d` |
| [SEC-bench-Pro](https://github.com/SEC-bench/SEC-bench-Pro) | `da80928ee20dc417ca6a068a1213e1d9d279df20` |
| [CASTLE-Benchmark](https://github.com/CASTLE-Benchmark/CASTLE-Benchmark) | `c7391c9ec5dd944653103fbf55e7ebbf85842d82` |

## ReposVul JSONL

| 파일 | 공개 Google Drive ID | SHA-256 |
|---|---|---|
| `raw/reposvul/reposvul-c.jsonl` | `1UNHKaEU1Hls5fmOFLW2YefGN1FqGeOrA` | `d238394c57e14bedfd4c6cc37617f7beeefddf289642fed75b1f27913d59cac7` |
| `raw/reposvul/reposvul-cpp.jsonl` | `1jYwIOXJUHhbTA0UkKVLQYyuxKBlv2kKO` | `1789f92c118310ae9fcabb31c1b790afeca56b05c66fe03ecf83ef87eba7f8bb` |

## 전체 프로젝트 스냅샷

| 사례 | 수정 전 소스 커밋 | 압축 파일 SHA-256 |
|---|---|---|
| ReposVul `file/file`, CVE-2014-2270 | [`f40883f736e0e065a8943ee8b7ebb0a536590d06`](https://github.com/file/file/tree/f40883f736e0e065a8943ee8b7ebb0a536590d06) | `9f2cfc7188afe2ceca74e66a9c3573876379179c6ac50bc470d5063e38d37670` |
| ReposVul `Exiv2/exiv2`, CVE-2021-29463 | [`9fd25fcd4b8f23079c9aebddfceba2a78e401833`](https://github.com/Exiv2/exiv2/tree/9fd25fcd4b8f23079c9aebddfceba2a78e401833) | `cd180a89f96f48d101980f72125021616298a6dce441e9f0f0eaca4b127425e9` |
| SEC Linux `CVE-2022-0185` | [`8357f6fb3d9a02ac55f0d758b9c79b4647c18bcb`](https://github.com/torvalds/linux/tree/8357f6fb3d9a02ac55f0d758b9c79b4647c18bcb) | `97d0e2ab95ce053f0bb89260a8cddfab5454bb783677fef8803f96c405bed006` |
| SEC V8 `472139305` | [`b5aa4c8b718d75f9cf4d4afd635ffd217f0acb38`](https://github.com/v8/v8/tree/b5aa4c8b718d75f9cf4d4afd635ffd217f0acb38) | `b2372e810aa5f202015a8490ffdb4ea05db76481f2a48ad165b9f16cad0ea377` |

각 압축 파일은 해당 GitHub 저장소의 `codeload.github.com/<owner>/<repo>/tar.gz/<commit>`에서 받았습니다. `shasum -a 256`으로 현재 파일과 위 값을 비교할 수 있습니다.
