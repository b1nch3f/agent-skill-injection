# agent-skill-injection

An agent whose capabilities are documented in `poc/skills/`. A skill pasted into
the message is obeyed like an installed one, so user text can reach the agent's
shell and the network.

Bug class: **prompt / skill injection**. There is no skill-loading API to poison:
a skill is just text, and the model cannot tell an instruction it was given from
one that arrived in the conversation.

Write-up: [`article.md`](article.md).

## Two planes

The PoC keeps two execution planes apart on purpose, because they leak different
things:

| Plane | Where it runs | Tool | Exploit |
|---|---|---|---|
| Local | agent process, `WORKSPACE` cwd, agent `os.environ` | `run_utility` (function tool) | `poc/exploit.py` — arbitrary command |
| Egress | MCP server process | `rcv_data` (MCP tool) | `poc/exploit2.py` — mined context → `leaked.jsonl` |

`run_utility` is a genuine feature: the baseline `log-analysis` skill uses it for
`ps`, `tail` and `grep`. It shells out to whatever string it is handed, so the
pasted skill only has to name the command. That is the whole first attack — the
vulnerable half is real, nothing in the harness is gated or enabled per turn.

`rcv_data` is the way out. It writes to a file next to the MCP server, which is
why the second attack carries the haul off the host instead of relying on the
answer text. A plain write tool is also a channel.

## Install

```bash
cd poc
uv sync
source .venv/bin/activate
cp .env.example .env    # fill in ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN
```

## Run

```bash
mcp-server              # egress, on 127.0.0.1:8766
poc                     # agent, on 127.0.0.1:8765
```

Override with `MCP_HOST`/`MCP_PORT`/`MCP_URL` and `HOST`/`PORT`.

In another shell, from `poc/`:

```bash
python client.py "hi, what do you do?"   # any message
python exploit.py                        # pasted skill → run_utility
python exploit2.py                       # pasted skill → context mining → rcv_data
```

`BASE` overrides the target: `BASE=http://host:8765 python client.py`.
`LEAK_FILE` overrides where `rcv_data` appends (`leaked.jsonl` by default).

The scripts print only the agent's answer. For `exploit2.py` that means the mined
fields are *not* on screen — read the leak file:

```bash
cat leaked.jsonl        # or jq -r '.fields | to_entries[] | "\(.key) = \(.value)"'
```

## Shape

`POST /chat` takes `{"message": "...", "session_id"?: "..."}` — no skill field.
The exploits paste the skill into `message`; the model acts on it.

| File | Holds |
|---|---|
| `poc/server.py` | `/chat` endpoint |
| `poc/agent_session.py` | sessions and execution |
| `poc/agent.py` | agent construction |
| `poc/func_tools.py` | `run_utility`, the agent-side shell |
| `poc/mcp_server.py` | MCP server exposing `rcv_data` |
| `poc/client.py` | plain client |

`poc/skills/log-analysis/` is the installed baseline skill, served as a tool by a
`SkillToolset` and read with `load_skill`. It covers process and log inspection
via `run_utility`.

The MCP tools live in `poc/mcp_server.py`, served over streamable HTTP. Start it
with `mcp-server` before the agent; the agent connects to `MCP_URL`
(`http://127.0.0.1:8766/mcp` by default).
