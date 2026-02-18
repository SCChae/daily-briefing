import json
import os
import requests
from dotenv import load_dotenv
from util.ain_slack import AinSlack

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIAL_ENV = os.path.join(BASE_DIR, "credential", ".env")
SLACK_CREDENTIAL_TEST = os.path.join(BASE_DIR, "credential", "slack_credential_test.json")

load_dotenv(CREDENTIAL_ENV)


def main():
    # Tigris 로그인
    session = requests.session()
    login_info = {
        "loginId": os.environ["TIGRIS_LOGIN_ID"],
        "passwd": os.environ["TIGRIS_PASSWORD"],
    }
    url_login = "https://www.tigrison.com/login"
    res = session.post(url_login, data=login_info, verify=False)
    res.raise_for_status()
    print(f"로그인: {res.status_code}")

    # 공지사항 조회
    res = session.get("https://www.tigrison.com/feed/notices", verify=False)
    res.raise_for_status()
    data = res.json()
    notices = data.get("data", [])
    print(f"공지사항: {len(notices)}건")

    if not notices:
        print("새 공지사항 없음")
        return

    # Slack 메시지 전송
    slack = AinSlack(SLACK_CREDENTIAL_TEST)
    for notice in notices:
        title = notice.get("title", "제목 없음")
        content = notice.get("text", notice.get("content", ""))
        author = notice.get("socialName", notice.get("author", ""))
        msg = f"📢 [티그리스 공지] {title}"
        if author:
            msg += f"\n작성자: {author}"
        if content:
            msg += f"\n{content[:500]}"
        print(f"전송: {title}")
        slack.send_message(msg)

    print("Slack 전송 완료")


if __name__ == "__main__":
    main()
