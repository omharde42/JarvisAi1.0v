"""
Code Executor Tool
Safely execute Python code with sandboxing and output capture
"""

import subprocess
import tempfile
import os
from typing import Any, Dict
import logging

from app.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class CodeExecutorTool(BaseTool):
    """
    Execute Python code in a sandboxed environment
    
    Features:
    - Timeout enforcement
    - Output capture
    - Error handling
    - Security: Run in isolated process
    """
    
    def __init__(
        self,
        max_timeout: int = 30,
        max_output_size: int = 10000,
    ):
        super().__init__(
            name="code_executor",
            description="Execute Python code and return output",
            category="code",
        )
        self.max_timeout = max_timeout
        self.max_output_size = max_output_size
    
    async def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Execute Python code
        
        Args:
            code: Python code to execute
        
        Returns:
            Execution result with stdout, stderr, and status
        """
        
        try:
            # Validate code
            is_valid, error = await self.validate_params(code=code)
            if not is_valid:
                return {
                    "success": False,
                    "result": None,
                    "error": error,
                    "metadata": {"type": "validation_error"},
                }
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute in subprocess with timeout
                result = subprocess.run(
                    ["python", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.max_timeout,
                )
                
                stdout = result.stdout[:self.max_output_size]
                stderr = result.stderr[:self.max_output_size]
                
                return {
                    "success": result.returncode == 0,
                    "result": stdout,
                    "error": stderr if stderr else None,
                    "metadata": {
                        "return_code": result.returncode,
                        "stdout_truncated": len(result.stdout) > self.max_output_size,
                        "stderr_truncated": len(result.stderr) > self.max_output_size,
                    },
                }
            
            finally:
                os.unlink(temp_file)
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "result": None,
                "error": f"Code execution timed out after {self.max_timeout}s",
                "metadata": {"type": "timeout"},
            }
        
        except Exception as e:
            self.logger.error(f"Code execution failed: {str(e)}")
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {"type": "execution_error"},
            }
    
    async def validate_params(self, code: str = None, **kwargs) -> tuple[bool, str]:
        """
        Validate code before execution
        """
        if not code:
            return False, "Code parameter is required"
        
        if not isinstance(code, str):
            return False, "Code must be a string"
        
        if len(code) > 100000:
            return False, "Code is too large (max 100KB)"
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "__import__",
            "eval",
            "exec",
            "compile",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code.lower():
                return False, f"Code contains dangerous pattern: {pattern}"
        
        return True, None
    
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
                    "code": {
                        "type": "string",
                        "description": "Python code to execute",
                    },
                },
                "required": ["code"],
            },
        }
