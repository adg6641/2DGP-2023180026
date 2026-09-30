# Drill #8 애니메이션 뷰어

AI로 생성한 픽셀 아트 검사의 걷기 → 달리기 → 점프 → 공격을 보여주는 pico2d 프로그램입니다.
각 동작을 정확히 5회 재생한 뒤 마지막 프레임에서 1초 정지하고 다음 동작으로 넘어갑니다.
공격 다음에는 걷기로 돌아가며 종료할 때까지 반복합니다.

## 실행

Python 3.10 이상과 pico2d 1.5.1 이상을 사용합니다. 현재 작업 PC의 Python 3.13 / pico2d 1.5.1에서 검증했습니다.

저장소 최상위에서 실행:

```powershell
python -m pip install -r Labs/LEC08/requirements.txt
python Labs/LEC08/animation_viewer.py
```

`animation_viewer.py`를 VS Code에서 열어 **Run Python File**로 실행해도 됩니다.
이미지와 JSON 경로는 소스 파일 위치를 기준으로 찾으므로 터미널의 현재 폴더에 영향을 받지 않습니다.
화면 글꼴은 Windows의 Consolas를 사용하며, Linux에서는 DejaVu Sans, macOS에서는 Monaco를 찾습니다.

## 채점 조건 구현

| 조건 | 구현 |
|---|---|
| 4종 이상 | 걷기 6프레임, 달리기 8프레임, 점프 7프레임, 공격 5프레임 |
| 중앙 재생 / 확대 | 960×640 창 중앙에서 재생, 각 포즈의 표시 높이 339.2px(화면 높이의 53%) |
| 5회 반복 / 1초 정지 | 동작별 전체 프레임을 5번 재생한 후 마지막 프레임을 1초간 유지 |
| 전체 무한 반복 | 걷기 → 달리기 → 점프 → 공격 → 걷기 순서를 계속 반복 |
| 복잡한 Sprite Sheet | 투명 여백을 잘라 1209×798 atlas에 실제 크기가 다른 26개 프레임을 배치 |
| 동작별 다른 프레임 수 | 각 동작의 독립적인 프레임 목록과 재생 시간을 사용 |
| 파일명 / 폴더 | `Labs/LEC08/animation_viewer.py` |
| 충분한 커밋 | 프로젝트 구성 → 데이터 모델 → 렌더링 → 재생 제어 → UI → 이미지 → 검사 → 문서 순서로 커밋 |

시간표: 걷기 3.60초+정지 1초, 달리기 3.40초+정지 1초, 점프 4.55초+정지 1초,
공격 3.00초+정지 1초입니다. 전체 한 순환은 18.55초입니다.

## 조작

SPACE는 수동 일시정지/재개, R은 전체 재시작, B는 프레임 경계와 확대 배율 표시,
ESC 또는 창 닫기는 종료입니다. 수동 일시정지 중에는 1초 자동 정지의 시간도 흐르지 않습니다.
상단에 동작, 상태, 반복 횟수, 프레임 번호를 표시하고 하단 진행 막대는 5회 재생 전체의 진행률을 나타냅니다.

## 파일

- `animation_viewer.py`: 시간 기반 재생, 메타데이터 로딩/검증, pico2d 화면/입력 처리
- `assets/sprite_atlas.png`: 프로그램에서 직접 사용하는 투명한 가변 크기 스프라이트 시트
- `assets/sprite_atlas.json`: 동작별 프레임 좌표, 크기, 앵커와 점프 높이
- `assets/generated_source.png`: AI가 생성한 32포즈 원본 시트
- `assets/packing_provenance.json`: 각 프레임의 원본 영역과 크롭 좌표
- `build_atlas.py`: 투명 간격을 찾아 포즈를 분리하고 가변 크기 atlas를 재생성하는 개발 도구
- `tests/test_animation_viewer.py`: 채점 조건 중심의 자동 검사
- `submission_explanation.txt`: 제출 시 첨부할 기능 구현 설명
- `ASSET_SOURCE.md`: AI 사용 방식과 최종 이미지 생성 프롬프트

## 검증

```powershell
python -m unittest discover -s Labs/LEC08/tests -v
python Labs/LEC08/animation_viewer.py --validate
python Labs/LEC08/animation_viewer.py --smoke-seconds 20
```

`--screenshot 경로.bmp` 옵션을 함께 주면 실제 렌더링한 첫 화면을 저장합니다.
스프라이트를 다시 패킹할 때만 Pillow가 추가로 필요합니다(`python -m pip install Pillow`, `python Labs/LEC08/build_atlas.py`).
게임 실행에는 Pillow를 사용하지 않습니다.
