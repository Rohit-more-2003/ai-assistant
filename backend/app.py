# -------------- IMPORTS ----------------

from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from dotenv import load_dotenv
import os
import re


# --------------- SETUP ----------------------

load_dotenv()

app = Flask(__name__)
CORS(app=app)

gemini_key = os.getenv("GEMINI_API_KEY")
llm_model = "gemini-2.5-flash"

system_prompt = """
    You are an autonomous AI assistant that provides detailed and interconnected information. 
    When given a sequence of related concepts, explain each concept and then draw a logical connection between them, 
    elaborating on their relationship. 
    Prioritize historical, scientific, or cultural links. 
    Keep responses informative and flowing and keep the answer between 0-10 lines.
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
    """Evaluate a mathematical expression with operators like +, -, *, /, ().
    Only use for expressions with actual numbers, not word problems."""

    try:
        expression = expression.replace(" ", "")

        if not re.match(r"^[0-9+\-*/().]+$", expression):
            return "Invalid Calculation"

        result = eval(expression, {"__builtins__": None}, {})
        return str(result)

    except:
        return "Calculation error"


@tool
def webSearchTool(query: str) -> str:
    """Search the web for current events, news, or facts you don't already know.
    Do NOT use for general knowledge, definitions, or simple math."""

    try:
        tavily = TavilySearchResults(
            max_results=3,
            tavily_api_key=os.getenv("TAVILY_API_KEY")
        )

        results = tavily.invoke(query)

        if not results:
            return "No results found"

        formatted = []
        for r in results:
            url = r.get("url", "")
            content = r.get("content", "").strip()
            formatted.append(f"Source: {url}\n{content}")

        return "\n\n---\n\n".join(formatted)

    except Exception as e:
        # FIX 1: Print full error to terminal so you can see what's going wrong
        print(f"[webSearchTool ERROR]: {str(e)}")
        raise   # Re-raise so agent_execution catches it and returns a proper error


# ----------- Memory/Chat History ---------------

def format_history(history):
    """Converts frontend message list to LangChain message objects.
    Frontend sends history WITHOUT the current user message,
    so no stripping needed here.
    """
    formatted = []

    for msg in history:
        if msg["role"] == "user":
            formatted.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            formatted.append(AIMessage(content=msg["content"]))

    return formatted


# -------------- HELPERS -----------------

def extract_text(content) -> str:
    """FIX 2: Gemini 2.5 Flash with thinking mode returns .content as a LIST
    of parts (thinking block + text block) instead of a plain string.
    This extracts only the final text part, ignoring thinking tokens.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        # Each part has a 'type' — we want 'text', not 'thinking'
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text", "")
        # Fallback: join all string parts
        return " ".join(p.get("text", "") for p in content if isinstance(p, dict))

    return str(content)


# -------------- AGENT EXECUTION -----------------

tools = [calculatorTool, webSearchTool]
llm_with_tools = llm.bind_tools(tools)

TOOL_MAP = {
    "calculatorTool": calculatorTool,
    "webSearchTool": webSearchTool,
}


def agent_execution(user_input, history):
    try:
        chain = prompt | llm_with_tools

        response = chain.invoke({
            "input": user_input,
            "history": history
        })

        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]
            tool_input = tool_call["args"]

            selected_tool = TOOL_MAP.get(tool_name)

            try:
                result = selected_tool.invoke(tool_input) if selected_tool else "Unknown tool"
            except Exception as tool_err:
                # FIX 1: Tool failed — return a clean user-facing error immediately
                # instead of passing the error string to the LLM (which causes blank output)
                print(f"[Tool execution ERROR]: {str(tool_err)}")
                return {
                    "type": "tool+llm",
                    "tool": tool_name,
                    "response": f"Sorry, the {tool_name} encountered an error: {str(tool_err)}. Please try again."
                }

            context_message = (
                f"The user asked: {user_input}\n\n"
                f"You used the {tool_name} and got this result:\n{result}\n\n"
                f"Now answer the user's question based on this information."
            )

            follow_up_messages = (
                [SystemMessage(content=system_prompt)]
                + history
                + [HumanMessage(content=context_message)]
            )

            final_response = llm.invoke(follow_up_messages)

            # FIX 2: Extract plain text from response (handles thinking mode list content)
            response_text = extract_text(final_response.content)

            return {
                "type": "tool+llm",
                "tool": tool_name,
                "response": response_text
            }

        # FIX 2: Also extract text for direct LLM responses
        response_text = extract_text(response.content)

        return {
            "type": "llm",
            "response": response_text
        }

    except Exception as e:
        print(f"[agent_execution ERROR]: {str(e)}")
        return {
            "type": "error",
            "response": "Something went wrong on the server. Please try again."
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