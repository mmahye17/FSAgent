from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from models.skill import SkillDefinition, SkillParameter


class BaseSkill(ABC):
    name: str = ""
    display_name: str = ""
    description: str = ""
    category: str = "general"
    requires_confirmation: bool = False
    parameters: list[SkillParameter] = []

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        ...

    def to_definition(self) -> SkillDefinition:
        return SkillDefinition(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            parameters=self.parameters,
            category=self.category,
            requires_confirmation=self.requires_confirmation,
        )
