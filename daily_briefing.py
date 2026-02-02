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
import datetime
import requests
from get_my_calendar_today import get_calendar_service, AINR_CAL, DATONR_CAL
from weather import get_today_weather
from todayinfo import is_day_off, get_upcoming_special_days
from useless_fact import UselessFact
from ain_slack import AinSlack

# Ollama 설정
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "exaone3.5:32b"


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


def generate_briefing(date: str, events: list, weather: str, special_days: list, fact: str) -> str:
    """
    Ollama를 통해 브리핑 문구 생성
    Args:
        date: 오늘 날짜 문자열
        events: 일정 리스트
        weather: 날씨 정보 문자열
        special_days: 특일 정보 리스트
        fact: useless fact 문자열
    Returns:
        브리핑 문구
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
        special_text = "오늘~내일 중 특별한 날이 없습니다."

    prompt = f"""당신은 친근한 비서입니다. 다음 정보를 바탕으로 아침 브리핑 메시지를 작성해주세요.

오늘 날짜: {date}

오늘의 날씨:
{weather}

오늘의 일정:
{events_text}

특일 정보:
{special_text}

오늘의 잡학사실 (영어):
{fact}

다음 형식으로 작성해주세요:
인사말 (날짜 포함)
오늘의 날씨 요약 (기온, 날씨 상태 간단히)
오늘의 일정 요약(오늘의 일정중에 00:00으로 된 시간은 종일 일정으로 언급하기)
특일정보가 있으면 간단히 언급하고, 없으면 아무런 코멘트 금지
잡학사실을 한국어로 번역하고 재미있게 소개
마무리 인사

짧고 간결하게 작성하되, 밝고 긍정적인 톤으로 작성해주세요. 포매팅에 **은 사용하지 말아주세요."""

    ollama_request = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
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
    return result.get("response", "").strip()


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
    date_str = today.strftime("%Y년 %m월 %d일 %A")
    print(f"날짜: {date_str}")

    # 2. 쉬는 날 체크
    print("\n쉬는 날 여부 확인 중...")
    is_off, reason = is_day_off()
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

    # 5. 특일 정보 조회
    print("\n특일 정보 조회 중...")
    try:
        special_days = get_upcoming_special_days(2)
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

    # 8. Ollama 브리핑 생성
    print("\n브리핑 생성 중...")
    try:
        briefing = generate_briefing(date_str, events, weather, special_days, fact)
        print(f"\n--- 브리핑 내용 ---\n{briefing}\n-------------------")
    except Exception as e:
        print(f"브리핑 생성 실패: {e}")
        return

    # 9. Slack 전송
    print("\nSlack 전송 중...")
    try:
        if args.prod:
            slack = AinSlack("/home/scchae/work/chae/tools/slack_credential_service.json")
            print("(실행 모드)")
        else:
            slack = AinSlack("/home/scchae/work/chae/tools/slack_credential_test.json")
            print("(테스트 모드)")
        thread_id = slack.send_message(briefing)
        if thread_id:
            print(f"전송 완료! Thread ID: {thread_id}")
        else:
            print("전송 실패!")
    except Exception as e:
        print(f"Slack 전송 실패: {e}")


if __name__ == "__main__":
    main()
