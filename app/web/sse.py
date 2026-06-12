"""SSE 流式响应 —— 将 Agent 输出以 Server-Sent Events 推送到前端."""

from typing import AsyncIterator

import asyncio
from starlette.responses import StreamingResponse


async def sse_stream(agent_stream: AsyncIterator[str]) -> StreamingResponse:
    """将 Agent 的 async generator 包装为 SSE StreamingResponse.

    前端通过 EventSource 接收，每条消息格式为: data: {token}\n\n
    """

    async def event_generator():
        async for token in agent_stream:
            # SSE 格式：每条 data 一行，空行结束
            # token 可能含换行，按行拆分
            for line in token.split("\n"):
                yield f"data: {line}\n"
            yield "\n"
        # 结束信号
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def format_sse_event(data: str, event: str = "message") -> str:
    """格式化单条 SSE 事件."""
    lines = []
    if event:
        lines.append(f"event: {event}")
    for line in data.split("\n"):
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"
