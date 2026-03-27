import { useEffect, useRef, useState } from 'react';
import { sendMessage } from '../services/api.js';
import MessageBubble from './MessageBubble.jsx';

function ChatWindow({ messages, setMessages }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);
  const quickPrompts = [
    'I am feeling overwhelmed today.',
    'I had a great day and feel excited.',
    'I am anxious about my exams.'
  ];

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function onSend() {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    // Prevent multiple sends
    setLoading(true);

    const userMsg = { sender: 'user', text: trimmed, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setText('');

    try {
      const response = await sendMessage(trimmed, 'user1');
      
      // Ensure we have valid response data
      if (!response || !response.response) {
        throw new Error('Invalid response from backend');
      }
      
      const botMsg = {
        sender: 'bot',
        text: response.response,
        strategy: response.strategy || 'normal_mode',
        emotion: response.detected_emotion || null,
        ts: Date.now()
      };
      
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      
      const errorMsg = {
        sender: 'bot',
        text: 'Unable to reach backend right now. Please verify the API server is running on port 8000.',
        strategy: 'system_warning',
        ts: Date.now()
      };
      
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }

  function onClearChat() {
    if (loading) return;
    setMessages([]);
    setText('');
    document.getElementById('chat-input')?.focus();
  }

  function applyQuickPrompt(promptText) {
    if (loading) return;
    setText(promptText);
    document.getElementById('chat-input')?.focus();
  }

  return (
    <div className="chat-wrap">
      <header className="chat-header">
        <div>
          <h2>Conversation Console</h2>
          <p>Emotion-aware response engine</p>
        </div>

        <div className="chat-actions">
          {messages.length > 0 && (
            <button
              type="button"
              className="ghost-button"
              onClick={onClearChat}
              aria-label="Clear all chat messages"
            >
              Clear chat
            </button>
          )}
          <span className="status-dot" aria-label="Backend connection status: live">Live</span>
        </div>
      </header>

      <div className="message-list" aria-live="polite" aria-busy={loading}>
        {messages.length === 0 && (
          <div className="empty-state">
            <h3>Start your first message</h3>
            <p>
              Try: "I am feeling overwhelmed today" or "I had a great day" to see adaptive strategy responses.
            </p>

            <div className="quick-prompts" aria-label="Quick prompt actions">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="quick-prompt-button"
                  onClick={() => applyQuickPrompt(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <MessageBubble key={`${msg.ts}-${index}`} message={msg} />
        ))}

        {loading && (
          <div className="typing-row">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form
        className="input-row"
        onSubmit={(e) => {
          e.preventDefault();
          onSend();
        }}
      >
        <label className="sr-only" htmlFor="chat-input">Message input</label>
        <textarea
          id="chat-input"
          value={text}
          rows={1}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder="Type your message and press Enter"
          aria-label="Type your message"
        />
        <button
          type="submit"
          disabled={!text.trim() || loading}
          aria-label={loading ? 'Sending message' : 'Send message'}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

export default ChatWindow;
