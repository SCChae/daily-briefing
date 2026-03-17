"""
Daily Briefing 생성기
- Google Calendar 일정 조회
- 날씨 정보 조회
- 특일 정보 조회
- Useless Fact 조회
- Ollama를 통한 브리핑 문구 생성
- Slack 채널로 전송
"""

import argparse
import calendar
import datetime
import json
import requests
import arrow
from util.get_my_calendar_today import get_calendar_service, AINR_CAL, DATONR_CAL
from util.weather import get_today_weather
from util.air_quality import get_air_quality
from util.todayinfo import is_day_off, get_upcoming_special_days
from util.useless_fact import UselessFact
from util.ain_slack import AinSlack
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SLACK_CREDENTIAL_SERVICE = os.path.join(BASE_DIR, "credential", "slack_credential_service.json")
SLACK_CREDENTIAL_TEST = os.path.join(BASE_DIR, "credential", "slack_credential_test.json")

# Ollama 설정
OLLAMA_URL = "http://localhost:11434"
#OLLAMA_MODEL = "exaone3.5:32b"
OLLAMA_MODEL = "qwen3.5:27b"


def get_date_position(date: datetime.date = None) -> str:
    """
    날짜의 연간/월간 위치 정보를 문자열로 반환
    Args:
        date: 날짜 (기본값: 오늘)
    Returns:
        "오늘은 2026년의 x번째주, xx번째 날, 올해가 xx%지났고, 이번달은 xx% 지났습니다."
    """
    if date is None:
        KST = datetime.timezone(datetime.timedelta(hours=9))
        date = datetime.datetime.now(KST).date()

    # 올해의 몇 번째 주 (ISO week number)
    week_number = date.isocalendar()[1]

    # 올해의 몇 번째 날
    day_of_year = date.timetuple().tm_yday

    # 올해가 몇 % 지났는지
    year = date.year
    days_in_year = 366 if calendar.isleap(year) else 365
    year_progress = (day_of_year / days_in_year) * 100

    # 이번 달이 몇 % 지났는지
    days_in_month = calendar.monthrange(year, date.month)[1]
    month_progress = (date.day / days_in_month) * 100

    return (
        f"오늘은 {year}년의 {week_number}번째주, "
        f"올해가 {year_progress:.1f}% 지났습니다."
    )


def get_todays_events(service, calendar_id: str) -> list:
    """
    오늘의 캘린더 일정 조회
    Args:
        service: Google Calendar 서비스 객체
        calendar_id: 캘린더 ID
    Returns:
        일정 리스트 [{"summary": "...", "start_time": "..."}]
    """
    KST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(KST).date()

    start_of_day = datetime.datetime.combine(today, datetime.datetime.min.time())
    end_of_day = datetime.datetime.combine(today, datetime.datetime.max.time())

    start_of_day = start_of_day.replace(tzinfo=KST)
    end_of_day = end_of_day.replace(tzinfo=KST)

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    result = []

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        dt = datetime.datetime.fromisoformat(start)
        start_str = dt.strftime("%H:%M")
        result.append({
            "summary": event["summary"],
            "start_time": start_str
        })

    return result


