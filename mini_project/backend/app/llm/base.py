"""
Base interface for LLM providers.

The application uses this interface so that the rest of the
application does not depend directly on Groq.

A different LLM provider can be added later without changing
the observation analysis service.
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """
    Abstract base class for an LLM provider.

    Every LLM provider used by the application should implement
    the generate_json() method.
    """

    @abstractmethod
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> dict[str, Any]:
        """
        Send prompts to the LLM and return a JSON object.

        Parameters
        ----------
        system_prompt:
            Instructions describing how the LLM should behave.

        user_prompt:
            The caregiver observation that needs to be analyzed.

        Returns
        -------
        dict[str, Any]
            Structured information extracted by the LLM.

        Raises
        ------
        NotImplementedError
            If a subclass does not implement this method.
        """

        raise NotImplementedError