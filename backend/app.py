from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv
import os

# -------------- SETUP ----------------
load_dotenv()

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

prompt = ChatPromptTemplate([
    ("system", system_prompt),
    (MessagesPlaceholder(variable_name="history")),
    ("user", "{input}")
])

chain = prompt | llm

# -------------- CHATBOT ---------------
print("AI: Hi, I am your personal assistant, how can I help you today?")

history = []
while True:
    user_input = input("You: ")
    if user_input == "exit":
        break

    response = chain.invoke({
        "input": user_input,
        "history": history
    })

    print(f"AI: {response.content}")

    history.append(HumanMessage(content=user_input))
    history.append(AIMessage(content=response.content))

    # print(f"History: {history}")