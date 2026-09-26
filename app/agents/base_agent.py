"""
Base Agent — Abstract foundation for all multi-agent components.

Every specialised agent inherits from BaseAgent and implements run().
The base class provides:
  - Unified LLM access via ModelRouter (Gemini → Groq fallback)
  - Structured logging with agent name
  - JSON response parsing with retries
  - Standard result envelope
"""

import time
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Any
from ..utils.model_router import generate, parse_json_from_response


class AgentResult:
    """Standard result envelope returned by every agent."""

    def __init__(self, agent_name: str, data: dict, model_used: str = "", error: str = ""):
        self.agent_name  = agent_name
        self.data        = data          # The actual agent output
        self.model_used  = model_used    # Which LLM ran this
        self.error       = error         # Non-empty if the agent failed
        self.success     = not bool(error)

    def __repr__(self):
        status = "OK" if self.success else f"ERR:{self.error[:40]}"
        return f"<AgentResult agent={self.agent_name} status={status} model={self.model_used}>"


class BaseAgent(ABC):
    """
    Abstract base for all specialised agents.

    Sub-classes must implement:
        build_prompt(**inputs) -> str
        parse_output(text, **inputs) -> dict

    And optionally override:
        run(**inputs) -> AgentResult   (for fully custom control flow)
    """

    name: str = "BaseAgent"

    # ── LLM parameters (override in subclass) ──────────────────────────────
    temperature: float = 0.3
    max_tokens:  int   = 1500
    task_type:   str   = "general"   # "research" | "pitch" | "audit" | "general"

    def _log(self, msg: str):
        print(f"[{self.name}] {msg}")

    def _call_llm(self, prompt: str, task_type: str = None) -> dict:
        """
        Call the model router and return {"text": ..., "model_used": ...}.
        Uses self.task_type unless overridden by the task_type argument.
        Raises RuntimeError if all providers fail.
        """
        effective_task = task_type or self.task_type
        self._log(f"Calling LLM (task={effective_task})...")
        result = generate(
            prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            task_type=effective_task,
        )
        self._log(f"Response received from {result['model_used']}")
        return result

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from LLM response with markdown fence stripping."""
        return parse_json_from_response(text)

    @abstractmethod
    def build_prompt(self, **inputs) -> str:
        """Build the prompt string from inputs. Must be implemented."""

    @abstractmethod
    def parse_output(self, text: str, **inputs) -> dict:
        """Parse LLM output into a structured dict. Must be implemented."""

    def run(self, **inputs) -> "AgentResult":
        """
        Default synchronous run loop:
          1. Build prompt
          2. Call LLM (with agent's task_type for smart routing)
          3. Parse output
          4. Return AgentResult

        Override this for custom control flow.
        """
        self._log(f"Starting with inputs: {list(inputs.keys())}")
        try:
            prompt   = self.build_prompt(**inputs)
            llm_out  = self._call_llm(prompt)
            data     = self.parse_output(llm_out["text"], **inputs)
            self._log("Completed successfully")
            return AgentResult(
                agent_name=self.name,
                data=data,
                model_used=llm_out["model_used"],
            )
        except Exception as e:
            self._log(f"Failed: {e}")
            return AgentResult(
                agent_name=self.name,
                data={},
                error=str(e),
            )

    # ── Async wrapper ────────────────────────────────────────────────────────

    async def run_async(self, **inputs) -> "AgentResult":
        """
        Run this agent in a thread pool so it can be awaited inside asyncio.gather()
        without blocking the event loop. Synchronous LLM calls go into executor.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.run(**inputs))
