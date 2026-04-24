"""
LLM Service
Integration with multiple LLM providers (OpenAI, Google Gemini, Anthropic Claude)
"""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum

import openai
import anthropic
import google.generativeai as genai


logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider enumeration"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"


class LLMModel(str, Enum):
    """LLM model enumeration"""
    # OpenAI
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Google Gemini
    GEMINI_PRO = "gemini-pro"
    GEMINI_VISION = "gemini-pro-vision"
    
    # Claude
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class LLMService:
    """
    LLM Service for AI reasoning and response generation
    Supports multiple providers with fallback capability
    """
    
    def __init__(self,
                 openai_api_key: Optional[str] = None,
                 gemini_api_key: Optional[str] = None,
                 claude_api_key: Optional[str] = None):
        """
        Initialize LLM service
        
        Args:
            openai_api_key: OpenAI API key
            gemini_api_key: Google Gemini API key
            claude_api_key: Anthropic Claude API key
        """
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        self.claude_api_key = claude_api_key
        
        # Initialize clients
        if openai_api_key:
            openai.api_key = openai_api_key
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        
        self.claude_client = None
        if claude_api_key:
            self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
    
    # ========================================================================
    # OpenAI Chat Completion
    # ========================================================================
    
    async def chat_openai(self,
                         messages: List[Dict[str, str]],
                         model: str = "gpt-4",
                         temperature: float = 0.7,
                         max_tokens: int = 2000,
                         functions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Chat completion with OpenAI
        
        Args:
            messages: Chat messages
            model: Model to use
            temperature: Temperature (0-2)
            max_tokens: Maximum tokens in response
            functions: Optional function calling schema
        
        Returns:
            Response dictionary with content and metadata
        """
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if functions:
                kwargs["functions"] = functions
                kwargs["function_call"] = "auto"
            
            response = openai.ChatCompletion.create(**kwargs)
            
            choice = response.choices[0]
            content = choice.message.get("content") or ""
            
            result = {
                "provider": "openai",
                "model": model,
                "content": content,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": choice.finish_reason,
            }
            
            # Handle function calling
            if "function_call" in choice.message:
                result["function_call"] = choice.message["function_call"]
            
            logger.info(f"✅ OpenAI chat: {response.usage.total_tokens} tokens")
            return result
        
        except Exception as e:
            logger.error(f"❌ OpenAI chat failed: {e}")
            raise
    
    # ========================================================================
    # Google Gemini Chat
    # ========================================================================
    
    async def chat_gemini(self,
                         messages: List[Dict[str, str]],
                         model: str = "gemini-pro",
                         temperature: float = 0.7,
                         max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Chat completion with Google Gemini
        
        Args:
            messages: Chat messages
            model: Model to use
            temperature: Temperature (0-2)
            max_tokens: Maximum tokens in response
        
        Returns:
            Response dictionary
        """
        try:
            genai_model = genai.GenerativeModel(model)
            
            # Convert to Gemini format
            chat_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                chat_messages.append({
                    "role": role,
                    "parts": msg["content"]
                })
            
            response = genai_model.generate_content(
                contents=chat_messages[-1]["parts"],  # Send last message
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
                stream=False,
            )
            
            result = {
                "provider": "gemini",
                "model": model,
                "content": response.text,
                "tokens_used": 0,  # Gemini doesn't provide token count in response
                "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN",
            }
            
            logger.info(f"✅ Gemini chat: {response.text[:100]}...")
            return result
        
        except Exception as e:
            logger.error(f"❌ Gemini chat failed: {e}")
            raise
    
    # ========================================================================
    # Claude Chat
    # ========================================================================
    
    async def chat_claude(self,
                         messages: List[Dict[str, str]],
                         model: str = "claude-3-opus-20240229",
                         temperature: float = 0.7,
                         max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Chat completion with Claude
        
        Args:
            messages: Chat messages
            model: Model to use
            temperature: Temperature (0-1)
            max_tokens: Maximum tokens in response
        
        Returns:
            Response dictionary
        """
        try:
            response = self.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
            
            content = response.content[0].text if response.content else ""
            
            result = {
                "provider": "claude",
                "model": model,
                "content": content,
                "tokens_used": response.usage.output_tokens + response.usage.input_tokens,
                "finish_reason": response.stop_reason,
            }
            
            logger.info(f"✅ Claude chat: {response.usage.output_tokens} tokens")
            return result
        
        except Exception as e:
            logger.error(f"❌ Claude chat failed: {e}")
            raise
    
    # ========================================================================
    # Generic Chat Interface
    # ========================================================================
    
    async def chat(self,
                  messages: List[Dict[str, str]],
                  provider: LLMProvider = LLMProvider.OPENAI,
                  model: Optional[str] = None,
                  temperature: float = 0.7,
                  max_tokens: int = 2000,
                  functions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generic chat interface with provider selection
        
        Args:
            messages: Chat messages
            provider: LLM provider to use
            model: Model to use (uses default if None)
            temperature: Temperature setting
            max_tokens: Maximum tokens
            functions: Optional function calling schema
        
        Returns:
            Response dictionary
        """
        if provider == LLMProvider.OPENAI:
            model = model or "gpt-4"
            return await self.chat_openai(messages, model, temperature, max_tokens, functions)
        elif provider == LLMProvider.GEMINI:
            model = model or "gemini-pro"
            return await self.chat_gemini(messages, model, temperature, max_tokens)
        elif provider == LLMProvider.CLAUDE:
            model = model or "claude-3-opus-20240229"
            return await self.chat_claude(messages, model, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    # ========================================================================
    # Embeddings
    # ========================================================================
    
    async def get_embeddings_openai(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """
        Get embeddings using OpenAI
        
        Args:
            texts: Texts to embed
            model: Embedding model
        
        Returns:
            List of embedding vectors
        """
        try:
            response = openai.Embedding.create(
                input=texts,
                model=model,
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
        
        except Exception as e:
            logger.error(f"❌ OpenAI embeddings failed: {e}")
            raise
    
    async def get_embeddings_gemini(self, texts: List[str], model: str = "embedding-001") -> List[List[float]]:
        """
        Get embeddings using Google Gemini
        
        Args:
            texts: Texts to embed
            model: Embedding model
        
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model=f"models/{model}",
                    content=text,
                )
                embeddings.append(result["embedding"])
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
        
        except Exception as e:
            logger.error(f"❌ Gemini embeddings failed: {e}")
            raise
    
    async def get_embeddings(self,
                            texts: List[str],
                            provider: LLMProvider = LLMProvider.OPENAI) -> List[List[float]]:
        """
        Get embeddings with provider selection
        
        Args:
            texts: Texts to embed
            provider: Provider to use
        
        Returns:
            List of embedding vectors
        """
        if provider == LLMProvider.OPENAI:
            return await self.get_embeddings_openai(texts)
        elif provider == LLMProvider.GEMINI:
            return await self.get_embeddings_gemini(texts)
        else:
            raise ValueError(f"Embeddings not supported for provider: {provider}")
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    async def check_provider_status(self) -> Dict[str, str]:
        """Check status of all configured providers"""
        status = {}
        
        # OpenAI
        if self.openai_api_key:
            try:
                openai.Model.list()
                status["openai"] = "✅ Available"
            except Exception as e:
                status["openai"] = f"❌ {str(e)}"
        else:
            status["openai"] = "⚠️ Not configured"
        
        # Gemini
        if self.gemini_api_key:
            status["gemini"] = "✅ Available"
        else:
            status["gemini"] = "⚠️ Not configured"
        
        # Claude
        if self.claude_api_key:
            try:
                self.claude_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
                status["claude"] = "✅ Available"
            except Exception as e:
                status["claude"] = f"❌ {str(e)}"
        else:
            status["claude"] = "⚠️ Not configured"
        
        return status
