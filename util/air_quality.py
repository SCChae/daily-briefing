import requests
import os
from dotenv import load_dotenv

load_dotenv()

GONGGONG_API_KEY = os.environ.get("GONGGONG_API_KEY", "")

api_url = "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"

STATION_NAME = "서초구"

GRADE_EMOJI = {
    '1': '😊',
    '2': '🙂',
    '3': '😷',
    '4': '🚫',
}

GRADE_LABEL = {
    '1': '좋음',
    '2': '보통',
    '3': '나쁨',
    '4': '매우나쁨',
}


def get_air_quality() -> str:
    """에어코리아 API에서 양재동 실시간 미세먼지 정보를 조회하여 문자열로 반환"""
    params = {
        'serviceKey': GONGGONG_API_KEY,
        'returnType': 'json',
        'numOfRows': '1',
        'pageNo': '1',
        'stationName': STATION_NAME,
        'dataTerm': 'DAILY',
        'ver': '1.0',
    }

    response = requests.get(api_url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    items = data['response']['body']['items']
    if not items:
        return "공기질 정보를 가져오지 못했습니다."

    item = items[0]
    pm10_value = item.get('pm10Value', '-')
    pm10_grade = item.get('pm10Grade', '')
    pm25_value = item.get('pm25Value', '-')
    pm25_grade = item.get('pm25Grade', '')

    pm10_emoji = GRADE_EMOJI.get(pm10_grade, '❓')
    pm10_label = GRADE_LABEL.get(pm10_grade, pm10_grade)
    pm25_emoji = GRADE_EMOJI.get(pm25_grade, '❓')
    pm25_label = GRADE_LABEL.get(pm25_grade, pm25_grade)

    return (
        f"{pm10_emoji} 미세먼지(PM10): {pm10_value}μg/m³ {pm10_label} | "
        f"{pm25_emoji} 초미세먼지(PM2.5): {pm25_value}μg/m³ {pm25_label}"
    )


def main():
    msg = get_air_quality()
    print(msg)

if __name__ == "__main__":
    main()
