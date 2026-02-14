import requests
import os
import arrow
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

GONGGONG_API_KEY = os.environ.get("GONGGONG_API_KEY", "")

BASE_URL = "https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService"
API_ENDPOINTS = {
    'holiday': '/getRestDeInfo',      # 공휴일 정보
    'division': '/get24DivisionsInfo', # 24절기 정보
    'sundry': '/getSundryDayInfo',     # 잡절 정보
}


def fetch_special_days(year: str, month: str, api_type: str) -> list:
    """
    특정 연월의 특일 정보 조회
    Args:
        year: 연도 (예: '2026')
        month: 월 (예: '01')
        api_type: API 타입 ('holiday', 'division', 'sundry')
    Returns:
        특일 리스트 [{"date": "20260101", "name": "신정", "type": "holiday"}]
    """
    if api_type not in API_ENDPOINTS:
        return []

    url = BASE_URL + API_ENDPOINTS[api_type]
    params = {
        'serviceKey': GONGGONG_API_KEY,
        'solYear': year,
        'solMonth': month,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        # XML 파싱
        root = ET.fromstring(response.content)

        # 응답 확인
        total_count = root.find('.//totalCount')
        if total_count is None or total_count.text == '0':
            return []

        # 특일 항목 추출
        items = []
        for item in root.findall('.//item'):
            locdate = item.find('locdate')
            dateName = item.find('dateName')
            if locdate is not None and dateName is not None:
                items.append({
                    'date': locdate.text,
                    'name': dateName.text,
                    'type': api_type
                })

        return items

    except requests.exceptions.RequestException as err:
        print(f"API 요청 오류: {err}")
        return []
    except ET.ParseError as e:
        print(f"XML 파싱 오류: {e}")
        return []


def fetch_holidays(year: str, month: str) -> list:
    """
    특정 연월의 공휴일 목록 조회 (하위 호환용)
    """
    return fetch_special_days(year, month, 'holiday')


def is_holiday(date: arrow.Arrow = None) -> tuple:
    """
    특정 날짜가 공휴일인지 확인
    Args:
        date: 확인할 날짜 (기본값: 오늘)
    Returns:
        (공휴일 여부, 공휴일명 또는 None)
    """
    if date is None:
        date = arrow.now('Asia/Seoul')

    year = date.format('YYYY')
    month = date.format('MM')
    date_str = date.format('YYYYMMDD')

    holidays = fetch_holidays(year, month)

    for holiday in holidays:
        if holiday['date'] == date_str:
            return True, holiday['name']

    return False, None


def is_weekend(date: arrow.Arrow = None) -> tuple:
    """
    특정 날짜가 주말인지 확인
    Args:
        date: 확인할 날짜 (기본값: 오늘)
    Returns:
        (주말 여부, 요일명)
    """
    if date is None:
        date = arrow.now('Asia/Seoul')

    weekday = date.weekday()  # 0=월, 1=화, ..., 5=토, 6=일
    weekday_names = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']

    if weekday in [5, 6]:
        return True, weekday_names[weekday]

    return False, weekday_names[weekday]


def is_day_off(date: arrow.Arrow = None) -> tuple:
    """
    특정 날짜가 쉬는 날(주말 또는 공휴일)인지 확인
    Args:
        date: 확인할 날짜 (기본값: 오늘)
    Returns:
        (쉬는날 여부, 사유)
    """
    if date is None:
        date = arrow.now('Asia/Seoul')

    # 공휴일 확인
    is_hol, holiday_name = is_holiday(date)
    if is_hol:
        return True, f"공휴일 ({holiday_name})"

    # 주말 확인
    is_wknd, weekday_name = is_weekend(date)
    if is_wknd:
        return True, f"주말 ({weekday_name})"

    return False, None


def get_upcoming_special_days(n: int = 7) -> list:
    """
    오늘부터 n일 후까지의 특일 정보(24절기, 잡절, 공휴일) 조회
    Args:
        n: 오늘 기준 며칠 후까지 조회할지 (기본값: 7)
    Returns:
        특일 리스트 [{"date": "20260101", "name": "신정", "type": "holiday"}]
        날짜순 정렬됨
    """
    today = arrow.now('Asia/Seoul')
    end_date = today.shift(days=n)

    # 조회할 연월 목록 생성
    months_to_query = set()
    current = today
    while current <= end_date:
        months_to_query.add((current.format('YYYY'), current.format('MM')))
        current = current.shift(months=1).replace(day=1)

    # 모든 특일 정보 수집
    all_special_days = []
    for year, month in months_to_query:
        for api_type in ['holiday', 'division', 'sundry']:
            days = fetch_special_days(year, month, api_type)
            all_special_days.extend(days)

    # 날짜 범위 필터링
    start_str = today.format('YYYYMMDD')
    end_str = end_date.format('YYYYMMDD')

    filtered = [
        day for day in all_special_days
        if start_str <= day['date'] <= end_str
    ]

    # 날짜순 정렬
    filtered.sort(key=lambda x: x['date'])

    return filtered


def get_today_info() -> str:
    """
    오늘의 특일 정보를 문자열로 반환
    Returns:
        특일 정보 문자열
    """
    today = arrow.now('Asia/Seoul')
    date_str = today.format('YYYY년 MM월 DD일')
    _, weekday_name = is_weekend(today)

    is_off, reason = is_day_off(today)

    if is_off:
        return f"📅 {date_str} ({weekday_name})\n🎉 오늘은 쉬는 날입니다: {reason}"
    else:
        return f"📅 {date_str} ({weekday_name})\n💼 오늘은 평일입니다."


def main():
    """특일 정보 조회 테스트"""
    print("=== 오늘의 특일 정보 ===\n")
    print(get_today_info())

    print("\n=== 이번 달 공휴일 목록 ===")
    today = arrow.now('Asia/Seoul')
    holidays = fetch_holidays(today.format('YYYY'), today.format('MM'))

    if holidays:
        for h in holidays:
            print(f"  - {h['date']}: {h['name']}")
    else:
        print("  이번 달에는 공휴일이 없습니다.")

    print("\n=== 앞으로 30일간 특일 정보 ===")
    type_names = {'holiday': '공휴일', 'division': '24절기', 'sundry': '잡절'}
    upcoming = get_upcoming_special_days(7)

    if upcoming:
        for day in upcoming:
            type_name = type_names.get(day['type'], day['type'])
            print(f"  - {day['date']}: {day['name']} ({type_name})")
    else:
        print("  특일 정보가 없습니다.")


if __name__ == "__main__":
    main()
