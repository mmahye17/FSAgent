from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.skills.registry import skill_registry
from common.logger import get_logger
from models.response import ResponseModel
from models.skill import SkillExecuteRequest, SkillListResponse, SkillResult

router = APIRouter(prefix="/skills", tags=["skills"])
logger = get_logger(__name__)


@router.get("", response_model=ResponseModel[SkillListResponse])
async def list_skills() -> ResponseModel[SkillListResponse]:
    skills = skill_registry.list_definitions()
    return ResponseModel(data=SkillListResponse(skills=skills))


@router.post("/{skill_name}/execute", response_model=ResponseModel[SkillResult])
async def execute_skill(
    skill_name: str, body: SkillExecuteRequest
) -> ResponseModel[SkillResult]:
    skill = skill_registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    import time

    start = time.monotonic()
    try:
        result_value = await skill.execute(**body.parameters)
        elapsed = (time.monotonic() - start) * 1000
        return ResponseModel(
            data=SkillResult(
                success=True,
                skill_name=skill_name,
                result=result_value,
                execution_time_ms=round(elapsed, 2),
            )
        )
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        logger.error("skill_execution_failed", skill=skill_name, error=str(exc))
        return ResponseModel(
            data=SkillResult(
                success=False,
                skill_name=skill_name,
                error=str(exc),
                execution_time_ms=round(elapsed, 2),
            )
        )
