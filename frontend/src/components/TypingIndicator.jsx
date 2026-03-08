import './TypingIndicator.css'

export default function TypingIndicator() {
  return (
    <div className="message-row assistant">
      <span className="message-label">AI</span>
      <div className="typing-bubble">
        <span className="dot" style={{ animationDelay: '0ms' }} />
        <span className="dot" style={{ animationDelay: '160ms' }} />
        <span className="dot" style={{ animationDelay: '320ms' }} />
      </div>
    </div>
  )
}
