from typing import List

from .augmented_llm_openai import OpenAIAugmentedLLM
from .intent_classifier import Intent
from .intent_classifier_llm import LLMIntentClassifier

CLASSIFIER_SYSTEM_INSTRUCTION = """
You are a precise intent classifier that analyzes input requests to determine their intended action or purpose.
You are provided with a request and a list of intents to choose from.
You can choose one or more intents, or choose none if no intent is appropriate.
"""


class OpenAILLMIntentClassifier(LLMIntentClassifier):
    """
    An LLM router that uses an OpenAI model to make routing decisions.
    """

    def __init__(
        self,
        intents: List[Intent],
        classification_instruction: str | None = None,
    ):
        openai_llm = OpenAIAugmentedLLM(instruction=CLASSIFIER_SYSTEM_INSTRUCTION)

        super().__init__(
            llm=openai_llm,
            intents=intents,
            classification_instruction=classification_instruction,
        )