import { useState } from 'react';
import ChatWindow from './components/ChatWindow.jsx';
import { MessageSquareText, Handshake, Database, Sparkles } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState([]);
  const [showIntroModal, setShowIntroModal] = useState(true);

  function focusChatInput() {
    const chatPanel = document.querySelector('.chat-panel');
    const input = document.getElementById('chat-input');

    chatPanel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    input?.focus();
  }

  function handleStartSession() {
    setShowIntroModal(false);
    setTimeout(() => {
      focusChatInput();
    }, 120);
  }

  return (
    <div className={`app-shell ${showIntroModal ? 'onboarding-open' : ''}`}>
      <div className="bg-orb orb-a" />
      <div className="bg-orb orb-b" />
      <div className="bg-grid" />

      <main className="layout layout-chat-only">
        <section className="chat-panel glass">
          <ChatWindow messages={messages} setMessages={setMessages} />
        </section>
      </main>

      {showIntroModal && (
        <div className="intro-modal" role="dialog" aria-modal="true" aria-label="Welcome and start session">
          <div className="intro-backdrop" />
          <section className="intro-card glass">
            <div className="welcome-content">
              <h1>Conversation Workspace</h1>
              <p className="welcome-subtitle">
                A focused AI space for emotionally aware conversations, contextual memory, and safety-first support.
              </p>

              <div className="features">
                <div className="feature-item">
                  <span className="feature-icon" aria-hidden="true"><MessageSquareText size={20} /></span>
                  <div>
                    <h3>Real Conversation</h3>
                    <p>Natural, thoughtful dialogue tailored to your needs</p>
                  </div>
                </div>
                <div className="feature-item">
                  <span className="feature-icon" aria-hidden="true"><Handshake size={20} /></span>
                  <div>
                    <h3>Empathetic Support</h3>
                    <p>Understanding your feelings and responding with care</p>
                  </div>
                </div>
                <div className="feature-item">
                  <span className="feature-icon" aria-hidden="true"><Database size={20} /></span>
                  <div>
                    <h3>Remember Context</h3>
                    <p>I remember our conversations to give better help</p>
                  </div>
                </div>
              </div>

              <div className="cta">
                <button type="button" className="cta-button" onClick={handleStartSession}>
                  <Sparkles size={16} aria-hidden="true" />
                  Start Session
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default App;
