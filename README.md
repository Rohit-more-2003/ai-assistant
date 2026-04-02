# 🤖 Agentic AI Chat App (React + Flask + LLM)

A full-stack AI chatbot application built using **React (frontend)** and **Flask (backend)**, powered by an LLM with basic **tool routing (calculator + web search)** to simulate an **agentic AI system**.

---

## 🚀 Features

* 💬 Interactive chat UI (React)
* 🧠 LLM-powered responses (Google Gemini via LangChain)
* 🧮 Built-in calculator tool
* 🌐 Web search tool (DuckDuckGo API)
* 🔀 Intelligent routing between tools and LLM
* 💾 Chat persistence using localStorage
* ⚡ Fast and lightweight architecture

---

## ⚙️ Tech Stack

### Frontend

* React (Vite)
* Fetch API
* LocalStorage

### Backend

* Flask
* LangChain
* Google Generative AI (Gemini)
* DuckDuckGo API

---

## 🧠 How It Works (Agent Logic)

The backend implements a simple **agentic routing system**:

### 1. Calculator Tool

* Detects mathematical expressions
* Safely evaluates using `eval()`
* Returns result instantly

### 2. Web Search Tool

* Triggered by keywords like:

  * `latest`, `news`, `today`, `price`, etc.
* Uses DuckDuckGo API
* Extracts:

  * Abstract
  * Related topics

### 3. LLM (Fallback / Core Brain)

* Handles general queries
* Enhances search results using prompt injection

### 🔀 Routing Flow

```text
User Input
   ↓
[Check Calculator]
   ↓
[Check Search Trigger]
   ↓
[LLM Response]
```

---

## 🔧 Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/agentic-ai-chat.git
cd agentic-ai-chat
```

---

### 2️⃣ Backend Setup (Flask)

```bash
cd backend
pip install -r requirements.txt
```

#### Create `.env` file

```text
GEMINI_API_KEY=your_api_key_here
```

#### Run server

```bash
python app.py
```

Server runs on:

```url
http://127.0.0.1:5000
```

---

### 3️⃣ Frontend Setup (React)

```bash
cd frontend
npm install
npm run dev
```

App runs on:

```url
http://localhost:5173
```

---

## 🔌 API Endpoint

### POST `/chat`

#### Request

```json
{
  "message": "What is 5 + 10?"
}
```

#### Response

```json
{
  "response": "15"
}
```

---

## 📸 UI Overview

* Chat history display
* Input box with Enter key support
* Loading state handling
* Clear chat button
* Auto-scroll to latest message

---

## ⚠️ Limitations

* Basic keyword-based routing (not true autonomous agent)
* DuckDuckGo API has limited structured results
* No streaming responses
* No memory/context beyond current message
* `eval()` used (safe but still minimal validation)

---

## 🔮 Future Improvements

* ✅ Replace keyword routing with LLM-based tool selection
* ✅ Add conversation memory
* ✅ UI improvements (Markdown, code highlighting)
* ✅ Authentication & user sessions
* ✅ Deployment (Docker + Cloud)
