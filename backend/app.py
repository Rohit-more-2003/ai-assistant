# -------------- IMPORTS ----------------

from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv
import os
import re
import json

import requests


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
    MessagesPlaceholder("history"),
    ("user", "{input}")
])


# -------------- Tools -----------------

@tool
def calculatorTool(expression: str) -> str:
    """This is math tool and returns only in string format"""
    try:
        expression = expression.replace(" ", "")

        if not re.match(r"[^0-9+\-*/().]+$"):
            return None
        
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    
    except:
        return None
    

@tool
def webSearchTool(query: str) -> str:
    """This is web search tool and return response in json format"""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "query": query,
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
    

# ----------- Memory/Chat History ---------------

def format_history(history):
    """Returns history as chatbot history sepered wrt role"""
    formatted = []

    for msg in history:
        if msg["role"] == "user":
            formatted.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            formatted.append(AIMessage(content=msg["content"]))

    return formatted


# -------------- AGENT EXECUTION -----------------

# ----- TOOL BINDING -----
tools = [calculatorTool, webSearchTool]
llm_with_tools = llm.bind_tools(tools)

def agent_execution(user_input, history):
    chain = prompt | llm_with_tools

    response = chain.invoke({
        "input": user_input,
        "history": history
    })
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]

        tool_name = tool_call["name"]
        tool_input = tool_call["args"]

        if tool_name == "calculatorTool":
            result = calculatorTool.invoke(tool_input)
        elif tool_name == "webSearchTool":
            result = webSearchTool.invoke(tool_input)
        else:
            result = "Unknown tool"
        
        final_response = chain.invoke({
            "input": f"Tool result: {result}",
            "history": history # contains latest user input too
        })
        

        return {
            "type": "tool+llm",
            "tool": tool_name,
            "response": final_response.content
        }
    
    return {
        "type": "llm",
        "response": response.content
    }



# -------------- ROUTES ---------------

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    user_input = data.get("message", "")
    history = data.get("history", [])

    formatted_history = format_history(history)

    result = agent_execution(user_input, formatted_history)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)