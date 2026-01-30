from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json

class AinSlack:
    def __init__(self, credential_path):
        """
        SlackAPI 클래스 초기화
        Args:
            credential_path (str): slack_credential.json 파일 경로
        """
        try:
            with open(credential_path, 'r') as f:
                credentials = json.load(f)
                self.slack_token = credentials.get('slack_token')
                self.channel_id = credentials.get('channel_id')
                
            if not self.slack_token or not self.channel_id:
                raise ValueError("slack_token과 channel_id가 필요합니다")
                
            self.client = WebClient(token=self.slack_token)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Credential 파일을 찾을 수 없습니다: {credential_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Credential 파일이 올바른 JSON 형식이 아닙니다: {credential_path}")

    def send_message(self, message):
        """
        Slack 채널에 메시지 전송
        Args:
            message (str): 전송할 메시지
        Returns:
            str: 메시지 thread ID (실패시 None)
        """
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message
            )
            return response["ts"]
        except SlackApiError as e:
            print(f"메시지 전송 중 에러 발생: {e}")
            return None

    def send_reply(self, thread_ts, reply_message):
        """
        Slack 스레드에 답글 전송
        Args:
            thread_ts (str): 답글을 달 스레드의 ID
            reply_message (str): 전송할 답글 내용
        Returns:
            str: 답글 메시지 ID (실패시 None)
        """
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=thread_ts,
                text=reply_message
            )
            return response["ts"]
        except SlackApiError as e:
            print(f"답글 전송 중 에러 발생: {e}")
            return None


def main():
    """
    메인 함수 - AinSlack 클래스 테스트
    """
    try:
        # AinSlack 인스턴스 생성
        slack = AinSlack("slack_credential.json")
        
        # 테스트 메시지 전송
        print("메시지 전송 테스트 시작...")
        thread_id = slack.send_message("AinSlack 테스트 메시지입니다.")
        
        if thread_id:
            print(f"메시지 전송 성공! Thread ID: {thread_id}")
            
            # 답글 테스트
            print("\n답글 전송 테스트 시작...")
            reply_id = slack.send_reply(thread_id, "테스트 답글입니다.")
            
            if reply_id:
                print(f"답글 전송 성공! Reply ID: {reply_id}")
            else:
                print("답글 전송 실패!")
        else:
            print("메시지 전송 실패!")
            
    except Exception as e:
        print(f"테스트 중 에러 발생: {e}")


if __name__ == "__main__":
    main()
