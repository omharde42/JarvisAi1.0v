class JarvisBrain:
    def __init__(self, llm_service):
        self.llm = llm_service

    async def process(self, user_input: str):
        try:
            response = await self.llm.generate(user_input)
            return {
                "status": "success",
                "response": response
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            } 

