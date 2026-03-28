# -------------- IMPORTS ----------------
from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv
import os
import re

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

# -------------- FUNCTIONS -----------------
def get_response(user_input):
    response = chain.invoke({"input": user_input})

    return response.content


def simpleCalculator(user_input):
    try:
        result = eval(user_input)
        return result
    except:
        return "Invalid Calculation"

# ------------- RESPONSE ROUTING -----------------
def route_request(user_input):
    """This function decides which tool to use for current task"""
    # Basic simple math expression
    if re.match(r"^[0-9+\-*/(). ]+$", user_input):
        return simpleCalculator(user_input)

    return get_response(user_input)

# -------------- ROUTES ---------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "") # this means that get message if it exists or get default (here "")

    response = route_request(user_input)

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)