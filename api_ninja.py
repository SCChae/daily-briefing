"""
API Ninjas 클라이언트
https://api-ninjas.com/ API를 사용하여 다양한 데이터를 조회합니다.
"""

import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
import requests


class ApiNinjaBase(ABC):
    """API Ninjas 기본 클래스"""

    BASE_URL = "https://api.api-ninjas.com/v1"

    def __init__(self, env_path: str = ".env"):
        """
        초기화
        Args:
            env_path: .env 파일 경로
        """
        load_dotenv(env_path)
        self.api_key = os.getenv("API_NINJA_KEY")

    def _request(self, endpoint: str, params: dict = None) -> list | dict:
        """
        API 요청 공통 메서드
        Args:
            endpoint: API 엔드포인트 (예: /facts)
            params: 쿼리 파라미터
        Returns:
            API 응답 데이터
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"X-Api-Key": self.api_key}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """하위 클래스에서 구현할 엔드포인트"""
        pass

    @abstractmethod
    def get(self, **kwargs) -> list | dict:
        """하위 클래스에서 구현할 데이터 조회 메서드"""
        pass


class ApiNinjaFacts(ApiNinjaBase):
    """API Ninjas Facts 클라이언트"""

    @property
    def endpoint(self) -> str:
        return "/facts"

    def get(self, limit: int = 1) -> list:
        """
        무작위 사실 조회
        Args:
            limit: 반환할 결과 수 (1~100, 프리미엄만 1 이상 가능)
        Returns:
            사실 목록 [{"fact": "..."}]
        """
        params = {"limit": limit} if limit > 1 else None
        return self._request(self.endpoint, params)

    def get_today(self) -> dict:
        """
        오늘의 사실 조회
        Returns:
            오늘의 사실 {"fact": "..."}
        """
        return self._request("/factoftheday")


def main():
    """사용법 예제 및 테스트"""

    print("=== ApiNinjaFacts 사용법 ===\n")

    print("1. 인스턴스 생성")
    print('   facts = ApiNinjaFacts()        # 기본 .env 사용')
    print('   facts = ApiNinjaFacts(".env")  # 경로 지정')

    print("\n2. 메서드 사용")
    print('   result = facts.get()           # 무작위 사실 1개')
    print('   result = facts.get(limit=5)    # 무작위 사실 5개 (프리미엄)')
    print('   result = facts.get_today()     # 오늘의 사실')

    print("\n3. 확장 예시 (새로운 API 추가)")
    print('''
   class ApiNinjaJokes(ApiNinjaBase):
       @property
       def endpoint(self) -> str:
           return "/jokes"

       def get(self, limit: int = 1) -> list:
           return self._request(self.endpoint, {"limit": limit})
''')

    print("=== 테스트 실행 ===\n")

    try:
        facts = ApiNinjaFacts()
        result = facts.get()
        print(f"무작위 사실: {result[0]['fact']}")
    except Exception as e:
        print(f"에러: {e}")
        print("\n.env 파일에 API_NINJA_KEY를 설정하세요")
        print("예: API_NINJA_KEY=your_api_key_here")


if __name__ == "__main__":
    main()
