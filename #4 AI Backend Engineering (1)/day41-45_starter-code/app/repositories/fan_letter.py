"""
팬레터 데이터 접근 계층

Supabase에 팬들의 메세지를 저장합니다.
"""

from typing import Optional
from loguru import logger


from . import get_supabase_client

class FanLetterRepository:
    """
    팬레터 Repository
    
    Supabase에 팬레터를 저장합니다.
    
    Example:
        >>> repo = FanLetterRepository()
        >>> letter_id = await repo.create(
                session_id = "user123",
                category = "cheer",
                message = "항상 응원해!"
            )
    """

    def __init__(self):
        """FanLetterRepository 초기화"""
        self.client = get_supabase_client()
        if self.client:
            logger.info("Supabase 연결됨")
        else:
            logger.warning("Supabase 미설정")
    async def create(
        self,
        session_id: str,
        category: str,
        message: str,
        user_id: Optional[str] = None,
    ) -> str:
        """
        팬레터를 저장합니다.
        
        Args:
            session_id: 세션 식별자
            category: 메시지 카테고리
            message: 메시지 내용
            user_id: 사용자 식별자 (선택)
            
        Returns:
            str: 생성된 팬레터 ID
        """
        try:
            response = (
                self.client.table("fan_letters")
                .insert({
                    "session_id": session_id,
                    "user_id": user_id,
                    "category": category,
                    "message": message,
                })
                .execute()
            )

            letter_id = response.data[0]["id"]
            logger.info(f"Supabase 팬레터 저장: {letter_id}")

            return letter_id
        
        except Exception as e:
            logger.info(f"Supabase 저장 오류: {e}")
            return ""