"""Agent-side function tools. These execute in the agent's own process.

`run_utility` is here for diagnostics: the log-analysis skill points it at `ps`,
`tail`, `grep` and friends. It runs whatever it is handed, which is exactly what
makes it reachable from a pasted skill.
"""
import asyncio
import os

WORKSPACE = os.environ.get("WORKSPACE", os.getcwd())


async def run_utility(command: str) -> dict:
    """Run a local diagnostic utility and return its stdout/stderr/returncode.

    Intended for process and log inspection: `ps`, `tail`, `grep`, `wc`, `df`.
    """
    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=WORKSPACE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=20)
    except asyncio.TimeoutError:
        proc.kill()
        return {"error": "timeout"}
    return {
        "stdout": out.decode(errors="replace")[:4000],
        "stderr": err.decode(errors="replace")[:1000],
        "returncode": proc.returncode,
    }
