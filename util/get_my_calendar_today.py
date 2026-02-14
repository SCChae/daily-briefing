import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from util.ain_slack import AinSlack

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


#def get_calendar_service():
#    """Gets authorized calendar service."""
#    creds = None
#    if os.path.exists("./token.json"):
#        creds = Credentials.from_authorized_user_file("/home/scchae/work/tigris/token.json", SCOPES)
#    return build("calendar", "v3", credentials=creds)

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
        #today = today + datetime.timedelta(days=1)  # 내일 날짜 보기

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

AIN_CAL  = 'c_0dfb641923f99dd9592aea5532373393a5a56b61ff6004a4665a5ee96d8f364e@group.calendar.google.com'
AINR_CAL = 'c_4a296c449497a5362d9a06a2ae85431fbc1bc7771e0a6184eb9dd95ec23e46c2@group.calendar.google.com'
DATONR_CAL = 'c_765521344c3e3dff24976481f7ad15a725560472920d2e6f1b0ac1f831cdcd35@group.calendar.google.com'
MY_CAL   = 'chae@aination.kr'

def main():
    service = get_calendar_service()
    
    # List all available calendars
    #calendars = list_calendars(service)
    #if not calendars:
    #    return
    
    # Get events for selected calendar
    msg = get_todays_calendar_events(service, AINR_CAL)
    print(msg)
    msg = get_todays_calendar_events(service, DATONR_CAL)
    print(msg)
#    slack = AinSlack("/home/scchae/work/tigris/slack_credential.json")
#    thread_id = slack.send_message(msg)

if __name__ == "__main__":
    main()
