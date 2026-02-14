# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains utility tools and API clients for internal use. Scripts are standalone Python utilities without a unified build system.

## Project Structure

```
tools/
├── daily_briefing.py          # 메인 스크립트 (엔트리포인트)
├── .env                       # 환경변수 (dotenv)
├── credential/                # 인증 파일 (gitignored)
│   ├── slack_credential_service.json
│   ├── slack_credential_test.json
│   └── token.json
├── util/                      # 유틸리티 모듈 패키지
│   ├── ain_slack.py           # Slack 메시징 래퍼
│   ├── weather.py             # 기상청 날씨 조회
│   ├── todayinfo.py           # 공휴일/특일 정보
│   ├── get_my_calendar_today.py  # Google Calendar 연동
│   ├── useless_fact.py        # Useless Fact API
│   ├── api_ninja.py           # API Ninja 클라이언트
│   └── joke_api.py            # Joke API 클라이언트
├── data/                      # 데이터 파일
│   └── kma_forecast_grid_coordinates.csv
├── template/                  # 템플릿 파일
│   └── py_template.py
└── get_tigris_put_gcalendar/  # Tigris→Google Calendar 동기화
    └── get_tigris_and_put_team_cal.py
```

## Running Scripts

Scripts are run directly with Python:
```bash
python daily_briefing.py          # 메인 브리핑 (테스트 모드)
python daily_briefing.py -p       # 메인 브리핑 (프로덕션 모드)
```

## Architecture

### API Client Pattern

API clients follow a consistent class-based pattern:
- `ApiNinjaBase` (util/api_ninja.py): Abstract base class with `_request()` method and `endpoint` property
- Subclasses implement `endpoint` property and `get()` method
- Example clients: `ApiNinjaFacts`, `JokeApi`, `UselessFact`

### Credential Loading

Two patterns are used:
1. **JSON credential file**: Load via constructor path parameter (e.g., `AinSlack("credential/slack_credential.json")`)
2. **Environment variables**: Load via python-dotenv (e.g., `API_NINJA_KEY` in `.env`)

### Main Function Convention

All scripts include a `main()` function that serves dual purpose:
1. Prints usage examples showing how to instantiate and use the class
2. Runs a simple test/demo of the functionality

### Key Components

- `util/ain_slack.py`: Slack messaging wrapper using slack_sdk
- `util/get_my_calendar_today.py`: Google Calendar integration using OAuth tokens
- `util/weather.py`: 기상청 초단기예보 API 클라이언트
- `util/todayinfo.py`: 공공데이터 특일정보 API 클라이언트

## Dependencies

Required packages (install as needed):
- `slack_sdk` - Slack API
- `python-dotenv` - Environment variable loading
- `requests` - HTTP client
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` - Google Calendar
- `fastapi`, `uvicorn` - Meeting recorder server
- `whisper` - Speech recognition
- `pytz` - Timezone handling
- `arrow` - Date/time utilities

## Custom Slash Command

`/py-class` - Generates a Python class file from a template with credential loading pattern and main() test function
