// src/components/Message.jsx
import './Message.css'

export default function Message({ role, text, error, isThinking }) {
  const isUser = role === 'user'
  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <span className="message-label">
        {isUser ? 'YOU' : 'AI'}
      </span>
      <div className={`message-bubble ${error ? 'error' : ''} ${isThinking ? 'thinking' : ''}`}>
        {text}
      </div>
    </div>
  )
}