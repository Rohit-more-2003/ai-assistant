// ------------------ IMPORTS ------------------
import { useState, useRef, useEffect } from "react";
import "./App.css"

// ------------------ COMPONENT ------------------
export default function App() {

  // ------------------ STATE ------------------
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);

  // ----------------- EFFECTS -----------------

  // --- Load from localstorage ---
  useEffect(() => {
    const saved = localStorage.getItem("chat");
    if (saved) {
      setMessages(JSON.parse(saved));
    }
  }, []);

  // --- Save to localstorage ---
  useEffect(() => {
    localStorage.setItem("chat", JSON.stringify(messages));
  }, [messages]);

  // --- Auto Scroll ---
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  // ------------------ FUNCTIONS ------------------
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input.trim() };

    // FIX: snapshot history BEFORE adding current user message.
    // This is sent as "history" to the backend so the current user
    // message is not duplicated (it's already sent separately as "message").
    const historyBeforeThisTurn = [...messages];

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: userMessage.content,       // current user input
          history: historyBeforeThisTurn      // past messages only, no duplicate
        })
      });

      const data = await res.json();

      setMessages(prev => [
        ...prev,
        {
          role: "ai",
          content: data.response,
          tool: data.tool || null
        }
      ]);
    } catch (err) {
      console.error("Error: ", err);
      setMessages(prev => [
        ...prev,
        {
          role: "ai",
          content: "Something went wrong. Please try again.",
          tool: null
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    localStorage.removeItem("chat");
  };


  // ------------------ UI ------------------
  return (
    <div className="container">

      <div className="header">
        <h2>AI Assistant</h2>
        <button onClick={handleClear} className="clear-btn">Clear Chat</button>
      </div>

      <div className="chat-box">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>

            <div className="bubble">
              {msg.content}
            </div>

            {msg.tool && (
              <div className="tool-tag">
                used: {msg.tool}
              </div>
            )}

          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="bubble">Typing...</div>
          </div>
        )}

        <div ref={chatEndRef}></div>
      </div>

      <div className="input-row">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend}>Send</button>
      </div>

    </div>
  );
}