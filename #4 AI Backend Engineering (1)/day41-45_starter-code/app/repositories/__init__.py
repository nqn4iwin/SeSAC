from loguru import logger
from app.core.config import settings

_supabase_client = None


def get_supabase_client():
    """
    Supabase 클라이언트를 반환(싱글톤 패턴)

    init.py에 있는 이유 -> schedule.py & fan_letter.py에서 모두 반복되어 사용
    """
    global _supabase_client

    if _supabase_client is None and settings.supabase_url and settings.supabase_key:
        try:
            from supabase import create_client

            _supabase_client = create_client(
                settings.supabase_url, settings.supabase_key
            )
            logger.info("Supabase 클라이언트 초기화 완료")

        except Exception as e:
            logger.warning(f"Supabase 초기화 실패: {e}")
            _supabase_client = None

    return _supabase_client
