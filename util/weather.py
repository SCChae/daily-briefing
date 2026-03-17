import requests
import os
import arrow
from dotenv import load_dotenv

load_dotenv()

GONGGONG_API_KEY = os.environ.get("GONGGONG_API_KEY", "")

api_url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"

# 관측 위치 : 서울특별시 서초구 양재1동
NX = '61'
NY = '125'

# 기상청 단기예보 발표 시각 (3시간 간격)
BASE_TIMES = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']

'''
category: 예보 항목
- TMN : 최저 기온 - 오전 6시
- TMX : 최고 기온 - 오후 3시
- SKY : 하늘 상태
- PTY : 강수 형태

참고: 기상청 단기예보 API 발표 시각별 포함 항목
- TMN(최저기온): 0200 발표에만 포함
- TMX(최고기온): 0500 이후 발표에 포함
- 따라서 0500 이후 조회 시 TMN이 없으면 0200 데이터에서 별도로 가져와야 함
'''

STATUS_OF_SKY = {
    '1': '맑음 ☀️',
    '3': '구름많음 ☁️',
    '4': '흐림 ⛅️',
}

STATUS_OF_PRECIPITATION = {
    '0': '없음',
    '1': '비 🌧️',
    '2': '비/눈 🌨️',
    '3': '눈 ❄️',
    '4': '소나기 ☔️'
}


def get_latest_base_time(current_time_kst):
    """현재 시간 기준으로 가장 최근 발표된 base_time과 base_date를 반환"""
    current_hour = current_time_kst.hour
    current_minute = current_time_kst.minute
    current_hhmm = current_hour * 100 + current_minute

    # 가장 최근 발표 시각 찾기
    latest_base_time = None
    for bt in reversed(BASE_TIMES):
        if current_hhmm >= int(bt):
            latest_base_time = bt
            break

    # 현재 시간이 0200 이전이면 전날 2300 사용
    if latest_base_time is None:
        base_date = current_time_kst.shift(days=-1).format("YYYYMMDD")
        latest_base_time = '2300'
    else:
        base_date = current_time_kst.format("YYYYMMDD")

    return base_date, latest_base_time


def fetch_weather_data(base_date, base_time):
    """기상청 API에서 날씨 데이터를 가져옴"""
    params = {
        'serviceKey': GONGGONG_API_KEY,
        'numOfRows': '300',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': NX,
        'ny': NY,
        'pageNo': '1'
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'body' not in data.get('response', {}):
            return None

        return data['response']['body']['items']['item']

    except requests.exceptions.RequestException as err:
        print(f"API 요청 오류: {err}")
        return None


def find_forecast_value(items, category, fcst_time=None):
    """예보 항목에서 특정 카테고리 값을 찾음"""
    for item in items:
        if item['category'] == category:
            if fcst_time is None or item['fcstTime'] == fcst_time:
                return item['fcstValue']
    return None


def get_today_weather():
    # 현재 날짜 (KST 기준)
    current_time_kst = arrow.now('Asia/Seoul')

    # 가장 최근 발표 시각 계산
    base_date, base_time = get_latest_base_time(current_time_kst)

    # 날씨 데이터 가져오기
    items = fetch_weather_data(base_date, base_time)

    if items is None:
        return "날씨 정보를 가져오지 못했습니다. 😢"

    # 최저/최고 기온
    lowest_temp = find_forecast_value(items, 'TMN')
    highest_temp = find_forecast_value(items, 'TMX')

    # TMN은 0200 발표에만 포함되므로, 없으면 0200 데이터에서 가져오기
    if lowest_temp is None and base_time != '0200':
        items_0200 = fetch_weather_data(base_date, '0200')
        if items_0200:
            lowest_temp = find_forecast_value(items_0200, 'TMN')

    # 시간대별 예보: 오전(09), 낮(12), 오후(15), 저녁(18)
    SLOTS = [('0900', '오전'), ('1200', '낮'), ('1500', '오후'), ('1800', '저녁')]
    slot_parts = []
    prev_sky_key = None
    for fcst_time, label in SLOTS:
        sky = find_forecast_value(items, 'SKY', fcst_time)
        pty = find_forecast_value(items, 'PTY', fcst_time)
        tmp = find_forecast_value(items, 'TMP', fcst_time)
        pop = find_forecast_value(items, 'POP', fcst_time)
        if sky is None:
            continue

        sky_key = pty if pty and pty != '0' else sky
        sky_str = STATUS_OF_PRECIPITATION.get(pty, '') if pty and pty != '0' else STATUS_OF_SKY.get(sky, sky)

        parts = [f"{label} {sky_str} {tmp}°C"]
        if pop and int(pop) >= 20:
            parts.append(f"강수{pop}%")
        slot_str = ' '.join(parts)

        # 하늘상태가 이전 슬롯과 같으면 기온만 표시
        if sky_key == prev_sky_key:
            slot_str = f"{label} {tmp}°C"
            if pop and int(pop) >= 20:
                slot_str += f" 강수{pop}%"

        slot_parts.append(slot_str)
        prev_sky_key = sky_key

    temp_range = ""
    if lowest_temp and highest_temp:
        temp_range = f"🌡 {lowest_temp}°C → {highest_temp}°C"
    elif highest_temp:
        temp_range = f"🌡 최고 {highest_temp}°C"

    forecast_line = " / ".join(slot_parts)

    weather_msg = ""
    if temp_range:
        weather_msg += f"{temp_range}\n"
    if forecast_line:
        weather_msg += f"📋 {forecast_line}"

    return weather_msg if weather_msg else "날씨 정보를 가져오지 못했습니다. 😢"


def main():
    msg = get_today_weather()
    print(msg)

if __name__ == "__main__":
    main()
