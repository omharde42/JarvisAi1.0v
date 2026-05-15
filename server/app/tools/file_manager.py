"""
File Manager Tool
Handle file operations (read, write, delete, list)
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from app.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class FileManagerTool(BaseTool):
    """
    Manage files and directories
    
    Features:
    - Read/write files
    - List directories
    - Create/delete files
    - Path validation and sandboxing
    """
    
    def __init__(self, sandbox_dir: str = "/tmp/jarvis"):
        super().__init__(
            name="file_manager",
            description="Manage files and directories",
            category="system",
        )
        self.sandbox_dir = Path(sandbox_dir)
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    async def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute file operation
        
        Args:
            operation: read, write, list, delete, create_dir
            path: File path (relative to sandbox)
            content: File content (for write operation)
        """
        
        try:
            # Validate path
            full_path = self._validate_path(path)
            if not full_path:
                return {
                    "success": False,
                    "result": None,
                    "error": "Invalid path or outside sandbox",
                    "metadata": {"operation": operation},
                }
            
            if operation == "read":
                return await self._read_file(full_path)
            
            elif operation == "write":
                return await self._write_file(full_path, content)
            
            elif operation == "list":
                return await self._list_directory(full_path)
            
            elif operation == "delete":
                return await self._delete_file(full_path)
            
            elif operation == "create_dir":
                return await self._create_directory(full_path)
            
            else:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Unknown operation: {operation}",
                    "metadata": {},
                }
        
        except Exception as e:
            self.logger.error(f"File operation failed: {str(e)}")
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {"operation": operation},
            }
    
    def _validate_path(self, path: str) -> Optional[Path]:
        """
        Validate and sanitize file path
        Ensure it's within sandbox directory
        """
        try:
            full_path = (self.sandbox_dir / path).resolve()
            
            # Check if path is within sandbox
            if not str(full_path).startswith(str(self.sandbox_dir)):
                return None
            
            return full_path
        
        except Exception:
            return None
    
    async def _read_file(self, path: Path) -> Dict[str, Any]:
        """
        Read file content
        """
        if not path.exists():
            return {
                "success": False,
                "result": None,
                "error": f"File not found: {path.name}",
                "metadata": {},
            }
        
        try:
            content = path.read_text()
            return {
                "success": True,
                "result": content,
                "error": None,
                "metadata": {"size": len(content)},
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {},
            }
    
    async def _write_file(self, path: Path, content: str) -> Dict[str, Any]:
        """
        Write content to file
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            
            return {
                "success": True,
                "result": f"File written: {path.name}",
                "error": None,
                "metadata": {"size": len(content)},
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {},
            }
    
    async def _list_directory(self, path: Path) -> Dict[str, Any]:
        """
        List directory contents
        """
        if not path.exists():
            path = self.sandbox_dir
        
        try:
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
            
            return {
                "success": True,
                "result": items,
                "error": None,
                "metadata": {"count": len(items)},
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {},
            }
    
    async def _delete_file(self, path: Path) -> Dict[str, Any]:
        """
        Delete file
        """
        if not path.exists():
            return {
                "success": False,
                "result": None,
                "error": f"File not found: {path.name}",
                "metadata": {},
            }
        
        try:
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
            
            return {
                "success": True,
                "result": f"Deleted: {path.name}",
                "error": None,
                "metadata": {},
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {},
            }
    
    async def _create_directory(self, path: Path) -> Dict[str, Any]:
        """
        Create directory
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "result": f"Directory created: {path.name}",
                "error": None,
                "metadata": {},
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {},
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for LLM function calling
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "delete", "create_dir"],
                        "description": "File operation",
                    },
                    "path": {
                        "type": "string",
                        "description": "File path (relative to sandbox)",
                    },
                    "content": {
                        "type": "string",
                        "description": "File content (for write operation)",
                    },
                },
                "required": ["operation", "path"],
            },
        }
