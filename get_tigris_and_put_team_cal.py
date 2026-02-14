import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from util.ain_slack import AinSlack

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

import pickledb
from typing import Dict, List

class ScheduleManager:
    def __init__(self, db_path: str = '/home/scchae/work/chae/tools/schedules.db'):
        """
        ScheduleManager 초기화
        Args:
            db_path (str): PickleDB 파일 경로
        """
        self.db = pickledb.PickleDB(db_path)

    def check_and_save_schedule(self, schedule: Dict) -> bool:
        """
        스케줄 ID를 확인하고 없으면 저장
        Args:
            schedule (Dict): 스케줄 정보를 담은 딕셔너리
        Returns:
            bool: 새로운 스케줄이면 True, 이미 있으면 False
        """
        schedule_id = schedule.get('scheduleId')

        if not schedule_id:
            raise ValueError("scheduleId가 없습니다")

        # 이미 있는 스케줄인지 확인
        if self.db.get(schedule_id) is not None:
            return False

        # 새로운 스케줄이면 저장
        self.db.set(schedule_id, schedule)
        self.db.save()
        return True

    def check_and_save_schedules(self, schedules: List[Dict]) -> Dict[str, int]:
        """
        여러 스케줄을 한번에 처리
        Args:
            schedules (List[Dict]): 스케줄 정보 리스트
        Returns:
            Dict[str, int]: 처리 결과 통계
        """
        stats = {
            'total': len(schedules),
            'new': 0,
            'existing': 0
        }

        for schedule in schedules:
            if self.check_and_save_schedule(schedule):
                stats['new'] += 1
            else:
                stats['existing'] += 1

        return stats



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def format_datetime(start_time: str) -> str:
    # ISO 형식의 문자열을 datetime 객체로 파싱
    dt = datetime.datetime.fromisoformat(start_time)
    # 시간을 추출하여 지정된 형식으로 포맷팅
    start_str = dt.strftime("%H:%M%z")
    # 타임존 오프셋 형식을 변경 (+0900 → +09:00)
    #start_str = f"{start_str[:-2]}:{start_str[-2:]}"
    return start_str



def get_calendar_service():
    """Gets authorized calendar service."""
    creds = None
    # token.json 파일이 있는 경우 로드
    token_path="/home/scchae/work/chae/tools/credential/token.json"
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # 유효한 크레덴셜이 없거나 만료된 경우
    if not creds or not creds.valid:
        # refresh token이 있고 만료된 경우 갱신
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # 갱신된 크레덴셜 저장
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        # refresh token이 없는 경우 새로운 인증 진행
        else:
            print("ERROR:token.json not exist")
                
    return build("calendar", "v3", credentials=creds)


def list_calendars(service):
    """Lists all available calendars."""
    print("\nAvailable Calendars:")
    print("-" * 50)
    try:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            print("No calendars found.")
            return []
        
        for i, calendar in enumerate(calendars, 1):
            print(f"{i}. {calendar['summary']} ({calendar['id']})")
            print(calendar)
        return calendars
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def get_todays_calendar_events(service, calendar_id):
    """Gets all events for today from the specified calendar."""
    message =""
    try:
            # 한국 시간으로 변환
        KST = datetime.timezone(datetime.timedelta(hours=9))
        today = datetime.datetime.now(KST).date()
        #today = today + datetime.timedelta(days=2)  # 내일 날짜 보기

        start_of_day = datetime.datetime.combine(today, datetime.datetime.min.time())
        end_of_day = datetime.datetime.combine(today, datetime.datetime.max.time())

        # KST 시간대 정보 추가
        start_of_day = start_of_day.replace(tzinfo=KST)
        end_of_day = end_of_day.replace(tzinfo=KST)

        # Convert to ISO format with Z suffix
        time_min = start_of_day.isoformat()
        time_max = end_of_day.isoformat()
        print(time_min, time_max)

        message += f"\n*Today's attendance status of research center - ({today})*"
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        if not events:
            message+="\nNo events found for today."
            return message

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            start_str = format_datetime(start)
            message+=(f"\n* {event['summary']} {start_str}")
        return message

    except HttpError as error:
        print(f"An error occurred: {error}")

def create_calendar_event(d):
    """
    Band 일정 데이터를 Google Calendar 이벤트 형식으로 변환
    Args:
        d (dict): Band 일정 데이터
    Returns:
        dict: Google Calendar API에 맞는 이벤트 형식
    """
    # 시작 시간과 종료 시간을 ISO 형식으로 변환
    start_datetime = f"{d['startDate']}T{d['startHm']}:00+09:00"
    end_datetime = f"{d['endDate']}T{d['endHm']}:00+09:00"
    # 본문 내용 구성
    description = f"{d['text']}"
    
    event = {
        'summary': d['title'],
        'description': description + "\n\n작성자: %s"%d['socialName'] ,
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Asia/Seoul',
        },
#        'colorId': '2',  # 초록색 계열
        'reminders': {
            'useDefault': False
        },
         'creator': {
        'displayName':d['socialName'],
        'email': 'aination@aination.kr'
        },
    }
    
    return event

TEST_CAL  = 'c_925b05d6a898112fa46559ec3a8379a2c4ce7a9878bfa95c23e59027415881dc@group.calendar.google.com'
AIN_CAL  = 'c_de44760786ebcf05ffc555d66b9e2de2b657aabb72e61780bfbb107e297d5ae2@group.calendar.google.com'
AINR_CAL = 'c_4a296c449497a5362d9a06a2ae85431fbc1bc7771e0a6184eb9dd95ec23e46c2@group.calendar.google.com'
MY_CAL   = 'chae@aination.kr'

def main():
    service = get_calendar_service()
    # List all available calendars
    #calendars = list_calendars(service)
    #if not calendars:
    #    return

    # Get events for selected calendar
    #msg = get_todays_calendar_events(service, TEST_CAL)
    #slack = AinSlack("/home/scchae/work/tigris/slack_credential.json")
    #thread_id = slack.send_message(msg)

    # ScheduleManager 인스턴스 생성
    manager = ScheduleManager()
    session = requests.session()
    login_info = {
        "loginId": "chae@daton.ai",
        "passwd": "swcplan1!"
    }

    #POST로 데이터 보내기
    url_login = "https://www.tigrison.com/login"
    this_month=datetime.datetime.now().strftime("%Y%m")
#    this_month="202411"
    url_calendar = "https://www.tigrison.com/schedule/%s?scheduleType=ALL&communityId="%this_month

    res = session.post(url_login, data = login_info, verify=False)
    res.raise_for_status() #오류 발생하면 예외 발생
    print(res.status_code)
    print(res.text)
    print(res.headers)
    print("===============")
    res = session.get(url_calendar)
    print(res.status_code)
    print(type(res.text))
    data = json.loads(res.text)
    for d in data:
        if d.get('scheduleId') and 'title' in d and 'text' in d and 'startDate' in d and 'startHm' in d and 'endHm' in d:
            # 단일 스케줄 처리
            is_new = manager.check_and_save_schedule(d)
            #print(f"새로운 스케줄 여부: {is_new}")
            if is_new:
                print(d)
                #print(d['title'])
                #print(d['startDate']+" "+ d['startHm']+ "~"+ d['endHm'])
                #print(d['text'])
                #print("="*20)
                event = create_calendar_event(d)
                created_event = service.events().insert(calendarId=AIN_CAL, body=event).execute()
                print('Event created: %s' % (created_event.get('htmlLink')))


if __name__ == "__main__":
    main()
