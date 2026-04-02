# -------------- IMPORTS ----------------
from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv
import os
import re

import requests # for web search

# --------------- SETUP ----------------------

load_dotenv()

app = Flask(__name__)
CORS(app=app)   

gemini_key = os.getenv("GEMINI_API_KEY")
llm_model = "gemini-2.5-flash-lite"

system_prompt = """
    You are a helpful AI assistant.
    Give clear, concise, and accurate answers.
    Keep responses short and easy to understand.
    Add references to the website if necessary.
"""

# --------------- LLM -----------------
llm = ChatGoogleGenerativeAI(
    model=llm_model,
    google_api_key=gemini_key,
    temperature=0.3
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | llm

# -------------- Tools -----------------
def get_response(user_input):
    response = chain.invoke({
            "input": user_input
        })

    return response.content


def simpleCalculator(user_input):
    """This is math tool for given ai"""
    try:
        expression = user_input.replace(" ", "")

        if not re.match(r"[^0-9+\-*/().]+$"):
            return None
        
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    
    except:
        return None
    

def webSearch(user_input):
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "query": user_input,
            "format": "json"
        }

        res = requests.get(url, params=params)
        data = res.json()

        if data.get("AbstractText"):
            return data["AbstractText"]
        
        elif data.get("RelatedTopics"):
            topics = data["RelatedTopics"][:3]
            results = []

            for t in topics:
                if "Text" in t:
                    results.append(t["Text"])

            return "\n".join(results)

    except:
        return None

# ------------- RESPONSE ROUTING -----------------
def shouldUseSearch(user_input):
    """This function checks if web search tool should be used for given task"""
    # ------------------ SEARCH TRIGGERS ------------------
    # Temporal triggers (time-sensitive)
    TEMPORAL_KEYWORDS = ["latest", "current", "recent", "today", "now","live", "updated", 
        "newest", "this week", "this month", "2026"]

    # Event-based triggers
    EVENT_KEYWORDS = ["news", "headlines", "score", "weather", "stock", "price", "exchange rate", "standings"]

    # Action-based triggers
    ACTION_KEYWORDS = ["search", "find", "lookup", "look up", "check", "verify", "confirm", "research"]

    # Phrase-based triggers
    PHRASE_KEYWORDS = ["is it true", "what happened", "where can i buy"]

    text = user_input.lower()

    # if any trigger word found return True
    for word in TEMPORAL_KEYWORDS+EVENT_KEYWORDS+ACTION_KEYWORDS:
        if word in text:
            return True
        
    for phrase in PHRASE_KEYWORDS:
        if phrase in text:
            return True
        
    return False # if not, return False


def route_request(user_input):
    """This function decides which tool to use for current task"""
    calc_res = simpleCalculator(user_input)
    if calc_res is not None:
        return {
            "type": "tool",
            "tool": "calculator",
            "response": calc_res
        }
    
    if shouldUseSearch(user_input):
        search_result = webSearch(user_input)
        
        if search_result:
            combined_input = f"Use this  information:\n{search_result}\n\nAnswer: {user_input}"
            response = get_response(combined_input)

            return {
                "type": "tool+llm",
                "tool": "web search",
                "response": response
            }

    llm_response = get_response(user_input)
    return {
        "type": "llm",
        "response": llm_response
    }

# -------------- ROUTES ---------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    result = route_request(user_input)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)