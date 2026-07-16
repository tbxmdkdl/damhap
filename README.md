# 담합의 탑

전략기획·전략투자·브랜드성장 조직을 위한 Streamlit 기반 담합 컴플라이언스 게임입니다. 본편은 5층, 층당 3개 장면으로 진행되며, 각 장면은 1차 판단(80·60·40·0점)과 후속 조치(20·10·0점)의 2단계 선택으로 구성됩니다. 본편 점수와 플레이 시간을 기록하며, 본편 종료 후에는 별도 번외인 `마왕에게 도전` 모드를 플레이할 수 있습니다.

## 실행

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

로컬 실행 주소는 보통 `http://localhost:8501`입니다.

## Google Sheets 기록 연결

1. Google Cloud에서 서비스 계정을 만들고 Google Sheets API를 사용 설정합니다.
2. 기록을 받을 Google Sheet를 만들고 첫 번째 워크시트 이름을 `results`로 바꿉니다.
3. 해당 시트를 서비스 계정 이메일에 **편집자** 권한으로 공유합니다.
4. `.streamlit/secrets.toml.example`을 복사해 `.streamlit/secrets.toml`로 이름을 바꿉니다.
5. `spreadsheet_id`와 서비스 계정 JSON의 값을 채웁니다.
6. `results` 워크시트 첫 행에 아래 헤더를 붙여 넣습니다.

```text
제출시각 | 기록코드 | 이름 | 부서 | 본편점수 | 본편시간초 | 번외점수 | 번외연속통과 | 번외도전횟수 | 본편위험사용 | 본편위험성공 | 선택요약
```

`secrets.toml`은 `.gitignore`에 포함되어 있어 공개 저장소에 올라가지 않습니다. Streamlit Community Cloud로 배포할 때는 이 파일 내용을 앱 설정의 Secrets에 그대로 등록합니다.

## 순위 기준

- 본편: 본편 점수 내림차순, 동점이면 본편 시간 오름차순
- 번외: 번외 점수 내림차순, 동점이면 연속 통과 횟수 내림차순

참가자 식별은 이름과 부서만 사용합니다. 공개 링크 환경에서는 별도 로그인이나 중복 제출 방지가 없으므로, 운영 시에는 동일 이름의 중복 기록을 시트에서 정리하거나 사내 계정 인증이 가능한 배포 환경을 사용하세요.

`results`와 별도로 `leaderboard` 워크시트를 만들면 아래 수식으로 운영용 순위를 바로 볼 수 있습니다. 첫 번째 수식은 본편 순위, 두 번째 수식은 번외 순위입니다.

```text
=SORT(FILTER({results!C2:C,results!D2:D,results!E2:E,results!F2:F},results!C2:C<>""),3,FALSE,4,TRUE)
=SORT(FILTER({results!C2:C,results!D2:D,results!G2:G,results!H2:H},results!C2:C<>""),3,FALSE,4,FALSE)
```

## 이미지 적용

이미지가 없어도 앱은 실행됩니다. 아래 PNG를 `assets/`에 넣으면 빈 스프라이트 자리에 자동 적용됩니다.

```text
assets/
  tower_intro.png
  battle_bg_floor_1.png
  battle_bg_floor_2.png
  battle_bg_floor_3.png
  battle_bg_floor_4.png
  battle_bg_floor_5.png
  hero_male_back.png
  hero_male_front_sword.png
  hero_male_sword_rejected.png
  parchment_scroll.png
  enemy_floor_1.png
  enemy_floor_2.png
  enemy_floor_3.png
  enemy_floor_4.png
  enemy_floor_5.png
```

권장 규격은 아래와 같습니다.

| 파일 | 권장 비율 | 권장 해상도 | 배경 |
| --- | --- | --- | --- |
| `tower_intro.png` | 16:9 | 1280x720 | 불투명 |
| `battle_bg_floor_*.png` | 16:9 | 1280x720 이상 | 불투명 PNG |
| `hero_male_back.png` | 1:1 | 512x512 이상 | 투명 PNG |
| `hero_male_front_sword.png` | 1:1 | 512x512 이상 | 투명 PNG |
| `hero_male_sword_rejected.png` | 1:1 | 512x512 이상 | 투명 PNG |
| `parchment_scroll.png` | 4:5 내외 | 1024x1280 이상 | 투명 PNG |
| `enemy_floor_*.png` | 1:1 | 512x512 | 투명 PNG |

생성 이미지 파일은 업로드 전 실제 PNG인지 확인하고, 파일명과 확장자를 위 구조에 맞춰 넣으면 됩니다.

