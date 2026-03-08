import './Message.css'

export default function Message({ role, text, error }) {
  const isUser = role === 'user'
  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <span className="message-label">
        {isUser ? 'YOU' : 'AI'}
      </span>
      <div className={`message-bubble ${error ? 'error' : ''}`}>
        {text}
      </div>
    </div>
  )
}
