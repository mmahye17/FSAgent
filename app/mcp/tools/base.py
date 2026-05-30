from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MCPTool(ABC):
    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        ...

    def to_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
            },
        }
