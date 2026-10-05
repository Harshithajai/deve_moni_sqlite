import json
import os
import re
from dotenv import load_dotenv
from groq import Groq

# Force load environment variables from backend/.env regardless of where execution starts
dotenv_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../.env")
)
load_dotenv(dotenv_path, override=True)


class LLMProviderError(Exception):
    """Custom exception raised when Groq API calls or JSON parsing fail."""

    pass


class GroqProvider:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise LLMProviderError(
                "GROQ_API_KEY environment variable is missing."
            )

        self.client = Groq(api_key=api_key)
        # Defaults to your supported active model
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate plain text completion using Groq."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMProviderError(f"Groq API call failed: {e}")

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Generate structured JSON completion using Groq native JSON mode with regex fallback."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            system_prompt
                            + "\n\nIMPORTANT: Respond in valid JSON format only."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw_text = response.choices[0].message.content
        except Exception as e:
            raise LLMProviderError(f"Groq API call failed during JSON gen: {e}")

        # Extract strictly the JSON object between curly braces if markdown formatting is present
        clean_text = raw_text.strip()
        json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group(0)

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise LLMProviderError(
                f"Failed to parse LLM JSON output: {e}\nRaw response was:\n{raw_text}"
            )