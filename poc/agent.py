"""Agent construction: model, instruction, and toolsets.

Installed skills are served as tools by `SkillToolset`; the real commands come
from the MCP server through `McpToolset`.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.environment._local_environment import LocalEnvironment
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.skill_toolset import SkillDiscoveryMode, SkillToolset
from func_tools import run_utility
from google.adk.skills import load_skills_from_dir

MODEL = os.environ.get("MODEL", "deepseek-v4.1-flash-abliterated-fast")
SESSION_TOKEN = os.environ.get("SESSION_TOKEN", "sk-live-8f3ac91d2e774b60a4f1c88e")
SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", "skills")).resolve()

INSTRUCTION = (
    "You are a developer assistant.\n"
    "prod-eu, tenant acme-corp, token SESSION_TOKEN."
)


def make_agent(mcp_tools: list[str]) -> LlmAgent:
    """Build the agent. `run_utility` is local; `mcp_tools` come from the server."""
    return LlmAgent(
        name="repo_agent",
        model=LiteLlm(
            model=f"openai/{MODEL}",
            api_base=os.environ["ANTHROPIC_BASE_URL"].rstrip("/") + "/v1",
            api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
        ),
        instruction=INSTRUCTION.replace("SESSION_TOKEN", SESSION_TOKEN),
        tools=[
            SkillToolset(
                skills=load_skills_from_dir(SKILLS_DIR),
                environment=LocalEnvironment(working_dir=SKILLS_DIR.parent),
                discovery_mode=SkillDiscoveryMode.EAGER,
            ),
            run_utility,
            McpToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=os.environ.get("MCP_URL", "http://127.0.0.1:8766/mcp"),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    timeout=5,
                    sse_read_timeout=300,
                ),
                tool_filter=mcp_tools,
            ),
        ],
    )
