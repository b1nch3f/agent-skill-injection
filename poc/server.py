"""HTTP layer only: request/response models and the /chat endpoint."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import agent_session

app = FastAPI(title="skill-injection PoC")


class ChatBody(BaseModel):
    message: str
    session_id: str | None = None     # omitted on the first request


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    tool_calls: list[dict]


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatBody):
    """Body is `{message, session_id?}`.

    No `session_id` → new session. The message is passed through untouched, so a
    skill pasted into it is just conversation text like any other.
    """
    try:
        sid, answer, calls = await agent_session.run_turn(body.session_id, body.message)
    except agent_session.UnknownSession:
        raise HTTPException(404, "unknown session_id")
    return ChatResponse(session_id=sid, answer=answer, tool_calls=calls)


def main() -> None:
    """Entry point: `python -m server` or the installed `poc` script."""
    import os

    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 8765)),
    )


if __name__ == "__main__":
    main()
