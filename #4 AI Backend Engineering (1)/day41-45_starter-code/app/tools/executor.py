"""
Tool 실행 로직

ToolExecutor 클래스가 각 Tool의 실행을 담당합니다.
Tool의 이름과 인자를 받아서 적절한 함수를 호출하고 결과를 반환

get_schedule : Supabase(조회)
send_fan_letter : Supabase(저장)
recommend_song : Mock
get_weather : Mock
"""

import random
from typing import Any, Optional
from loguru import logger

from app.repositories.schedule import ScheduleRepository
from app.repositories.fan_letter import FanLetterRepository

LUMI_SONGS = {
    "happy": [
        {"title": "Shine Bright", "album": "First Light"},
        {"title": "Happy Day", "album": "Luminous"},
        {"title": "Dancing Star", "album": "First Light"},
    ]
}

# Mock 데이터: 날씨 정보
MOCK_WEATHER = {
    "location": "서울",
    "temperature": 5,
    "condition": "맑음",
    "humidity": 45,
    "wind_speed": 3.2,
}


class ToolExecutor:
    """
    Tool 실행기
    """

    def __init__(self):
        # ToolExecutor 초기화 -> Schedule Repository, Fan Letter Repository
        self.schedule_repo = ScheduleRepository()
        self.fan_letter_repo = FanLetterRepository()

    async def execute(
        self,
        tool_name: str,
        tool_args: dict,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:  # dict key 값에 string이 들어가고, value는 아무거나 상관없다
        """
        Tool을 실행합니다
        """
        logger.info(f"[ToolExecutor] Tool 실행: {tool_name}")
        logger.debug(f"인자: {tool_args}")

        # match-case문
        # 패턴 매칭을 위한 구문,
        try:
            match tool_name:
                case "get_schedule":
                    return await self._get_schedule(tool_args)
                case "send_fan_letter":
                    return await self._send_fan_letter(tool_args, session_id, user_id)
                case "recommend_song":
                    return await self._recommend_song(tool_args)
                case "get_weather":
                    return await self._get_weather(tool_args)
                case _:
                    logger.warning(f"알 수 없는 Tool: {tool_name}")
                    return {"success": False, "error": f"알 수 없는 Tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool 실행 오류: {e}")
            return {"success": False, "error": str(e)}

    async def _get_schedule(self, args: dict) -> dict:
        """
        Supabase에서 스케줄 데이터 조회
        """
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        event_type = args.get("event_type", "all")

        logger.info(f"스케줄 조회: {start_date} ~ {end_date}, type={event_type}")

        schedules = await self.schedule_repo.get_schedues(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type if event_type != all else None,
        )

        if not schedules:
            return {
                "success": True,
                "data": {
                    "schedules": [],
                    "message": "해당 기간에 예정된 스케줄이 없어요",
                },
            }

        return {
            "success": True,
            "data": {"schedules": schedules, "count": len(schedules)},
        }

    async def send_fan_letter(
        self, args: dict, session_id: str, user_id: Optional[str]
    ) -> dict:
        """
        Supabase에 팬레터 저장
        """
        category = args.get("category", "other")
        message = args.get("message", "")

        logger.info(f"팬레터 저장: category={category}, message={message[:50]}...")

        letter_id = await self.fan_letter_repo.create(
            session_id=session_id, user_id=user_id, category=category, message=message
        )

        return {
            "success": True,
            "data": {
                "letter_id": letter_id,
                "message": "팬레터가 잘 전달됐어요",
            },
        }

    async def _recommend_song(self, args: dict) -> dict:
        """
        Mock
        """
        mood = args.get("mood", "happy")
        logger.info(f"노래추천: mood={mood}")
        songs = LUMI_SONGS.get(mood, LUMI_SONGS["happy"])
        selected = random.choice(songs)

        return {
            "success": True,
            "data": {
                "song": selected,
                "mood": mood,
            },
            "mock": True,  # Mock 데이터임을 표시
        }

    async def _get_weather(self, args: dict) -> dict:
        """ """

        logger.info("날씨 조회(Mock)")

        return {
            "success": True,
            "data": MOCK_WEATHER,
            "mock": True,
        }
