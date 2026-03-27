import { useState } from 'react';
import ChatWindow from './components/ChatWindow.jsx';

function App() {
  const [messages, setMessages] = useState([]);

  function focusChatInput() {
    const chatPanel = document.querySelector('.chat-panel');
    const input = document.getElementById('chat-input');

    chatPanel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    input?.focus();
  }

  return (
    <div className="app-shell">
      <div className="bg-orb orb-a" />
      <div className="bg-orb orb-b" />
      <div className="bg-grid" />

      <main className="layout">
        <section className="welcome-panel glass">
          <div className="welcome-content">
            <h1>Hey there 👋</h1>
            <p className="welcome-subtitle">
              I'm here to listen, understand, and support you. Share what's on your mind—judgment-free, always.
            </p>
            
            <div className="features">
              <div className="feature-item">
                <span className="feature-icon">💬</span>
                <div>
                  <h3>Real Conversation</h3>
                  <p>Natural, thoughtful dialogue tailored to your needs</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🤝</span>
                <div>
                  <h3>Empathetic Support</h3>
                  <p>Understanding your feelings and responding with care</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">💾</span>
                <div>
                  <h3>Remember Context</h3>
                  <p>I remember our conversations to give better help</p>
                </div>
              </div>
            </div>

            <div className="cta">
              <button type="button" className="cta-button" onClick={focusChatInput}>
                Start chatting now
              </button>
            </div>
          </div>
        </section>

        <section className="chat-panel glass">
          <ChatWindow messages={messages} setMessages={setMessages} />
        </section>
      </main>
    </div>
  );
}

export default App;