def generate_briefing_json(date: str, events: list, weather: str, special_days: list, fact: str, date_position: str = "", air_quality: str = "") -> dict:
    """
    Ollama를 통해 JSON 형식의 브리핑 생성
    Args:
        date: 오늘 날짜 문자열
        events: 일정 리스트
        weather: 날씨 정보 문자열
        special_days: 특일 정보 리스트
        fact: useless fact 문자열
        date_position: 날짜 위치 정보 문자열
        air_quality: 공기질 정보 문자열
    Returns:
        브리핑 JSON dict
    """
    # 일정 포맷팅
    if events:
        events_text = "\n".join([f"- {e['start_time']} {e['summary']}" for e in events])
    else:
        events_text = "오늘은 일정이 없습니다."

    # 특일 정보 포맷팅
    type_names = {'holiday': '공휴일', 'division': '24절기', 'sundry': '잡절'}
    if special_days:
        special_text = "\n".join([
            f"- {day['date']}: {day['name']} ({type_names.get(day['type'], day['type'])})"
            for day in special_days
        ])
    else:
        special_text = ""

    prompt = f"""당신은 친근한 비서입니다. 다음 정보를 바탕으로 아침 브리핑 내용을 JSON 형식으로 작성해주세요.

오늘 날짜: {date}

날짜 위치 정보:
{date_position}

오늘의 날씨:
{weather}

오늘의 공기질:
{air_quality if air_quality else "공기질 정보 없음"}

오늘의 일정:
{events_text}

특일 정보:
{special_text if special_text else "없음"}

오늘의 잡학사실 (영어):
{fact}

다음 JSON 형식으로 작성해주세요. 반드시 유효한 JSON만 출력하세요:
{{
  "greeting": "아침 인사말 (3-4문장). 날짜와 요일을 자연스럽게 언급하고, 날씨/일정/특일 등 오늘의 전체 맥락을 고려해서 연구원들에게 힘이 나고 유머러스한 인사말을 작성. 월요일이면 주말 끝 위로, 금요일이면 불금 언급, 날씨가 좋으면 기분 좋은 멘트, 일정이 많으면 파이팅 멘트 등 상황에 맞게 재치있게. **은 절대 사용하지 말 것.",
  "weather": "날씨 요약 (최저, 최고 기온, 날씨 상태 간단히, 1-2문장)",
  "schedule": "일정 브리핑 (00:00은 종일 일정으로 언급, 중복일정이 있으면 한번만 언급, 연구원들 재택근무는 정확히 팀과 이름을 언급)",
  "special_day": "특일 정보가 있으면 간단히 언급, 없으면 special_day 항목을 생성하지 않음",
  "fact": "반드시 한국어로만 작성. 영어 원문을 한국어로 번역한 내용 + 재미있는 코멘트 (2-3문장). 영어를 절대 포함하지 말 것. 잡학사실 내용이 성적이거나 불쾌감을 유발하면 항목을 생성하지 않음",
  "closing": "마무리 인사(날짜 포함, 날씨와 요일을 고려해서 연구활동을 독려하는 적절한 1문장)"
}}

짧고 간결하게, 밝고 긍정적인 톤으로 작성해주세요.

참고: 일정에 다음과 같은 이름이 있으면 소속과 직책을 확인해서 보정해줘.

이세라 AI 솔루션개발팀/팀장
이승민 AI 솔루션개발팀/주임연구원
정종찬 AI 솔루션개발팀/주임연구원
강진형 AI 솔루션개발팀/연구원
최호진 기반기술실/실장 
문영민 기반기술실/파트장
김규태 AI 비전솔루션팀/팀장
이재익 AI 비전솔루션팀/주임
김서영 AI 비전솔루션팀/연구원
김지우 AI 비전솔루션팀/연구원
유승호 AI 비전솔루션팀/연구원
최민혁 AI 비전솔루션팀/연구원
채승철 산업지능연구소/소장

팀이름은 줄임말도 정식명칭으로 해줘
솔개팀--> AI솔루션개발팀
비솔팀--> AI비전솔루션팀


"""

    ollama_request = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000
        }
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=ollama_request,
        timeout=120
    )
    response.raise_for_status()

    result = response.json()
    response_text = result.get("response", "").strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # JSON 파싱 실패시 기본 구조 반환
        return {
            "greeting": f"안녕하세요! {date}입니다.",
            "weather": weather,
            "schedule": events_text,
            "special_day": special_text if special_text else None,
            "fact": fact,
            "closing": "좋은 하루 보내세요!"
        }


def build_slack_blocks(date: str, briefing: dict, date_position: str = "", air_quality: str = "", original_fact: str = "") -> list:
    """
    브리핑 JSON을 Slack Block Kit 형식으로 변환
    Args:
        date: 오늘 날짜 문자열
        briefing: 브리핑 JSON dict
        date_position: 날짜 위치 정보 문자열
        air_quality: 공기질 정보 문자열
        original_fact: 잡학사실 영문 원문
    Returns:
        Slack Block Kit 블록 리스트
    """
    blocks = []

    # 헤더
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"📅 {date} 오늘의 브리핑",
            "emoji": True
        }
    })

    # 인사말 + 날짜 위치
    greeting_text = f"👋 {briefing.get('greeting', '')}"
    if date_position:
        greeting_text += f"\n_{date_position}_"
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": greeting_text
        }
    })

    # 날씨 + 공기질
    weather_text = briefing.get('weather', '')
    if air_quality:
        weather_text += f"\n{air_quality}"
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": weather_text
        }
    })


    # 일정
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*📆 오늘의 일정*\n{briefing.get('schedule', '')}"
        }
    })

    # 특일 정보 (있는 경우에만)
    special_day = briefing.get('special_day')
    if special_day:
#        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🎉 오늘은..? *\n{special_day}"
            }
        })

    blocks.append({"type": "divider"})

    # 잡학사실
    fact_text = f"*💡 오늘의 잡학사실*\n{briefing.get('fact', '')}"
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": fact_text
        }
    })

    blocks.append({"type": "divider"})

    # 마무리 인사 (context block)
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"✨ {briefing.get('closing', '')}"
            }
        ]
    })

    return blocks


