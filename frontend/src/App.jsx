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
    // ---- FIX #12: `loading` check already existed; added `disabled` on the
    //      button itself (see JSX below) so it is visually + functionally blocked.
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input.trim() };

    // Snapshot history BEFORE adding current user message so the backend
    // does not receive the current turn twice.
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
          message: userMessage.content,
          history: historyBeforeThisTurn
        })
      });

      const data = await res.json();

      // ---- FIX #9: Guard against missing / falsy `data.response` ----
      // Before: content: data.response  →  could be undefined, null, or ""
      // After:  fall back to a user-facing message so the bubble is never blank.
      const responseText =
        data?.response && typeof data.response === "string" && data.response.trim()
          ? data.response.trim()
          : "No response received. Please try again.";

      setMessages(prev => [
        ...prev,
        {
          role: "ai",
          content: responseText,
          tool: data?.tool || null
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

        {/* ---- FIX #12: `disabled` prop prevents clicks AND triggers browser/CSS
              disabled styling automatically. The label also shifts to "..." so the
              user gets visual feedback that a request is in flight. ---- */}
        <button onClick={handleSend} disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </div>

    </div>
  );
}