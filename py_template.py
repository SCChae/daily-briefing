"""
Python 클래스 템플릿
- 클래스 기반 구조
- credential/config 파일 로드 패턴
- main 함수에서 사용법 예제 및 테스트
"""

import json


class MyClass:
    """클래스 설명"""

    def __init__(self, credential_path: str):
        """
        초기화
        Args:
            credential_path: credential.json 파일 경로
        """
        with open(credential_path, 'r') as f:
            credentials = json.load(f)
            self.api_key = credentials.get('api_key')
            self.endpoint = credentials.get('endpoint')

        # 클라이언트 초기화
        # self.client = SomeClient(...)

    def do_something(self, param: str) -> str:
        """
        주요 기능 메서드
        Args:
            param: 입력 파라미터
        Returns:
            결과 문자열
        """
        # 구현
        return f"result: {param}"

    def do_another(self, param1: str, param2: str) -> dict:
        """
        추가 기능 메서드
        Args:
            param1: 첫번째 파라미터
            param2: 두번째 파라미터
        Returns:
            결과 딕셔너리
        """
        # 구현
        return {"param1": param1, "param2": param2}


def main():
    """사용법 예제 및 테스트"""

    print("=== MyClass 사용법 ===\n")

    # 1. 인스턴스 생성
    print("1. 인스턴스 생성")
    print('   obj = MyClass("credential.json")')

    # 2. 주요 메서드 사용
    print("\n2. do_something() 사용")
    print('   result = obj.do_something("hello")')

    # 3. 추가 메서드 사용
    print("\n3. do_another() 사용")
    print('   result = obj.do_another("a", "b")')

    print("\n=== 테스트 실행 ===\n")

    try:
        obj = MyClass("credential.json")

        result1 = obj.do_something("test")
        print(f"do_something 결과: {result1}")

        result2 = obj.do_another("x", "y")
        print(f"do_another 결과: {result2}")

    except FileNotFoundError as e:
        print(f"credential 파일 없음: {e}")
    except Exception as e:
        print(f"에러: {e}")


if __name__ == "__main__":
    main()
