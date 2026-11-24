# harness-lab

세 권의 wikidocs 책(Claude Code Howto, Reason Network 해부, 하네스 엔지니어링)을 우리 저장소에 적용해 보는 실습 폴더.
단계마다 폴더 하나, 측정 스크립트 하나, README 하나를 둔다.

## 목적
"AI를 잘 쓰는 법"을 감이 아니라 숫자로 확인한다. 각 단계는 같은 질문에 답한다.
- 무엇을 바꾸는가 (변경안)
- 무엇과 비교하는가 (기준선)
- 무엇이 얼마나 달라지는가 (토큰, 비용, 정확도)

## 단계
| 단계 | 폴더 | 주제 | 상태 |
|---|---|---|---|
| 1 | `01-instructions/` | 지시 설계: 입구 파일과 규칙 분리 | 완료 |
| 2 | `02-...` | 이후 단계는 학습서 로드맵 순서대로 추가 | 예정 |

## 실행 준비
```
python --version        # 3.11 이상
pip install ruff        # 린트/포맷
pip install anthropic   # --counter claude 를 쓸 때만 필요
```
API 키가 필요한 옵션은 `ANTHROPIC_API_KEY` 환경 변수에서만 읽는다. 키를 파일에 쓰지 않는다.
