import json
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from backend.fs_tools import read_file, list_files, write_file, search_in_file


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and extract text from resume files (PDF, TXT, DOCX)",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory with optional extension filter",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list files from"
                    },
                    "extension": {
                        "type": "string",
                        "description": "Optional file extension filter (e.g., '.pdf', '.txt')"
                    }
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a text file, creating directories if needed",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to write to"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search for keywords in file content",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "File to search in"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to find (case-insensitive)"
                    }
                },
                "required": ["filepath", "keyword"]
            }
        }
    }
]

TOOL_ARGUMENT_NAMES = {
    schema["function"]["name"]: set(schema["function"]["parameters"]["properties"])
    for schema in TOOL_SCHEMAS
}

SYSTEM_PROMPT = (
    "You are a local file-system assistant. Use the provided tools when file "
    "information is needed. Base your final answer only on tool results and do "
    "not claim that a file was written unless the write_file tool was actually "
    "called successfully. Use only these exact tool names: read_file, "
    "list_files, write_file, search_in_file. Do not invent tool names such as "
    "load, open, find, or search. To search a folder, first call list_files, "
    "then call search_in_file for each relevant filepath returned by list_files."
)

TOOL_USE_RETRY_PROMPT = (
    "Your previous tool call was invalid. Try again using only these exact "
    "tools: read_file, list_files, write_file, search_in_file. Tool arguments "
    "must be valid JSON objects matching the tool schema."
)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Call the LLM with a list of messages.

        Args:
            messages: List of messages in OpenAI format

        Returns:
            Response dict with role, content, and optional tool_calls
        """
        pass

    def format_tool_result(self, tool_name: str, result: Any) -> str:
        """Format tool result for inclusion in messages."""
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        return str(result)

    def format_assistant_message(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Format an assistant response for conversation history."""
        return {
            "role": "assistant",
            "content": response.get("content", "")
        }

    def format_tool_message(self, tool_call: Dict[str, Any], tool_name: str, result: Any) -> Dict[str, Any]:
        """Format a tool result for conversation history."""
        return {
            "role": "user",
            "content": f"Tool call result for {tool_name}:\n{self.format_tool_result(tool_name, result)}"
        }


class OpenAICompatibleProvider(LLMProvider):
    """Shared message formatting for OpenAI-compatible chat APIs."""

    def format_assistant_message(self, response: Dict[str, Any]) -> Dict[str, Any]:
        message = {
            "role": "assistant",
            "content": response.get("content", "")
        }
        if response.get("tool_calls"):
            message["tool_calls"] = response["tool_calls"]
        return message

    def format_tool_message(self, tool_call: Dict[str, Any], tool_name: str, result: Any) -> Dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": self.format_tool_result(tool_name, result)
        }


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai library not installed. Run: pip install openai")

    def call(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call OpenAI API with tool support."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto"
        )

        result = {
            "role": "assistant",
            "content": response.choices[0].message.content or ""
        }

        if response.choices[0].message.tool_calls:
            result["tool_calls"] = []
            for tool_call in response.choices[0].message.tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

        return result


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic library not installed. Run: pip install anthropic")

    def call(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call Anthropic API with tool support."""
        tools = self._convert_to_anthropic_format(TOOL_SCHEMAS)
        system_prompt = "\n\n".join(
            message["content"]
            for message in messages
            if message["role"] == "system"
        )
        anthropic_messages = [
            message
            for message in messages
            if message["role"] != "system"
        ]

        request = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
            "tools": tools
        }
        if system_prompt:
            request["system"] = system_prompt

        response = self.client.messages.create(**request)

        result = {
            "role": "assistant",
            "content": ""
        }

        tool_calls = []

        for block in response.content:
            if hasattr(block, "text"):
                result["content"] = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input)
                    }
                })

        if tool_calls:
            result["tool_calls"] = tool_calls

        return result

    def _convert_to_anthropic_format(self, schemas: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool format to Anthropic format."""
        anthropic_tools = []

        for schema in schemas:
            func = schema["function"]
            anthropic_tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": {
                    "type": "object",
                    "properties": func["parameters"]["properties"],
                    "required": func["parameters"]["required"]
                }
            })

        return anthropic_tools


