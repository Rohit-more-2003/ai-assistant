# -------------- IMPORTS ----------------
from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv
import os
import re
import json

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


def calculatorTool(user_input):
    """This is math tool and returns only in string format"""
    try:
        expression = user_input.replace(" ", "")

        if not re.match(r"[^0-9+\-*/().]+$"):
            return None
        
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    
    except:
        return None
    

def webSearchTool(user_input):
    """This is web search tool and return response in json format"""
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
    
# ----------------- ROUTING COMPONENTS ----------------

# --------- SEARCH TRIGGERS ---------
# Temporal triggers (time-sensitive)
TEMPORAL_KEYWORDS = ["latest", "current", "recent", "today", "now","live", "updated", 
    "newest", "this week", "this month", "2026"]

# Event-based triggers
EVENT_KEYWORDS = ["news", "headlines", "score", "weather", "stock", "price", "exchange rate", "standings"]

# Action-based triggers
ACTION_KEYWORDS = ["search", "find", "lookup", "look up", "check", "verify", "confirm", "research"]

# Phrase-based triggers
PHRASE_KEYWORDS = ["is it true", "what happened", "where can i buy"]

# ------- TOOL DEFINITION FOR LLM -------
TOOLS_DESCRIPTION = """
You have access to the following tools:

1. calculatorTool
    - Use for mathematical expressions
    - Input: a valid math expression(e.g. '2+2', '10//5')
    
2. webSearchTool
    - Use for current events, recent info or factual lookup
    - Use when question involves latest data, news, or verification

Instructions:
    - If a tool is needed, respond only in JSON format:
    {
        "tool": "calculatorTool" or "webSearchTool"
        "input": "user_input"
    }

    - If no tool is needed, respond:
    {
        "tool": "none"
    }
"""
    

# ------------- RESPONSE ROUTING -----------------
def shouldUseSearch(user_input):
    """This function checks if web search tool should be used for given task"""
    text = user_input.lower()

    # if any trigger word found return True
    for word in TEMPORAL_KEYWORDS+EVENT_KEYWORDS+ACTION_KEYWORDS:
        if word in text:
            return True
        
    for phrase in PHRASE_KEYWORDS:
        if phrase in text:
            return True
        
    return False # if not, return False


def tool_decided_with_llm(user_input):
    """This is llm decision function which tool is to be used"""

    decision_prompt = f"""
{TOOLS_DESCRIPTION}

Important:
    - Respond ONLY with JSON format
    - Do not add explanation

User input:
{user_input}
"""
    
    response = llm.invoke(decision_prompt)

    try:
        decision = json.loads(response.content)
        return decision
    except:
        return {"tool": "none"}


def route_request(user_input):
    """This function decides which tool to use for current task"""

    # 1. calculator (fast rule)
    calc_res = calculatorTool(user_input)
    if calc_res is not None:
        return {
            "type": "tool",
            "tool": "calculator",
            "response": calc_res
        }
    
    # 2. web search (fast filter)
    if shouldUseSearch(user_input):
        search_result = webSearchTool(user_input)
        
        if search_result:
            combined_input = f"Use this  information:\n{search_result}\n\nAnswer: {user_input}"
            response = get_response(combined_input)

            return {
                "type": "tool+llm",
                "tool": "web search",
                "response": response
            }
        
    # 3. LLM decides tool (for complex cases)
    decision = tool_decided_with_llm(user_input)
    tool = decision.get("tool")

    if tool == "calculatorTool":
        result = calculatorTool(decision.get("input", user_input))
        if result:
            return {
                "type": "llm+tool",
                "tool": "calculator",
                "response": result
            }
    elif tool == "webSearchTool":
        result = webSearchTool(decision.get("input", user_input))
        if result:
            return {
                "type": "llm+tool",
                "tool": "web search",
                "response": result
            }

    # 4. Default
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