def main():
    """Daily Briefing 실행"""
    # 인자 파싱
    parser = argparse.ArgumentParser(description='Daily Briefing 생성기')
    parser.add_argument('-p', '--prod', action='store_true',
                        help='실행 모드 (기본: 테스트 모드)')
    args = parser.parse_args()

    print("=== Daily Briefing 생성 시작 ===\n")

    # 1. 오늘 날짜
    KST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(KST)
#    today = datetime.datetime.now(KST) + datetime.timedelta(days=1)
    date_str = today.strftime("%Y년 %m월 %d일 %A")
    print(f"날짜: {date_str}")

    # 2. 쉬는 날 체크
    print("\n쉬는 날 여부 확인 중...")
    is_off, reason = is_day_off(arrow.get(today))
    if is_off:
        print(f"오늘은 쉬는 날입니다: {reason}")
        print("브리핑을 생성하지 않고 종료합니다.")
        return

    # 3. Google Calendar 일정 조회
    print("\n캘린더 일정 조회 중...")
    try:
        service = get_calendar_service()
        events = get_todays_events(service, AINR_CAL)
        events += get_todays_events(service, DATONR_CAL)
        events.sort(key=lambda e: e['start_time'])
        print(f"일정 {len(events)}개 조회됨")
        for e in events:
            print(f"  - {e['start_time']} {e['summary']}")
    except Exception as e:
        print(f"캘린더 조회 실패: {e}")
        events = []

    # 4. 날씨 정보 조회
    print("\n날씨 정보 조회 중...")
    try:
        weather = get_today_weather()
        print(weather)
    except Exception as e:
        print(f"날씨 조회 실패: {e}")
        weather = "날씨 정보를 가져오지 못했습니다."

    # 4-1. 공기질 정보 조회
    print("\n공기질 정보 조회 중...")
    try:
        air_quality = get_air_quality()
        print(air_quality)
    except Exception as e:
        print(f"공기질 조회 실패: {e}")
        air_quality = "공기질 정보를 가져오지 못했습니다."

    # 5. 특일 정보 조회
    print("\n특일 정보 조회 중...")
    try:
        special_days = get_upcoming_special_days(1)
        type_names = {'holiday': '공휴일', 'division': '24절기', 'sundry': '잡절'}
        if special_days:
            for day in special_days:
                type_name = type_names.get(day['type'], day['type'])
                print(f"  - {day['date']}: {day['name']} ({type_name})")
        else:
            print("  특일 정보 없음")
    except Exception as e:
        print(f"특일 정보 조회 실패: {e}")
        special_days = []

    # 7. Useless Fact 조회
    print("\nUseless Fact 조회 중...")
    try:
        fact_api = UselessFact(language="en")
        fact_data = fact_api.get_random()
        fact = fact_data["text"]
        print(f"Fact: {fact}")
    except Exception as e:
        print(f"Fact 조회 실패: {e}")
        fact = "No fact available today."

    # 8. 날짜 위치 정보 생성
    date_position = get_date_position(today.date())
    print(f"\n날짜 위치: {date_position}")

    # 9. Ollama 브리핑 생성 (JSON 형식)
    print("\n브리핑 생성 중...")
    try:
        briefing = generate_briefing_json(date_str, events, weather, special_days, fact, date_position, air_quality)
        print(f"\n--- 브리핑 내용 (JSON) ---")
        print(json.dumps(briefing, ensure_ascii=False, indent=2))
        print("-------------------")
    except Exception as e:
        print(f"브리핑 생성 실패: {e}")
        return

    # 10. Block Kit 변환
    print("\nBlock Kit 변환 중...")
    blocks = build_slack_blocks(date_str, briefing, date_position, air_quality, fact)

    # fallback text 생성
    fallback_text = f"{briefing.get('greeting', '')} {briefing.get('weather', '')} {briefing.get('schedule', '')} {briefing.get('closing', '')}"

    # 11. Slack 전송
    print("\nSlack 전송 중...")
    try:
        if args.prod:
            slack = AinSlack(SLACK_CREDENTIAL_SERVICE)
            print("(실행 모드)")
        else:
            slack = AinSlack(SLACK_CREDENTIAL_TEST)
            print("(테스트 모드)")
        thread_id = slack.send_message(fallback_text, blocks=blocks)
        if thread_id:
            print(f"전송 완료! Thread ID: {thread_id}")
        else:
            print("전송 실패!")
    except Exception as e:
        print(f"Slack 전송 실패: {e}")


if __name__ == "__main__":
    main()
