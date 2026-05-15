"""
Base Tool Class
Abstract base for all tools in the system
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all tools
    
    A tool is a capability that can be called by agents to perform specific actions:
    - Code execution
    - File operations
    - Browser control
    - System commands
    - API calls
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str = "general",
        requires_auth: bool = False,
    ):
        """
        Initialize base tool
        
        Args:
            name: Unique tool identifier
            description: Human-readable description
            category: Tool category (code, browser, system, api, etc.)
            requires_auth: Whether tool requires authentication
        """
        self.name = name
        self.description = description
        self.category = category
        self.requires_auth = requires_auth
        self.logger = logging.getLogger(f"tools.{name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters
        
        Returns:
            Result dictionary with:
            {
                "success": bool,
                "result": Any,
                "error": Optional[str],
                "metadata": Dict
            }
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for tool (for LLM function calling)
        
        Returns:
            Schema with name, description, parameters
        """
        pass
    
    async def validate_params(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters before execution
        
        Returns:
            (is_valid, error_message)
        """
        return True, None
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get tool information
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "requires_auth": self.requires_auth,
            "schema": self.get_schema(),
        }


class ToolRegistry:
    """
    Registry for managing available tools
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.logger = logger
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool
        """
        if tool.name in self.tools:
            self.logger.warning(f"Tool {tool.name} already registered, overwriting")
        
        self.tools[tool.name] = tool
        self.logger.info(f"✅ Registered tool: {tool.name}")
    
    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"Unregistered tool: {tool_name}")
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name
        """
        return self.tools.get(tool_name)
    
    def get_all(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools
        """
        return self.tools.copy()
    
    def get_by_category(self, category: str) -> List[BaseTool]:
        """
        Get tools by category
        """
        return [tool for tool in self.tools.values() if tool.category == category]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all tools with their info
        """
        return [tool.get_info() for tool in self.tools.values()]
