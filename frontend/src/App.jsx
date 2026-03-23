// ------------------ IMPORTS ------------------
import { useState } from "react";

// ------------------ COMPONENT ------------------
export default function App() {

  // ------------------ STATE ------------------
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  // ------------------ FUNCTIONS ------------------
  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);  // prev react provided variable, here, prev = previous state value of messages 

    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message: input })
    });

    const data = await res.json();

    const aiMessage = { role: "ai", content: data.response };
    setMessages((prev) => [...prev, aiMessage]);

    setInput("");
  };

  // ------------------ UI ------------------
  return (
    <div style={{ padding: "20px" }}>
      <h1>AI Chat</h1>

      <div>
        {messages.map((msg, index) => (
          <div key={index}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type message..."
      />

      <button onClick={handleSend}>Send</button>
    </div>
  );
};