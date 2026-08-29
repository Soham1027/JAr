import json
import re

from app.brain.ollama_client import OllamaClient
from app.tools.system import open_application


SYSTEM_PROMPT = """
You are JARVIS, a personal AI assistant running locally on the user's computer.

Your personality:
- Helpful
- Intelligent
- Professional
- Natural
- Concise when possible

Current capabilities:
- Conversation
- Opening applications, files, folders, and URLs with the open_application tool

Important rules:
- When the user asks to open something, call open_application. Do not only describe how to open it.
- Never claim that you performed an action when you did not.
- Never invent information.
- If you do not know something, say so.
- Follow the user's instructions carefully.
- After a tool result, reply briefly with what happened.
"""


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": (
                "Open an application, file, folder, or URL on this Windows computer. "
                "Use this whenever the user wants something opened or launched."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": (
                            "What to open. Examples: chrome, notepad, vscode, "
                            "calculator, downloads, https://youtube.com, C:\\\\path\\\\file.pdf"
                        ),
                    }
                },
                "required": ["target"],
            },
        },
    }
]

OPEN_PATTERN = re.compile(
    r"""
    ^\s*
    (?:(?:hey|hi|hello|ok|okay)\s+)?
    (?:jarvis\s*[,:]?\s+)?
    (?:please\s+)?
    (?:can\s+you\s+|could\s+you\s+|would\s+you\s+)?
    (?:please\s+)?
    (?:open|launch|start)\s+
    (?P<target>.+?)
    [\s.!?]*
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)


class JarvisAgent:

    def __init__(self):

        self.llm = OllamaClient()

        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

    def ask(self, user_message: str) -> str:

        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        direct = self._direct_open(user_message)

        if direct is not None:
            self.messages.append(
                {
                    "role": "assistant",
                    "content": direct,
                }
            )
            return direct

        message = self.llm.chat(self.messages, tools=TOOLS)
        message = self._run_tools(message)

        response = (message.get("content") or "").strip()

        if not response:
            response = "I heard you."

        self.messages.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        return response

    def _direct_open(self, user_message: str) -> str | None:

        match = OPEN_PATTERN.match(user_message.strip())

        if not match:
            return None

        result = open_application(match.group("target"))
        return self._open_reply(result)

    def _run_tools(self, message: dict) -> dict:

        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            return message

        self.messages.append(message)

        for call in tool_calls:
            name, arguments = self._parse_tool_call(call)

            if name == "open_application":
                result = open_application(arguments.get("target", ""))
            else:
                result = {"ok": False, "error": f"Unknown tool: {name}"}

            self.messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )

        return self.llm.chat(self.messages, tools=TOOLS)

    def _parse_tool_call(self, call) -> tuple[str, dict]:

        if isinstance(call, dict):
            function = call.get("function") or {}
            name = function.get("name") or call.get("name") or ""
            arguments = function.get("arguments") or call.get("arguments") or {}
        else:
            function = getattr(call, "function", None)
            name = getattr(function, "name", "") if function else ""
            arguments = getattr(function, "arguments", {}) if function else {}

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"target": arguments}

        if not isinstance(arguments, dict):
            arguments = {}

        return name, arguments

    def _open_reply(self, result: dict) -> str:

        if result.get("ok"):
            label = result.get("label") or result.get("opened") or "it"
            return f"Opening {label}."

        return result.get("error") or "I could not open that."
