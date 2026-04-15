// ------------------ IMPORTS ------------------
import { useState, useRef, useEffect } from "react";
import "./App.css"

// ------------------ COMPONENT ------------------
export default function App() {

  // ------------------ STATE ------------------
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem("chat");
    return saved ? JSON.parse(saved) : [];
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);

  // ------------------ FUNCTIONS ------------------
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);

    setLoading(true);

    try{  
      const res = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ 
          message: input.trim(),
          history: messages
        })
      });

      const data = await res.json();

      const aiMessage = { role: "ai", content: data.response };
      setMessages((prev) => [...prev, aiMessage]);
    }
    catch(err){
      setMessages((prev) => [
        ...prev,
        {role: "ai", content: "Error: Unable to connect to server."}
      ]);
    }

    setInput("");
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !loading){
      handleSend();
    }
  }

  const handleClear = () => {
    setMessages([]);
    localStorage.removeItem("chat");
  }

  // ----------------- Effects -----------------
  useEffect(() => {
    localStorage.setItem("chat", JSON.stringify(messages));
  }, [messages]);
  
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({behaviour: "smooth"});
  }, [messages]);

  // ------------------ UI ------------------
  return (
    <div className="container">
      <h1 className="title">AI Chat</h1>

      <div className="chat-box">
        {messages.map((msg, index) => (
          <div 
            key={index}
            className={msg.role === "user" ? "userMessage" : "aiMessage"}
          >
            {msg.content}
          </div>  
        ))}
        <div ref={chatEndRef}></div>
      </div>

      <div className="input-row">
        <input
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type message..."
          disabled={loading}
        />

        <button 
          className="button" 
          onClick={handleSend}
          disabled={loading}
        >
          {loading ? "Loading....." : "Enter"}
        </button>
      </div>

      <button className="button" onClick={handleClear}>
        Clear Chat
      </button>
    </div>
  );
};