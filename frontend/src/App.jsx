// src/App.jsx
import { useState, useRef, useEffect } from 'react'
import Message from './components/Message'
import TypingIndicator from './components/TypingIndicator'
import './App.css'

const USER_ID = 'user_' + Math.random().toString(36).slice(2, 9)

export default function App() {
  const [messages, setMessages]         = useState([
    { role: 'assistant', text: 'Bereit. Was möchtest du wissen?' }
  ])
  const [input, setInput]               = useState('')
  const [loading, setLoading]           = useState(false)
  const [streaming, setStreaming]       = useState(false)
  const [useReasoning, setUseReasoning] = useState(false)
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function handleStreamEvent(msg) {
    switch (msg.type) {

      case 'reasoning':
        // Reasoning-Text in die Blase schreiben — als "thinking"
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          updated[updated.length - 1] = {
            ...last,
            thinking: `▸ goal: ${msg.goal}\n▸ intent: ${msg.intent}\n▸ complexity: ${msg.complexity}\n▸ key points: ${msg.key_points.join(', ')}`,
          }
          return updated
        })
        break

      case 'planning':
        // Plan an Thinking-Text anhängen
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          const steps = msg.steps.map(s => s.action).join(', ')
          updated[updated.length - 1] = {
            ...last,
            thinking: (last.thinking || '') + `\n▸ plan: ${steps}`,
          }
          return updated
        })
        break

      case 'token':
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          updated[updated.length - 1] = {
            ...last,
            // Erster Token → thinking wegwerfen, finale Antwort beginnt
            thinking: null,
            text: last.text + msg.value,
          }
          return updated
        })
        break

      default:
        console.warn('Unbekannter Event-Typ:', msg.type)
    }
  }

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading || streaming) return

    setMessages(prev => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id:       USER_ID,
          message:       text,
          use_reasoning: useReasoning,
        }),
      })

      if (!res.ok) throw new Error(`Server error ${res.status}`)

      setLoading(false)
      setStreaming(true)

      // Leere Blase — nimmt erst thinking, dann finale Antwort
      setMessages(prev => [...prev, { role: 'assistant', text: '', thinking: null }])

      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      let   buffer  = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            handleStreamEvent(JSON.parse(line))
          } catch {
            console.warn('Kein valides JSON:', line)
          }
        }
      }

    } catch (err) {
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.role === 'assistant' && last.text === '') {
          updated[updated.length - 1] = {
            role: 'assistant', text: `Fehler: ${err.message}`, error: true,
          }
        } else {
          updated.push({ role: 'assistant', text: `Fehler: ${err.message}`, error: true })
        }
        return updated
      })
    } finally {
      setLoading(false)
      setStreaming(false)
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
        <label className="reasoning-toggle">
          <input
            type="checkbox"
            checked={useReasoning}
            onChange={e => setUseReasoning(e.target.checked)}
          />
          reasoning
        </label>
      </header>

      <main className="messages">
        {messages.map((msg, i) => (
          <Message
            key={i}
            role={msg.role}
            text={msg.thinking ?? msg.text}
            error={msg.error}
            isThinking={!!msg.thinking}
          />
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
          disabled={loading || streaming}
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={!input.trim() || loading || streaming}
        >
          ▸
        </button>
      </footer>
    </div>
  )
}