"""
Tool Executor - Dynamic Tool Execution
Manages tool registry and safe execution
"""

import logging
from typing import Any, Dict, Optional, Callable, List
import asyncio
import json

from app.core.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)


class Tool:
    """
    Base tool interface
    """

    def __init__(
        self,
        name: str,
        description: str,
        execute_func: Callable,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.execute_func = execute_func
        self.parameters = parameters or {}

    def get_schema(self) -> Dict[str, Any]:
        """Return tool schema for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """
    Registry for all available tools
    """

    def __init__(self):
        """Initialize tool registry"""
        self.tools: Dict[str, Tool] = {}
        logger.info("✅ Tool Registry initialized")

    def register(self, tool: Tool) -> None:
        """
        Register a tool
        """
        self.tools[tool.name] = tool
        logger.info(f"📌 Registered tool: {tool.name}")

    def get(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name
        """
        return self.tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools with schemas
        """
        return [tool.get_schema() for tool in self.tools.values()]


class ToolExecutor:
    """
    Safe tool execution engine

    Features:
    - Tool registry management
    - Async execution
    - Error handling and fallback
    - Timeout protection
    - Execution logging
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize executor
        """
        self.registry = ToolRegistry()
        self.timeout = timeout
        logger.info(f"✅ Tool Executor initialized (timeout: {timeout}s)")

    def register_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a new tool
        """
        tool = Tool(
            name=name,
            description=description,
            execute_func=func,
            parameters=parameters,
        )
        self.registry.register(tool)

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a tool with given parameters

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters

        Returns:
            Execution result

        Raises:
            ToolExecutionError: If tool execution fails
        """
        try:
            # Get tool
            tool = self.registry.get(tool_name)
            if not tool:
                raise ToolExecutionError(
                    tool_name=tool_name,
                    message=f"Tool not found: {tool_name}",
                )

            logger.info(f"🔧 Executing tool: {tool_name}")

            # Execute with timeout
            try:
                if asyncio.iscoroutinefunction(tool.execute_func):
                    result = await asyncio.wait_for(
                        tool.execute_func(**parameters),
                        timeout=self.timeout,
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(tool.execute_func, **parameters),
                        timeout=self.timeout,
                    )

                logger.info(f"✅ Tool {tool_name} executed successfully")

                return {
                    "success": True,
                    "tool": tool_name,
                    "result": result,
                    "error": None,
                }

            except asyncio.TimeoutError:
                raise ToolExecutionError(
                    tool_name=tool_name,
                    message=f"Tool execution timed out after {self.timeout}s",
                )

        except ToolExecutionError:
            raise
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {str(e)}", exc_info=True)
            raise ToolExecutionError(
                tool_name=tool_name,
                message=str(e),
            )


# Global tool executor
tool_executor: Optional[ToolExecutor] = None


async def get_tool_executor() -> ToolExecutor:
    """
    Get or create global tool executor
    """
    global tool_executor
    if tool_executor is None:
        tool_executor = ToolExecutor()
        # Register default tools here
        await _register_default_tools(tool_executor)
    return tool_executor


async def _register_default_tools(executor: ToolExecutor) -> None:
    """
    Register built-in tools
    """

    # Simple calculator tool
    async def calculator(expression: str) -> str:
        """Evaluate mathematical expression"""
        try:
            result = eval(expression, {"__builtins__": {}})
            return str(result)
        except Exception as e:
            raise ToolExecutionError("calculator", str(e))

    executor.register_tool(
        name="calculator",
        description="Perform mathematical calculations",
        func=calculator,
        parameters={
            "expression": "Mathematical expression to evaluate",
        },
    )

    # Echo tool (for testing)
    async def echo(message: str) -> str:
        """Echo back a message"""
        return message

    executor.register_tool(
        name="echo",
        description="Echo back a message (for testing)",
        func=echo,
        parameters={
            "message": "Message to echo",
        },
    )

    logger.info("✅ Default tools registered")
