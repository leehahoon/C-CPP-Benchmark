# C/C++ 정적분석 벤치마크 작업 공간

세 공개 벤치마크를 원본과 평가용 산출물로 나눠 보관합니다.

| 벤치마크 | 준비된 데이터 | 정적분석 평가에서의 역할 |
|---|---:|---|
| [ReposVul](https://github.com/Eshe0922/ReposVul) | C 4,010개/C++ 689개 원본 레코드, `target=1`인 취약 파일 729개, 전체 프로젝트 스냅샷 2개 | 실제 프로젝트의 취약 파일 탐지 |
| [SEC-bench-Pro](https://github.com/SEC-bench/SEC-bench-Pro) | 344개 사례의 메타데이터·패치·대상 파일 라벨, 전체 프로젝트 스냅샷 2개 | V8·Linux 실제 프로젝트 사례 |
| [CASTLE C250](https://github.com/CASTLE-Benchmark/CASTLE-Benchmark) | C 파일 250개, 취약 150개·비취약 100개, 원본 줄 라벨 | 줄 탐지와 비취약 파일의 경보 확인 |

## GitHub에서 받은 뒤 한 번에 재현

Git 커밋에는 스크립트, 라벨, 평가 결과를 포함합니다. 수 GB인 원본 다운로드 파일(`data/raw/`), 원본 저장소(`sources/`), 분석 대상 소스(`workloads/`)와 생성된 빌드 파일은 제외합니다. Docker가 실행 중인 새 복제본에서 아래 한 명령을 실행하면 **이미지 빌드 → 컨테이너에서 원본 다운로드·SHA-256 확인·압축 해제·라벨 생성 → Cppcheck·Clang 평가·점수 계산**까지 수행합니다. 다운로드에 필요한 `gdown`도 이미지 안에 설치됩니다.

```bash
bash docker_build.sh
```

다운로드와 압축 해제에는 수 GB의 여유 공간이 필요합니다. 원본은 [고정 버전과 해시](data/PROVENANCE.md)를 사용하며, 이미 받은 파일은 확인 후 재사용합니다. 다운로드 단계에만 컨테이너 네트워크를 사용하고 분석 단계는 네트워크를 끕니다. 생성된 데이터는 호스트의 `data/raw/`, `sources/`, `workloads/`에 저장돼 컨테이너 종료 후에도 남습니다. 평가 결과는 `results/`에 저장됩니다.

`bash docker_build.sh prepare`는 이미지와 데이터·라벨만 준비하고, `bash docker_build.sh smoke`는 CASTLE 두 분석기의 실행과 점수 계산까지 확인합니다. 기본 실행은 CASTLE, ReposVul 취약 파일 729건, 준비된 ReposVul 프로젝트 2건, SEC 대상 파일 2건과 V8·Linux 전체 소스를 분석합니다. V8 전체 소스에는 시간 제한을 두지 않고 Linux 전체 소스는 기본 1,200초 제한으로 실행합니다. Linux 제한은 `BENCH_LINUX_TIMEOUT=3600 bash docker_build.sh`처럼 바꿀 수 있습니다. 이전 실행의 점수·SARIF·시간 기록도 Git 커밋에 포함돼 있습니다.

## 바로 실행

이 Mac에는 Colima Docker 환경과 `ccpp-benchmark:local` 이미지가 준비돼 있습니다. Docker를 다시 시작해야 할 때는 `colima start`를 실행합니다. 이미지만 다시 만들려면 `bash docker/run.sh build`를 실행합니다.

평가 컨테이너는 현재 폴더를 마운트하고 네트워크를 끈 상태에서 실행됩니다.

```bash
bash docker/run.sh castle
bash docker/run.sh score-castle
bash docker/run.sh cppcheck-castle
bash docker/run.sh score-cppcheck-castle
bash docker/run.sh reposvul-files
bash docker/run.sh score-reposvul-files
bash docker/run.sh clang-reposvul-files
bash docker/run.sh score-clang-reposvul-files
bash docker/run.sh projects-small
bash docker/run.sh score-projects-small
bash docker/run.sh clang-file-project
bash docker/run.sh score-clang-file-project
bash docker/run.sh clang-exiv2-project
bash docker/run.sh score-clang-exiv2-project
bash docker/run.sh cppcheck-sec-target
bash docker/run.sh score-cppcheck-sec-target
bash docker/run.sh clang-sec-target
bash docker/run.sh score-clang-sec-target
```

`castle`은 컨테이너의 Clang으로, `cppcheck-castle`은 Cppcheck로 CASTLE 250개 파일을 각각 분석합니다. `reposvul-files`와 `clang-reposvul-files`는 ReposVul의 양성 C/C++ 파일 729개를 각각 분석합니다. `projects-small`은 ReposVul의 C 및 C++ **프로젝트 전체** 두 개를 Cppcheck로 분석합니다. `clang-file-project`와 `clang-exiv2-project`는 준비된 두 프로젝트에서 각각 **대상 파일 한 개**를 빌드 설정과 함께 Clang으로 분석합니다. SEC의 V8·Linux 전체 소스는 각각 `projects-v8`·`projects-linux`로 분석합니다. Linux 전체 분석은 특히 오래 걸릴 수 있습니다. `cppcheck-sec-target`과 `clang-sec-target`은 준비된 SEC 사례 2개의 대상 파일만 분석합니다.

전체 프로젝트의 기본 사례별 제한 시간은 1,200초입니다. 더 길게 실행하려면 `BENCH_TIMEOUT=3600 bash docker/run.sh projects-v8`처럼 지정합니다. 제한 없이 실행하려면 `BENCH_TIMEOUT=0 bash docker/run.sh projects-v8`을 사용합니다.

대형 파일의 실행 시간을 관리하기 위해 `reposvul-files`, `projects-v8`, `projects-linux`, `projects`의 Cppcheck는 파일당 구성 탐색을 1개로 제한합니다. 전체 ReposVul 소규모 프로젝트 스캔은 Cppcheck 기본 구성으로 실행합니다.

빠른 연결 시험은 `bash docker/run.sh target-files`와 `bash docker/run.sh score-target-files`입니다. 이 모드는 네 프로젝트에서 라벨이 붙은 대상 파일만 분석하므로 프로젝트 수준 탐지 성능으로 해석하지 않습니다.

기본 Cppcheck 실행에는 각 프로젝트의 빌드 설정이나 컴파일 데이터베이스가 연결돼 있지 않습니다. Cppcheck 결과는 실행 경로 확인용 기준선이며, 최종 비교에는 평가할 분석기의 빌드·포함 경로 설정을 고정해 사용하세요.

결과는 `results/`에 사례별 SARIF와 점수 JSON·CSV로 저장됩니다. 평가 스크립트는 SARIF 2.1.0을 읽으며, 다른 분석기의 결과도 `<사례 ID>.sarif` 파일명으로 모으면 됩니다.

```bash
bash docker/run.sh score labels/eval-all-ready.jsonl results/my-analyzer results/my-analyzer-score
```

### Coverity 적용 상태

Coverity Analysis 실행 파일과 C/C++ 분석 라이선스는 현재 환경에 없습니다. [공식 설치 안내](https://docs.blackduck.com/r/coverity/2026.9/coverity-documentation/download-installers-and-documentation.html)에 따르면 배포 파일은 Black Duck 계정으로 받아야 하고 분석에는 유효한 라이선스가 필요합니다. 현재 Docker는 Linux ARM64이며, [공식 지원 표](https://docs.blackduck.com/r/coverity/latest/coverity-documentation/supported-platforms-for-coverity-analysis.html)의 Linux ARM64 항목에는 C/C++ 정식 분석 지원이 표시되지 않습니다. Coverity로 이 벤치마크를 평가하려면 C/C++ 분석 라이선스와 Linux x86_64 설치 파일, 해당 아키텍처의 실행 환경이 필요합니다. [무료 Coverity Scan](https://scan.coverity.com/faq/)도 등록된 오픈소스 프로젝트에 대한 서비스로, 이 로컬 벤치마크 모음의 임의 분석을 대신하지 않습니다. 따라서 Coverity 탐지 건수는 아직 측정되지 않았습니다.

라이선스를 갖춘 환경에서 각 사례를 분석한 뒤 `cov-format-errors --json-output-v10` 결과를 `<사례 ID>.json`으로 저장하면, 다음 명령으로 SARIF 변환과 기존 라벨 대조를 할 수 있습니다. 원본 JSON과 변환 결과는 `results/` 아래에 두며, 라이선스 파일은 이 작업 공간에 복사하거나 Docker 이미지에 포함하지 마세요.

```bash
python3 scripts/coverity_json_to_sarif.py --manifest labels/eval-all-ready.jsonl \
  --input-dir results/coverity-json --output-dir results/coverity-sarif
python3 scripts/evaluate_sarif.py --manifest labels/eval-all-ready.jsonl \
  --results results/coverity-sarif --output results/coverity-score
```

변환되지 않은 사례는 점수에서 누락으로 표시됩니다. 특히 ReposVul 취약 파일 729건은 프로젝트별 빌드 정보가 없는 단일 파일 사례이므로, Coverity가 실제로 컴파일·캡처한 파일만 분석된 사례로 세어야 합니다.

`labels/eval-ready.jsonl`은 CASTLE 250건과 전체 프로젝트 4건으로 이뤄진 프로젝트 중심 입문 세트입니다. `labels/eval-all-ready.jsonl`은 CASTLE 250건, ReposVul 취약 파일 729건, SEC 전체 프로젝트 2건을 합친 981건의 전체 준비 세트입니다. 각 레코드의 `source_dir`이 분석할 소스 루트입니다. CASTLE은 `source_file` 하나씩, ReposVul 파일 사례는 라벨의 `path` 하나씩, 전체 프로젝트 사례는 `source_dir` 전체를 분석합니다. 분석기마다 빌드 방식이 다르므로 분석기 실행 명령은 그 도구에 맞춰 지정해야 합니다.

## 폴더 구조

```text
sources/                     세 벤치마크의 원본 Git 저장소
data/raw/reposvul/           C·C++ 원본 JSONL과 선택한 프로젝트 압축본
data/raw/sec/                선택한 V8·Linux 소스 압축본
workloads/castle/source/     CASTLE C250 실행용 C 파일
workloads/reposvul_files/   ReposVul target=1 취약 파일 729개
workloads/reposvul_projects/  C file/file, C++ Exiv2 전체 소스
workloads/sec/              SEC Linux, V8 전체 소스
labels/                     정규화된 사례·파일·위치 라벨(JSONL)
scripts/                    데이터 추출, 확인, SARIF 평가
docker/                     격리된 분석 환경과 실행 명령
results/                    사례별 SARIF 및 점수
```

`bash scripts/rebuild_labels.sh`는 내려받은 원본에서 라벨과 실행용 파일을 다시 생성합니다. 출처와 원본 해시는 [data/PROVENANCE.md](data/PROVENANCE.md)에 기록했습니다.

## 라벨을 읽는 방법

- **CASTLE:** `ground_truth=positive/negative`와 `upstream_exact_line`은 원본의 직접 라벨입니다. 100개 비취약 파일이 있어 경보 발생 비율을 계산할 수 있습니다.
- **ReposVul:** `target=1`인 C/C++ 파일만 양성으로 사용합니다. `code_before`를 수정 전 파일로 저장했고, 파일 경로는 원본의 `file_name`을 사용합니다. `line_candidates`는 패치의 수정 전 줄이 `code_before`와 맞을 때만 채웁니다. 후보 줄은 검증된 취약 지점 자체와 동의어가 아닙니다. `target=0/-1`이나 빠진 파일을 비취약 정답으로 취급하지 않습니다.
- ReposVul의 729건은 **파일 단위 사례 수**입니다. 같은 CVE나 같은 프로젝트의 여러 파일이 별도 사례일 수 있어 고유 CVE 수로 읽지 않습니다.
- **SEC-bench-Pro:** `target_source_files`는 원본이 지정한 대상 파일입니다. `line_candidates`는 수정 패치에서 계산한 후보 위치이며, 344개 전체에 대해 실제 취약 체크아웃과의 일치를 검증한 값은 아닙니다. 준비된 Linux 사례는 패치 삭제 줄이 소스와 맞는지 확인했습니다. 준비된 V8 사례는 패치와 취약 체크아웃의 위치가 맞지 않아 **파일 라벨만** 사용합니다.

`evaluate_sarif.py`의 CASTLE 점수는 직접 줄 라벨과 비취약 파일을 사용합니다. ReposVul·SEC 점수는 대상 파일 탐지와 패치 후보 위치 탐지입니다. 이 두 벤치마크에는 완전한 비취약 라벨이 없으므로 전체 프로젝트에서 정밀도를 계산하지 않습니다.

이 SARIF 대조는 원저자의 공식 CASTLE Score가 아닙니다. 기본 점수는 경보의 CWE 적합성을 판정하지 않으며, 비취약 파일의 경보 수를 별도로 보여 줍니다. 아래 CASTLE 표의 보수적 탐지 수는 별도로 경고 내용과 원본 코드를 대조했습니다.

## Cppcheck·Clang Static Analyzer 평가 결과

2026-10-11, 위 Docker 환경에서 **현재 내려받은 소스**를 대상으로 실행했습니다. 표의 시간은 컨테이너 안에서 사례별 분석 명령에 걸린 시간을 합한 값이며 Docker 시작·점수 계산 시간은 제외합니다. 버전은 Cppcheck 2.13.0, Clang 18.1.3입니다. Cppcheck는 `--enable=warning`으로 실행했고 Clang은 기본 정적분석 체크를 사용했습니다. 두 도구의 경고 범위가 같다고 가정하지 않습니다.

| 벤치마크 | Cppcheck | Clang Static Analyzer |
|---|---|---|
| **CASTLE C250** | **취약 18/150** (경고 내용까지 확인), 원본 줄 일치 23/150; **안전 100/100 무경보**. 250/250 분석, **1.772초**. | **취약 16/150** (경고 내용까지 확인), 원본 줄 일치 17/150; **안전 95/100 무경보** (5건 경보). 250/250 분석, **6.835초**. |
| **ReposVul** | 정상 해석 556/729 취약 파일 중 대상 파일 경보 **130/556**. 패치 후보가 있는 정상 해석 457건 중 줄 일치 **18/457**, 경고 내용이 취약 유형과 부합하는 사례 **11/457**. 나머지 173건은 매크로·구문 해석 오류로 불완전. 안전 라벨 없음. 729건 실행 시도, **516.315초**. | 컴파일 완료 16/729 취약 파일 중 대상 파일 경보 **2/16**, 패치 후보 줄 일치 **0/13**. 713건은 헤더·빌드 설정 부족 등으로 컴파일 실패. 안전 라벨 없음. 729건 실행 시도, **17.123초**. |
| **SEC-bench-Pro** | 전체 344건 중 취약 소스가 준비된 **2건**의 대상 파일 분석: 대상 파일 경보 **1/2**, 확인된 패치 줄 탐지 **0/1**. 안전 라벨 없음. **0.259초**. V8 전체 소스는 대상 파일 경보 **0/1**, **2,037.131초**. Linux 전체 소스는 **1,200.035초 후 시간 초과**. | 소스 준비 2/344건의 대상 파일을 시도했으나 **0/2 컴파일 완료**. 취약 지점 탐지율·안전 판정 불가. **1.484초**(실패한 시도 포함). |

**취약 탐지의 뜻:** CASTLE의 18건과 16건은 원본이 지정한 줄에 경고가 있고 경고 내용도 해당 취약점과 맞는지 코드를 보며 보수적으로 확인한 수입니다. 같은 줄이지만 다른 문제를 지적한 Cppcheck 5건과 Clang 1건은 제외했습니다. 제외 사례와 이유는 [`results/castle-line-review.json`](results/castle-line-review.json)에 있습니다. 안전 수는 원본이 비취약으로 표시한 파일에 경고가 **하나도 없는** 사례 수입니다. 경고 5건을 수작업으로 실제 오탐이라고 확정한 수는 아닙니다.

Clang이 CASTLE의 안전 파일 5개에 낸 경고 중 3개는 사용하지 않는 값 저장(`deadcode.DeadStores`), 1개는 초기화되지 않은 인수, 1개는 메모리 누수 경고입니다. 따라서 95/100은 **모든 경고**를 기준으로 한 무경보 수이고, 보안 관련 경고만 보면 98/100에 경고가 없습니다. 뒤의 두 경고가 진짜 결함인지까지는 이 벤치마크의 안전 라벨만으로 확정할 수 없습니다.

**ReposVul의 11/457도 해당 CVE의 정확한 원인을 찾았다는 확정 수가 아닙니다.** 라벨은 수정 패치의 삭제 줄에서 유도한 후보입니다. 18건의 줄 일치 사례를 경고 메시지·코드·원본 CWE와 다시 대조해 11건만 취약 유형에 부합한다고 보수적으로 판단했습니다. 판정 내역은 [`results/reposvul-line-review.json`](results/reposvul-line-review.json)에 있습니다. Cppcheck의 `unknownMacro`, `syntaxError`, `internalAstError`, `preprocessorErrorDirective`는 취약점 경고에서 제외했습니다. 이 필터를 적용하지 않으면 대상 파일 경보 302/729, 후보 줄 일치 29/606으로 부풀어 오릅니다. 두 점수 파일은 `results/docker-cppcheck-reposvul-files-filtered-score.*`와 `results/docker-cppcheck-reposvul-files-score.*`에 각각 남겼습니다. ReposVul에는 신뢰할 수 있는 안전 파일 라벨이 없어 오탐 비율을 계산할 수 없습니다.

Clang의 ReposVul 실행 시간 17.123초에는 713건의 조기 컴파일 실패가 포함됩니다. 이를 729개 파일의 정상 분석 속도로 비교할 수 없습니다. Clang이 완료한 16건의 대상 파일 경고 2건도 패치 후보 줄과 일치하지 않았습니다.

ReposVul의 **전체 프로젝트 스냅샷 2개**도 Cppcheck로 별도 분석했습니다. 대상 파일에는 둘 다 경고가 있었지만 패치 후보 줄과 맞는 경고는 0/2였고, 분석 시간은 **146.118초**였습니다. Clang은 두 프로젝트의 **대상 파일**을 빌드 맥락을 추가해 2/2 분석했습니다. 두 파일 모두 경고가 있었지만 모두 사용하지 않는 값 저장(`deadcode.DeadStores`)이며 패치 후보 줄과 맞는 경고는 **0/2**, 분석 시간 합은 **4.741초**였습니다. Exiv2는 CMake가 생성한 실제 컴파일 설정을 사용했고, `file`은 원본 버전 5.16의 `magic.h` 템플릿으로 만든 헤더와 Linux 기능 매크로를 사용했습니다. 원본 소스는 수정하지 않았습니다. Clang의 두 실행은 프로젝트 전체 스캔이 아니므로 Cppcheck의 전체 프로젝트 시간과 직접 비교하지 않습니다. 이 두 사례는 위 729개 파일 사례와 중복되는 CVE이므로 분모에 더하지 않았습니다.

SEC Linux 대상 파일의 유일한 Cppcheck 경고는 `fs/fs_context.c:388`이고, 확인된 패치 줄은 **551**이어서 탐지로 세지 않았습니다. Linux **전체 소스** Cppcheck 분석은 1,200초 제한에 걸려 SARIF가 완성되지 않았습니다. 실패 기록과 정확한 소요 시간은 `results/docker-cppcheck-linux/`에 있습니다. V8 대상 파일에는 경고가 없습니다. 제한 없이 다시 마친 V8 전체 소스 분석은 **2,037.131초**가 걸렸고, 이전 완료 결과와 SARIF 해시가 완전히 일치했습니다. Cppcheck 진단 1,063건 중 735건은 매크로·구문·전처리 진단입니다. 이를 제외한 경고 328건에도 대상 파일 경고는 0건입니다. 해시와 시간 검증은 [`results/v8-run-verification.json`](results/v8-run-verification.json)에 남겼고, 이전 시간 초과 기록은 `results/docker-cppcheck-v8/previous-timeout-1200s/`에 있습니다. SEC의 나머지 **342건은 사례별 취약 소스가 없어 실행할 수 없으며**, 두 준비 사례에도 안전 라벨은 없습니다.

사례별 SARIF, 실패 이유, 시간(`timings.json`), 점수 JSON·CSV는 `results/`에 보관합니다. Cppcheck의 도구 자체 진단을 빼고 다시 점수화하려면 다음과 같이 실행합니다.

```bash
python3 scripts/evaluate_sarif.py --manifest labels/reposvul-files.jsonl \
  --results results/docker-cppcheck-reposvul-files \
  --output results/docker-cppcheck-reposvul-files-filtered-score \
  --exclude-rule unknownMacro --exclude-rule syntaxError \
  --exclude-rule internalAstError --exclude-rule preprocessorErrorDirective
```

## 현재 범위와 실행 환경

ReposVul C/C++ 원본은 모두 다운로드했고, 양성 취약 파일 729개를 바로 분석할 수 있습니다. 전체 프로젝트 스냅샷은 `file/file`과 `Exiv2/exiv2`의 수정 전 커밋을 준비했으며, 두 소스의 대상 파일이 원본 `code_before`와 바이트 단위로 일치함을 확인했습니다.

SEC-bench-Pro는 344개 사례의 메타데이터와 라벨을 모두 준비했습니다. 전체 소스 스냅샷은 Linux `CVE-2022-0185`와 V8 `472139305` 두 건입니다. 다른 342건은 사례마다 다른 대형 소스 버전 또는 Docker 이미지가 필요하므로 `labels/sec-bench-pro.jsonl`에만 수록했습니다. 이 저장소의 원래 PoC·수정 검증 하네스는 여기서 실행하지 않았습니다.

현재 Docker는 Apple Silicon 위의 Linux ARM64입니다. 컨테이너에서 `/dev/kvm`이 없음을 확인했습니다. SEC의 Linux PoC 채점은 공식 문서상 x86-64 Linux와 KVM이 필요하므로 이 환경에서 동일하게 재현할 수 없습니다. 여기서 제공하는 Docker 실행은 **소스 정적분석 평가**입니다.

CASTLE 원본은 수정하지 않았습니다. 최신 Clang에서 250개 전부를 분석하기 위해 Docker 이미지에 MySQL·OpenSSL·SQLite·cURL 개발 헤더를 넣고, 원본 코드 일부의 형 변환 및 선언 누락을 오류로 중단하지 않도록 Clang 옵션 두 개를 사용합니다. 이 옵션은 분석 결과 해석 시 함께 기록해야 합니다.
