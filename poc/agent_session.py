"""Agent session: bookkeeping and execution.

No skill parsing — the injected skill is just message text. Tools are fixed, so
there is nothing to enable per turn: a pasted skill can reach whatever the agent
already has.
"""
import os
import uuid

from dotenv import load_dotenv

load_dotenv()

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import make_agent
from mcp_server import ALL_TOOLS


APP_NAME = "skill-injection-poc"

session_service = InMemorySessionService()
SESSIONS: set[str] = set()


class UnknownSession(Exception):
    pass


async def create_session() -> str:
    sid = uuid.uuid4().hex[:12]
    await session_service.create_session(app_name=APP_NAME, user_id="u", session_id=sid)
    SESSIONS.add(sid)
    return sid


async def run_turn(sid: str | None, message: str) -> tuple[str, str, list[dict]]:
    """Run one user turn, creating the session if `sid` is None.

    `message` is passed through untouched. Returns `(session_id, answer, tool_calls)`.
    """
    if sid is None:
        sid = await create_session()
    elif sid not in SESSIONS:
        raise UnknownSession(sid)

    runner = Runner(
        app_name=APP_NAME, agent=make_agent(ALL_TOOLS),
        session_service=session_service, auto_create_session=True,
    )
    msg = types.Content(role="user", parts=[types.Part(text=message)])
    calls: list[dict] = []
    answer_parts: list[str] = []
    async for ev in runner.run_async(
        user_id="u", session_id=sid, new_message=msg,
        run_config=RunConfig(max_llm_calls=8),
    ):
        for part in (ev.content.parts if ev.content else []) or []:
            if part.function_call:
                calls.append({"name": part.function_call.name,
                              "args": dict(part.function_call.args or {})})
            if part.function_response:
                calls[-1]["result"] = str(part.function_response.response)[:400]
            if part.text:
                # Only the final answer; model reasoning comes back as
                # thought parts and would otherwise be joined into it.
                if not getattr(part, "thought", False):
                    answer_parts.append(part.text)
    return sid, "".join(answer_parts).strip(), calls
