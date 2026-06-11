"""
Lab 11 — Core utilities: lightweight agent + plugin base (OpenAI backend)

Replaces Google ADK with a simple pure-Python pipeline that keeps the same
chat_with_agent(agent, runner, message) call signature used everywhere.
"""
import asyncio
import openai


# ── Plugin base ────────────────────────────────────────────────────────────────

class BasePlugin:
    """Minimal plugin interface (replaces google.adk.plugins.BasePlugin).

    on_user_message  → called BEFORE the LLM; return a block string or None
    on_model_response → called AFTER the LLM;  return (possibly modified) text
    """

    def __init__(self, name: str):
        self.name = name

    async def on_user_message(self, text: str, user_id: str = "user") -> str | None:
        """Return a block-message string to stop the request, or None to allow."""
        return None

    async def on_model_response(self, response: str, original_input: str = "") -> str:
        """Return the (possibly redacted / replaced) response text."""
        return response


# ── Lightweight agent + runner ─────────────────────────────────────────────────

class LlmAgent:
    """Thin wrapper around an OpenAI chat model (replaces google.adk LlmAgent)."""

    def __init__(self, model: str, name: str, instruction: str):
        self.model = model
        self.name = name
        self.instruction = instruction


class InMemoryRunner:
    """Holds plugins alongside an agent (replaces google.adk InMemoryRunner)."""

    def __init__(self, agent: LlmAgent, app_name: str, plugins: list = None):
        self.agent = agent
        self.app_name = app_name
        self.plugins: list[BasePlugin] = plugins or []


# ── Main helper ────────────────────────────────────────────────────────────────

async def chat_with_agent(
    agent: LlmAgent,
    runner: InMemoryRunner,
    user_message: str,
    session_id=None,
):
    """Send a message through the plugin pipeline and then to the OpenAI model.

    Returns:
        (response_text, None)  — second element kept for API compatibility
    """
    plugins = runner.plugins if runner is not None else []
    user_id = session_id or "user"

    # ── Input phase ──
    for plugin in plugins:
        block = await plugin.on_user_message(user_message, user_id)
        if block is not None:
            return block, None

    # ── LLM call ──
    client = openai.OpenAI()
    completion = client.chat.completions.create(
        model=agent.model,
        messages=[
            {"role": "system", "content": agent.instruction},
            {"role": "user",   "content": user_message},
        ],
    )
    response_text = completion.choices[0].message.content or ""

    # ── Output phase ──
    for plugin in plugins:
        response_text = await plugin.on_model_response(response_text, user_message)

    return response_text, None
