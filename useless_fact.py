"""
Useless Facts API 클라이언트
https://uselessfacts.jsph.pl/ API를 사용하여 무작위 잡학사실을 조회합니다.
"""

import requests


class UselessFact:
    """Useless Facts API 클라이언트"""

    def __init__(self, language: str = "en"):
        """
        초기화
        Args:
            language: 언어 설정 (en: 영어, de: 독일어)
        """
        self.base_url = "https://uselessfacts.jsph.pl/api/v2/facts"
        self.language = language

    def get_random(self) -> dict:
        """
        무작위 잡학사실 조회
        Returns:
            잡학사실 정보 딕셔너리 (id, text, source, source_url, language, permalink)
        """
        url = f"{self.base_url}/random"
        params = {"language": self.language}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_today(self) -> dict:
        """
        오늘의 잡학사실 조회
        Returns:
            잡학사실 정보 딕셔너리 (id, text, source, source_url, language, permalink)
        """
        url = f"{self.base_url}/today"
        params = {"language": self.language}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


def main():
    """사용법 예제 및 테스트"""

    print("=== UselessFact 사용법 ===\n")

    print("1. 인스턴스 생성")
    print('   fact = UselessFact(language="en")')

    print("\n2. 메서드 사용")
    print('   random_fact = fact.get_random()')
    print('   today_fact = fact.get_today()')

    print("\n=== 테스트 실행 ===\n")

    try:
        fact = UselessFact(language="en")

        print("무작위 잡학사실:")
        random_fact = fact.get_random()
        print(f"  - {random_fact['text']}")

        print("\n오늘의 잡학사실:")
        today_fact = fact.get_today()
        print(f"  - {today_fact['text']}")

    except Exception as e:
        print(f"에러: {e}")


if __name__ == "__main__":
    main()
