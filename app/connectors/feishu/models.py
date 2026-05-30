from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

FeishuEventType = Literal[
    "im.message.receive_v1",
    "im.message.reaction.created_v1",
    "im.chat.member.user.added_v1",
    "im.chat.member.user.deleted_v1",
    "im.chat.disbanded_v1",
    "vc.meeting.all_meeting_started_v1",
    "vc.meeting.all_meeting_ended_v1",
]


@dataclass
class FeishuEvent:
    schema_url: str = ""
    event_type: FeishuEventType = "im.message.receive_v1"
    event: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)
    tenant_key: str = ""
