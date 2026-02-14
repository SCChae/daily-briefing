# Chae Tools

사내 업무 자동화 도구 모음. Google Calendar 일정, 날씨, 특일 정보를 수집하여 Slack으로 브리핑을 전송하고, Tigris 일정을 Google Calendar에 동기화합니다.

## 폴더 구조

```
tools/
├── daily_briefing.py              # 아침 브리핑 생성 및 Slack 전송
├── get_tigris_and_put_team_cal.py # Tigris 일정 → Google Calendar 동기화
├── .env                           # 환경변수 (API 키 등)
│
├── credential/                    # 인증 파일 (gitignored)
│   ├── slack_credential_service.json  # Slack 프로덕션 토큰
│   ├── slack_credential_test.json     # Slack 테스트 토큰
│   └── token.json                     # Google OAuth 토큰
│
├── util/                          # 유틸리티 모듈 패키지
│   ├── ain_slack.py               # Slack 메시징 래퍼 (slack_sdk)
│   ├── get_my_calendar_today.py   # Google Calendar API 연동
│   ├── weather.py                 # 기상청 초단기예보 조회
│   ├── todayinfo.py               # 공휴일/24절기/잡절 정보 조회
│   ├── useless_fact.py            # Useless Fact API
│   ├── api_ninja.py               # API Ninja 클라이언트 (베이스 클래스)
│   └── joke_api.py                # Joke API 클라이언트
│
├── data/                          # 데이터 파일
│   └── kma_forecast_grid_coordinates.csv  # 기상청 격자 좌표
│
├── template/                      # 템플릿
│   └── py_template.py             # Python 클래스 생성 템플릿
│
└── logs/                          # 로그 디렉토리
    ├── daily_briefing.log
    └── get_tigris.log
```

## 스크립트 설명

### daily_briefing.py

매일 아침 자동 브리핑을 생성하여 Slack 채널에 전송합니다.

**동작 순서:**
1. 오늘이 휴일인지 확인 (휴일이면 종료)
2. Google Calendar에서 오늘 일정 조회
3. 기상청 API로 날씨 정보 조회
4. 공휴일/특일 정보 조회
5. Useless Fact 조회
6. Ollama(exaone3.5:32b)로 브리핑 문구 생성 (JSON)
7. Slack Block Kit 형식으로 변환하여 전송

```bash
python daily_briefing.py        # 테스트 모드 (테스트 채널로 전송)
python daily_briefing.py -p     # 프로덕션 모드 (실제 채널로 전송)
```

### get_tigris_and_put_team_cal.py

Tigris(사내 그룹웨어) 일정을 조회하여 Google Calendar에 동기화합니다. PickleDB를 사용해 이미 동기화된 일정을 추적하므로 중복 등록을 방지합니다.

```bash
python get_tigris_and_put_team_cal.py
```

## 환경 설정

### 필수 패키지

```bash
pip install slack_sdk python-dotenv requests arrow pytz \
    google-auth google-auth-oauthlib google-api-python-client \
    pickledb
```

### 환경변수 (.env)

```
API_NINJA_KEY=<API Ninja 키>
SPECIAL_DAY_API_KEY=<공공데이터 특일정보 API 키>
```

### 인증 파일 (credential/)

| 파일 | 설명 |
|------|------|
| `slack_credential_service.json` | Slack Bot 프로덕션 토큰 (`token`, `channel_id`) |
| `slack_credential_test.json` | Slack Bot 테스트 토큰 |
| `token.json` | Google OAuth2 토큰 (Calendar API용) |

## Crontab 등록

```bash
crontab -e
```

아래 내용을 추가:

```cron
TZ=Asia/Seoul

# 평일 오전 8시 - 아침 브리핑 전송
0 8 * * 1-5 /home/scchae/miniconda3/bin/python /home/scchae/work/chae/tools/daily_briefing.py --prod >> /home/scchae/work/chae/tools/logs/daily_briefing.log 2>&1

# 평일 30분마다 - Tigris → Google Calendar 동기화
*/30 * * * 1-5 cd /home/scchae/work/chae/tools && /home/scchae/miniconda3/bin/python get_tigris_and_put_team_cal.py >> /home/scchae/work/chae/tools/logs/get_tigris.log 2>&1
```

**참고:**
- `TZ=Asia/Seoul` — cron 실행 시간을 한국 시간 기준으로 설정
- Python 절대경로 사용 — cron 환경에서는 conda PATH가 설정되지 않음
- 로그는 `logs/` 디렉토리에 기록됨
