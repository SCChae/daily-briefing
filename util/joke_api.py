"""
Official Joke API 클라이언트
- https://official-joke-api.appspot.com/
"""

import requests


class JokeApi:
    """Official Joke API 클라이언트"""

    def __init__(self, base_url: str = "https://official-joke-api.appspot.com"):
        """
        초기화
        Args:
            base_url: API 기본 URL
        """
        self.base_url = base_url

    def get_random_joke(self) -> dict:
        """
        랜덤 joke 조회
        Returns:
            joke 딕셔너리 (id, type, setup, punchline)
        """
        response = requests.get(f"{self.base_url}/random_joke")
        response.raise_for_status()
        return response.json()

    def get_jokes_by_type(self, joke_type: str, count: int = 1) -> list:
        """
        카테고리별 joke 조회
        Args:
            joke_type: 카테고리 (general, programming 등)
            count: 조회 개수
        Returns:
            joke 리스트
        """
        if count == 1:
            response = requests.get(f"{self.base_url}/jokes/{joke_type}/random")
        else:
            response = requests.get(f"{self.base_url}/jokes/{joke_type}/ten")
        response.raise_for_status()
        result = response.json()
        return result if isinstance(result, list) else [result]

    def get_joke_by_id(self, joke_id: int) -> dict:
        """
        ID로 joke 조회
        Args:
            joke_id: joke ID
        Returns:
            joke 딕셔너리
        """
        response = requests.get(f"{self.base_url}/jokes/{joke_id}")
        response.raise_for_status()
        return response.json()


def main():
    """사용법 예제 및 테스트"""

    print("=== JokeApi 사용법 ===\n")

    print("1. 인스턴스 생성")
    print("   api = JokeApi()")

    print("\n2. get_random_joke() - 랜덤 joke")
    print("   joke = api.get_random_joke()")

    print("\n3. get_jokes_by_type() - 카테고리별 joke")
    print('   jokes = api.get_jokes_by_type("programming")')

    print("\n4. get_joke_by_id() - ID로 조회")
    print("   joke = api.get_joke_by_id(1)")

    print("\n=== 테스트 실행 ===\n")

    try:
        api = JokeApi()

        # 랜덤 joke
        joke = api.get_random_joke()
        print(f"[랜덤 joke]")
        print(f"  Q: {joke['setup']}")
        print(f"  A: {joke['punchline']}")

        # 프로그래밍 joke
        jokes = api.get_jokes_by_type("programming")
        print(f"\n[프로그래밍 joke]")
        print(f"  Q: {jokes[0]['setup']}")
        print(f"  A: {jokes[0]['punchline']}")

    except Exception as e:
        print(f"에러: {e}")


if __name__ == "__main__":
    main()
