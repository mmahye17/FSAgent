from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WechatMessage:
    to_user_name: str = ""
    from_user_name: str = ""
    create_time: str = ""
    msg_type: str = "text"
    content: str = ""
    msg_id: str = ""
    agent_id: str = ""
    raw_xml: str = ""
