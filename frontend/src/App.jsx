import { useState } from "react";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessages = [
      ...messages,
      { role: "user", content: input },
      { role: "ai", content: "This is an example" }
    ];

    setMessages(newMessages);
    setInput("");
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>AI Chatbot</h1>

      <div style={{ marginBottom: "20px" }}>
        {messages.map((msg, index) => (
          <div key={index}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
      </div>

      <input 
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
      />

      <button onClick={handleSend}>Send</button>
    </div>
  );
}