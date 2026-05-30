from __future__ import annotations

from typing import Any

from app.skills.base import BaseSkill
from app.skills.calendar import CalendarQuerySkill
from app.skills.meeting import MeetingBookSkill, MeetingNotifySkill
from app.skills.minutes import MinutesFetchSkill, MinutesGenerateSkill, MinutesExtractActionsSkill
from app.skills.progress import ProgressTrackSkill
from app.skills.weekly import WeeklyReportSkill
from common.logger import get_logger
from models.skill import SkillDefinition

logger = get_logger(__name__)


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults: list[BaseSkill] = [
            MeetingBookSkill(),
            MeetingNotifySkill(),
            CalendarQuerySkill(),
            MinutesFetchSkill(),
            MinutesGenerateSkill(),
            MinutesExtractActionsSkill(),
            ProgressTrackSkill(),
            WeeklyReportSkill(),
        ]
        for skill in defaults:
            self.register(skill)

    def register(self, skill: BaseSkill) -> None:
        self._skills[skill.name] = skill
        logger.debug("注册完成", name=skill.name)

    def get(self, name: str) -> BaseSkill | None:
        return self._skills.get(name)

    def list_definitions(self) -> list[SkillDefinition]:
        return [s.to_definition() for s in self._skills.values()]


skill_registry = SkillRegistry()
