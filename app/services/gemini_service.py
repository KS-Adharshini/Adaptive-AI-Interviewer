import os
import json
import re
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from ..config import GEMINI_API_KEY, GEMINI_MODEL
from ..utils.helpers import setup_logger

logger = setup_logger("GeminiService")

T = TypeVar("T", bound=BaseModel)

class GeminiServiceError(Exception):
    """Custom exception for Gemini API errors to protect UI from stack traces."""
    pass

class GeminiService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
        self.model_name = model or os.getenv("GEMINI_MODEL", GEMINI_MODEL)
        self._client: Optional[genai.Client] = None

    def is_configured(self) -> bool:
        """Check if a valid API key format is present."""
        return bool(self.api_key and len(self.api_key.strip()) > 10 and not self.api_key.startswith("your_"))

    def _get_client(self) -> genai.Client:
        """Instantiate client lazily with the configured API key."""
        if not self.is_configured():
            raise GeminiServiceError(
                "Gemini API key is not configured. Please add your GEMINI_API_KEY in the .env file or Settings tab."
            )
        if self._client is None:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                raise GeminiServiceError(f"Failed to initialize Gemini client: {str(e)}")
        return self._client

    def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.4
    ) -> Any:
        """
        Generate structured output adhering to a Pydantic schema using Gemini.
        Safely strips markdown wrappers and validates with the schema.
        """
        client = self._get_client()
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json"
        )
        if schema is not None:
            config.response_schema = schema

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            raw_text = response.text or ""
            
            # Clean up potential markdown code block markers
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```"):
                cleaned_text = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned_text)
                cleaned_text = re.sub(r"\n?```$", "", cleaned_text).strip()

            if schema is not None:
                try:
                    return schema.model_validate_json(cleaned_text)
                except Exception as parse_err:
                    logger.warning(f"Direct schema validation failed: {parse_err}. Attempting json loads fallback.")
                    data = json.loads(cleaned_text)
                    return schema.model_validate(data)
            
            return json.loads(cleaned_text)
        except genai.errors.APIError as api_err:
            logger.error(f"Gemini API Error: {api_err}")
            if "RESOURCE_EXHAUSTED" in str(api_err) or "429" in str(api_err):
                raise GeminiServiceError("Gemini API rate limit reached. Please wait a moment before trying again.")
            raise GeminiServiceError(f"Gemini API Error: {str(api_err)}")
        except Exception as e:
            logger.error(f"Error during Gemini generation: {e}")
            raise GeminiServiceError(f"Failed to generate structured response: {str(e)}")

    def test_connection(self) -> bool:
        """Test if the API key and model connection are valid."""
        if not self.is_configured():
            return False
        try:
            client = self._get_client()
            res = client.models.generate_content(
                model=self.model_name,
                contents="Ping",
                config=types.GenerateContentConfig(max_output_tokens=10)
            )
            return bool(res and res.text)
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False
