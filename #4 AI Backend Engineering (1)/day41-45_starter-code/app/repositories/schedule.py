"""
스케줄 데이터 접근 계층

Supabase에서 루미의 스케줄 데이터를 조회합니다.
"""

from typing import Optional
from loguru import logger


from . import get_supabase_client


class ScheduleRepository:
    """
    스케줄 Repository

    Supabase에서 스케줄을 조회합니다.

    Example:
        >>>> repo = ScheduleRepository()
        >>>> schedule = await repo.get_schedule
                start_date = "2025-01-06",
                end_date = "2025-01-12"
    """

    def __init__(self):
        """ScheduleRepository 초기화"""
        self.client = get_supabase_client()
        if not self.client:
            raise ValueError(
                "Supabase 클라이언트가 설정되지 않았습니다. .env 파일을 확인하세요."
            )
        logger.info("Supabase 연결됨")

    async def get_schedues(
        self,
        start_date: str,
        end_date: str,
        event_type: Optional[str] = None,
    ) -> list[dict]:
        """
        스케줄 목록을 조회합니다.

        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            event_type: 이벤트 유형 필터 (선택)

        Returns:
            list[dict]: 스케줄 목록
        """
        try:
            # [설명] 쿼리 체이닝
            # 메서드 체이닝으로 조건을 추가합니다.
            # - select("*"): 모든 컬럼 선택
            # - gte(): 크거나 같음 (>=)
            # - lte(): 작거나 같음 (<=)
            # - eq(): 같음 (=)
            # - order(): 정렬
            query = self.client.table("schedules").select("*")

            # 날짜 필터 (start_time 컬럼 사용)
            if start_date:
                query = query.gte("start_time", start_date)
            if end_date:
                query = query.lte("end_time", end_date)

            if event_type:
                query = query.eq("event_type", event_type)

            response = query.order("start_time").execute()

            logger.info(f"Supabase 결과: {len(response.data)}건")
            return response.data

        except Exception as e:
            logger.error(f"Supabase 조회 오류: {e}")
            return []
