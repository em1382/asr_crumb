from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import Settings

import json


prompt = ChatPromptTemplate.from_messages([
    ("system", "You not say many words. No personality. Good baker. You read JSON containing bread ingredients. You tell me bread good or bread bad based on type of bread. If bread bad, you tell how fix."),
    ("human", "{ingredients}"),
])

chain = None

def configure(settings: Settings):
    """
    Configure the agent with FastAPI's settings.
    """
    api_key = settings.google_api_key
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set (required for the LLM).")

    global chain

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=api_key,
    )

    chain = prompt | llm


def get_recipe_recommendations(recipe: dict) -> list[dict]:
    """ Get recipe recommendations from the model. """
    return chain.invoke({
        "ingredients": json.dumps(recipe["ingredients"])
    })