class GroqProvider(OpenAICompatibleProvider):
    """Groq LLM provider implementation (FREE tier available)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.1-8b-instant",
        max_tokens: int = 1024
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable.")

        try:
            from groq import BadRequestError, Groq
            self.client = Groq(api_key=self.api_key)
            self.BadRequestError = BadRequestError
            self._fallback_tool_call_counter = 0
        except ImportError:
            raise ImportError("groq library not installed. Run: pip install groq")

    def call(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call Groq API with tool support."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                max_tokens=self.max_tokens
            )
        except self.BadRequestError as e:
            parsed_tool_call = self._parse_failed_tool_call(e)
            if parsed_tool_call:
                return parsed_tool_call
            raise

        result = {
            "role": "assistant",
            "content": response.choices[0].message.content or ""
        }

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            result["tool_calls"] = []
            for tool_call in tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

        return result

    def _parse_failed_tool_call(self, error: Exception) -> Optional[Dict[str, Any]]:
        """
        Recover Groq tool calls when the API rejects a nearly-valid generation.

        Some Groq-hosted models can generate a function call in text form, such as:
        <function=list_files{"directory": "sample_data/resumes"}</function>
        or:
        <function=search_in_file({"filepath": "resume.txt", "keyword": "Python"})</function>
        or:
        <function=search_in_file [{"filepath": "resume.txt", "keyword": "Python"}]</function>
        The API returns this as a tool_use_failed error instead of structured
        tool_calls. Parsing it lets the local agent loop continue.
        """
        failed_generation = None
        body = getattr(error, "body", None)

        if isinstance(body, dict):
            error_body = body.get("error", body)
            failed_generation = error_body.get("failed_generation")

        if not failed_generation:
            match = re.search(r"'failed_generation':\s*'(.+?)'\s*}", str(error), re.DOTALL)
            if match:
                failed_generation = match.group(1)

        if not failed_generation:
            return None

        match = re.search(
            r"<function=([A-Za-z_][A-Za-z0-9_]*)\s*>?\s*(.*?)(?:</function>|(?=\s*<function=)|$)",
            failed_generation,
            re.DOTALL,
        )
        if not match:
            return None

        tool_name, payload = match.groups()
        arguments = self._extract_json_payload(payload)
        if not arguments:
            return None

        try:
            tool_args = json.loads(arguments)
        except json.JSONDecodeError:
            return None

        if isinstance(tool_args, list) and tool_args and isinstance(tool_args[0], dict):
            tool_args = tool_args[0]

        if not isinstance(tool_args, dict):
            return None

        allowed_args = TOOL_ARGUMENT_NAMES.get(tool_name)
        if allowed_args:
            tool_args = {
                key: value
                for key, value in tool_args.items()
                if key in allowed_args
            }

        self._fallback_tool_call_counter += 1

        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": f"groq_failed_generation_{self._fallback_tool_call_counter}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_args)
                    }
                }
            ]
        }

    def _extract_json_payload(self, text: str) -> Optional[str]:
        """Extract the first balanced JSON object or array from generated text."""
        start = None
        opener = None

        for index, char in enumerate(text):
            if char in "{[":
                start = index
                opener = char
                break

        if start is None or opener is None:
            return None

        closer = "}" if opener == "{" else "]"
        stack = [closer]
        in_string = False
        escape = False

        for index in range(start + 1, len(text)):
            char = text[index]

            if escape:
                escape = False
                continue

            if char == "\\" and in_string:
                escape = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char in "{[":
                stack.append("}" if char == "{" else "]")
            elif stack and char == stack[-1]:
                stack.pop()
                if not stack:
                    return text[start:index + 1]

        return None


class FileAssistant:
    """Main assistant that orchestrates file operations with LLM tool calling."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.tool_functions = {
            "read_file": read_file,
            "list_files": list_files,
            "write_file": write_file,
            "search_in_file": search_in_file
        }

    def run(self, user_query: str, max_iterations: int = 10) -> str:
        """
        Run the assistant with a user query.

        Args:
            user_query: User's natural language query
            max_iterations: Maximum number of tool calls to allow

        Returns:
            Final response from the LLM
        """
        result = self.run_with_trace(user_query, max_iterations)
        return result.get("response", "")

    def run_with_trace(self, user_query: str, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run the assistant and return the final response plus tool call details.

        This is used by the web API so the frontend can show which tools ran,
        while run() keeps the original string-only interface for CLI/tests.
        """
        direct_result = self._run_direct_intent(user_query)
        if direct_result:
            return direct_result

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_query
            }
        ]

        tool_calls_made = []

        for iteration in range(max_iterations):
            try:
                response = self.provider.call(messages)
            except Exception as e:
                if not self._is_retryable_tool_error(e):
                    raise
                retry_messages = messages + [
                    {
                        "role": "user",
                        "content": TOOL_USE_RETRY_PROMPT
                    }
                ]
                response = self.provider.call(retry_messages)

            messages.append(self.provider.format_assistant_message(response))

            if "tool_calls" not in response or not response["tool_calls"]:
                return {
                    "success": True,
                    "response": response.get("content", ""),
                    "tool_calls": tool_calls_made
                }

            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])

                if isinstance(tool_args, list) and tool_args and isinstance(tool_args[0], dict):
                    tool_args = tool_args[0]

                if not isinstance(tool_args, dict):
                    tool_result = f"Invalid arguments for {tool_name}: expected an object"
                    tool_calls_made.append({
                        "tool": tool_name,
                        "input": tool_args,
                        "result": tool_result
                    })
                    messages.append(self.provider.format_tool_message(tool_call, tool_name, tool_result))
                    continue

                allowed_args = TOOL_ARGUMENT_NAMES.get(tool_name)
                if allowed_args:
                    tool_args = {
                        key: value
                        for key, value in tool_args.items()
                        if key in allowed_args
                    }

                if tool_name not in self.tool_functions:
                    tool_result = f"Unknown tool: {tool_name}"
                else:
                    try:
                        tool_func = self.tool_functions[tool_name]
                        tool_result = tool_func(**tool_args)
                    except TypeError as e:
                        tool_result = f"Error calling {tool_name}: {str(e)}"
                    except Exception as e:
                        tool_result = f"Error executing {tool_name}: {str(e)}"

                tool_calls_made.append({
                    "tool": tool_name,
                    "input": tool_args,
                    "result": tool_result
                })
                messages.append(self.provider.format_tool_message(tool_call, tool_name, tool_result))

        return {
            "success": False,
            "response": "Maximum iterations reached without completion.",
            "error": "Maximum iterations reached without completion.",
            "tool_calls": tool_calls_made
        }

    def _is_retryable_tool_error(self, error: Exception) -> bool:
        """Retry only provider errors caused by malformed model tool calls."""
        error_text = str(error)
        return (
            "tool_use_failed" in error_text
            or "Failed to call a function" in error_text
            or "failed_generation" in error_text
        )

    def _run_direct_intent(self, user_query: str) -> Optional[Dict[str, Any]]:
        """Handle common demo file queries without spending LLM tokens."""
        directory = self._extract_directory(user_query)
        query_lower = user_query.lower()

        if directory and "list" in query_lower:
            extension = ".txt" if ".txt" in query_lower or "resume" in query_lower else None
            files = list_files(directory, extension)
            filenames = [file["filename"] for file in files]
            response = (
                f"Found {len(files)} file(s) in {directory}:\n"
                + "\n".join(f"- {filename}" for filename in filenames)
            )
            return {
                "success": True,
                "response": response,
                "tool_calls": [
                    {
                        "tool": "list_files",
                        "input": {"directory": directory, "extension": extension},
                        "result": files
                    }
                ]
            }

        keyword = self._extract_search_keyword(user_query)
        is_folder_search = (
            directory
            and keyword
            and ("search" in query_lower or "find" in query_lower or "mention" in query_lower)
            and ("across" in query_lower or "all" in query_lower or "resume" in query_lower)
        )

        if is_folder_search:
            files = [
                file for file in list_files(directory, ".txt")
                if file["filename"].startswith("resume_")
            ]
            tool_calls = [
                {
                    "tool": "list_files",
                    "input": {"directory": directory, "extension": ".txt"},
                    "result": files
                }
            ]
            matching_files = []

            for file in files:
                search_result = search_in_file(file["filepath"], keyword)
                tool_calls.append({
                    "tool": "search_in_file",
                    "input": {"filepath": file["filepath"], "keyword": keyword},
                    "result": search_result
                })

                if search_result.get("success") and search_result.get("match_count", 0) > 0:
                    matching_files.append({
                        "filename": file["filename"],
                        "match_count": search_result["match_count"],
                        "matches": search_result["matches"][:3]
                    })

            if not matching_files:
                response = f"No resume files in {directory} mention '{keyword}'."
            else:
                lines = [
                    f"Found '{keyword}' in {len(matching_files)} resume file(s):"
                ]
                for match in matching_files:
                    lines.append(f"- {match['filename']}: {match['match_count']} match(es)")
                    for item in match["matches"]:
                        lines.append(f"  Line {item['line_number']}: {item['match_text']}")
                response = "\n".join(lines)

            return {
                "success": True,
                "response": response,
                "tool_calls": tool_calls
            }

        return None

    def _extract_directory(self, user_query: str) -> Optional[str]:
        """Extract the sample resume directory from a natural-language query."""
        match = re.search(r"sample_data/resumes/?", user_query)
        if match:
            return "sample_data/resumes"
        return None

    def _extract_search_keyword(self, user_query: str) -> Optional[str]:
        """Extract a simple quoted or unquoted keyword from search/find prompts."""
        quoted = re.search(r"['\"]([^'\"]+)['\"]", user_query)
        if quoted:
            return quoted.group(1).strip()

        match = re.search(
            r"(?:search for|find|mentioning|mentions)\s+([A-Za-z0-9+#._-]+)",
            user_query,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

        return None
