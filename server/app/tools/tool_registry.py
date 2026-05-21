class ToolRegistry:
    """
    Registers available tools
    """

    def __init__(self):
        self.tools = {
            "calculator": self.calculator,
            "web_search": self.web_search,
        }

    async def calculator(self, query: str):
        return f"Calculator executed: {query}"

    async def web_search(self, query: str):
        return f"Search executed: {query}"

    async def execute(self, tool_name: str, query: str):
        tool = self.tools.get(tool_name)

        if not tool:
            return f"Tool '{tool_name}' not found"

        return await tool(query)
