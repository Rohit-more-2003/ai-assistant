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

# from_messages specifies that it is chat style prompt
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
            return None # return None instead of or error string
        
        result = eval(expression, {"__builtins__": None}, {})
        return str(result) # for clean response
    
    except:
        return None
    

def webSearch(user_input):
    try:
        # this is the DuckDuckGo Instant Answer API
        # No API key required, and returns Structured JSON
        url = "https://api.duckduckgo.com/"
        params = {
            "query": user_input,
            "format": "json"
        }

        res = requests.get(url, params=params) # search user input using api and parameters
        data = res.json()

        if data.get("AbstractText"):
            return data["AbstractText"]  # all abstract text
        
        elif data.get("RelatedTopics"):
            topics = data["RelatedTopics"][:3]  # related topics limited to 3
            results = []

            for t in topics:
                if "Text" in t:
                    results.append(t["Text"])

            return "\n".join(results)

    except:
        return None

# ------------- RESPONSE ROUTING -----------------
def route_request(user_input):
    """This function decides which tool to use for current task"""
    calc_res = simpleCalculator(user_input)
    if calc_res is not None:
        return calc_res
        
    # basic condition to choose web search tool  
    if any(word in user_input.lower() for word in ["search", "latest", "news", "when", "what is", "who is"]):
        search_result = webSearch(user_input)
        
        if search_result:
            return search_result

    return get_response(user_input)

# -------------- ROUTES ---------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    response = route_request(user_input)

    return jsonify({
        "response": response
    })

if __name__ == "__main__":
    app.run(debug=True)