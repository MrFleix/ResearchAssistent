import { useState, useRef, useEffect } from 'react'
import Message from './components/Message'
import TypingIndicator from './components/TypingIndicator'
import './App.css'

const USER_ID = 'user_' + Math.random().toString(36).slice(2, 9)

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Bereit. Was möchtest du wissen?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading) return

    setMessages(prev => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, message: text }),
      })

      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      const reply = data.output?.response ?? 'Keine Antwort erhalten.'
      setMessages(prev => [...prev, { role: 'assistant', text: reply }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: `Fehler: ${err.message}`, error: true }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="layout">
      <header className="header">
        <span className="header-logo">▸ WORKFLOW</span>
        <span className="header-status">
          <span className="status-dot" />
          localhost:8000
        </span>
      </header>

      <main className="messages">
        {messages.map((msg, i) => (
          <Message key={i} role={msg.role} text={msg.text} error={msg.error} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <textarea
          ref={inputRef}
          className="input-field"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Nachricht eingeben — Enter zum Senden"
          rows={1}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={!input.trim() || loading}
        >
          ▸
        </button>
      </footer>
    </div>
  )
}
