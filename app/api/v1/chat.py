from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.harness.graph import AgentGraph
from common.logger import get_logger
from common.utils import generate_id, generate_uuid, utc_now
from models.chat import AsyncChatResponse, ChatRequest, ChatResponse, TaskStatus
from models.response import ResponseModel

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

_agent_graph = AgentGraph()
_task_store: dict[str, TaskStatus] = {}


@router.post("", response_model=ResponseModel[ChatResponse])
async def chat_sync(request: ChatRequest) -> ResponseModel[ChatResponse]:
    session_id = request.session_id or generate_id()

    result = await _agent_graph.run(
        session_id=session_id,
        user_id=request.user_id,
        message=request.message,
        platform=request.platform,
        group_id=request.group_id,
        metadata=request.metadata,
    )

    return ResponseModel(
        data=ChatResponse(
            session_id=session_id,
            message_id=generate_uuid(),
            reply=result.reply,
            tool_calls_made=result.tool_calls_made,
        )
    )


@router.post("/async", response_model=ResponseModel[AsyncChatResponse])
async def chat_async(
    request: ChatRequest, background_tasks: BackgroundTasks
) -> ResponseModel[AsyncChatResponse]:
    task_id = generate_uuid()
    session_id = request.session_id or generate_id()

    _task_store[task_id] = TaskStatus(
        task_id=task_id,
        status="queued",
        created_at=utc_now(),
        updated_at=utc_now(),
    )

    background_tasks.add_task(_process_async_chat, task_id, request, session_id)

    return ResponseModel(
        data=AsyncChatResponse(task_id=task_id, session_id=session_id, status="queued")
    )


@router.get("/tasks/{task_id}", response_model=ResponseModel[TaskStatus])
async def get_task_status(task_id: str) -> ResponseModel[TaskStatus]:
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ResponseModel(data=task)


async def _process_async_chat(task_id: str, request: ChatRequest, session_id: str) -> None:
    _task_store[task_id].status = "processing"
    _task_store[task_id].updated_at = utc_now()

    try:
        result = await _agent_graph.run(
            session_id=session_id,
            user_id=request.user_id,
            message=request.message,
            platform=request.platform,
            group_id=request.group_id,
            metadata=request.metadata,
        )
        _task_store[task_id].status = "completed"
        _task_store[task_id].result = ChatResponse(
            session_id=session_id,
            reply=result.reply,
            tool_calls_made=result.tool_calls_made,
        )
    except Exception as exc:
        _task_store[task_id].status = "failed"
        _task_store[task_id].error = str(exc)
    finally:
        _task_store[task_id].updated_at = utc_now()
