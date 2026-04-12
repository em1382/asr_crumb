import json
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import Settings
from app.models import FitRecommendationAgentOutput


_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "system_prompt.txt"
_SYSTEM_PROMPT = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()

prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", "{ingredients} {bread_type}"),
])

chain = None

# For demo purposes, we'll hardcode the Gemini 2.5 Flash model
AGENT_MODEL_NAME = "gemini-2.5-flash"


def configure(settings: Settings):
    """
    Configure the agent with FastAPI's settings.
    """
    api_key = settings.google_api_key
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set (required for the LLM).")

    global chain

    llm = ChatGoogleGenerativeAI(
        model=AGENT_MODEL_NAME,
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=api_key,
    )

    structured_llm = llm.with_structured_output(FitRecommendationAgentOutput)
    chain = prompt | structured_llm


def get_recipe_recommendations(recipe: dict) -> FitRecommendationAgentOutput:
    """Return structured output aligned with `fit_recommendation` table fields."""
    if chain is None:
        raise RuntimeError("Agent is not configured; call configure() during app startup.")
    return chain.invoke(
        {
            "ingredients": json.dumps(recipe["ingredients"]),
            "bread_type": recipe["recipe_name"],
        }
    )
