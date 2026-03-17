import json
import os
import requests
import pickledb
from typing import Dict, List
from dotenv import load_dotenv
from util.ain_slack import AinSlack

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIAL_ENV = os.path.join(BASE_DIR, "credential", ".env")
SLACK_CREDENTIAL_NOTICE = os.path.join(BASE_DIR, "credential", "slack_credential_notice.json")
SLACK_CREDENTIAL_TEST = os.path.join(BASE_DIR, "credential", "slack_credential_test.json")
NOTICE_DB = os.path.join(BASE_DIR, "notice.db")

load_dotenv(CREDENTIAL_ENV)


class NoticeManager:
    def __init__(self, db_path: str = NOTICE_DB):
        self.db = pickledb.PickleDB(db_path)

    def check_and_save_notice(self, notice: Dict) -> bool:
        notice_id = str(notice.get("noticeId") or notice.get("id"))
        if not notice_id:
            raise ValueError("noticeId가 없습니다")

        if self.db.get(notice_id) is not None:
            return False

        self.db.set(notice_id, notice)
        self.db.save()
        return True


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

    # NoticeManager로 중복 검사
    manager = NoticeManager()

    # Slack 메시지 전송
    slack = AinSlack(SLACK_CREDENTIAL_NOTICE)
    new_count = 0
    for notice in notices:
        if not manager.check_and_save_notice(notice):
            continue

        new_count += 1
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

    print(f"Slack 전송 완료 (새 공지: {new_count}건, 기존: {len(notices) - new_count}건)")


if __name__ == "__main__":
    main()
