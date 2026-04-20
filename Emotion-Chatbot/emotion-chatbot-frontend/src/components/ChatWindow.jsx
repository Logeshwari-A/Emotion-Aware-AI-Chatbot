import { useEffect, useRef, useState } from 'react';
import { sendMessage } from '../services/api.js';
import MessageBubble from './MessageBubble.jsx';
import VoiceInput from './VoiceInput.jsx';
import CallMode from './CallMode.jsx';
import VoiceSettings from './VoiceSettings.jsx';
import { useVoice } from '../hooks/useVoice.js';
import { useCallMode } from '../hooks/useCallMode.js';
import { translateEmotionToHuman, translateStrategyToHuman, translateRiskToHuman } from '../utils/emotionTranslator.js';
import { Phone, Lightbulb, Settings2, Trash2, SendHorizontal, Mic } from 'lucide-react';

function ChatWindow({ messages, setMessages }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [callMode, setCallMode] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [latestMetadata, setLatestMetadata] = useState(null);
  const [voiceSettings, setVoiceSettings] = useState({
    silenceTimeoutMs: 1000,
    preset: 'balanced',
  });
  const endRef = useRef(null);
  const voiceInputRef = useRef(null);
  const { isSpeaking, speak, stopSpeaking } = useVoice(voiceSettings);
  const {
    callState,
    duration,
    isMuted,
    speakerOn,
    callTranscript,
    formatDuration,
    startCall,
    endCall,
    toggleMute,
    toggleSpeaker,
    addToCallTranscript,
  } = useCallMode();
  const quickPrompts = [
    'I am feeling overwhelmed today.',
    'I had a great day and feel excited.',
    'I am anxious about my exams.'
  ];

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function onSend(overrideText = null) {
    // If TTS is speaking, stop it and listen for barge-in
    if (isSpeaking && voiceMode) {
      stopSpeaking();
    }

    const trimmed = (overrideText ?? text).trim();
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
        confidence: response.confidence || 0,
        risk_level: response.risk_level || 'low',
        safety_trigger: response.safety_trigger || false,
        crisis_resources: response.crisis_resources || [],
        reasoning_path: response.reasoning_path || {},
        ts: Date.now()
      };
      
      setMessages((prev) => [...prev, botMsg]);
      
      // Update Magic Mirror panel with latest metadata.
      setLatestMetadata({
        emotion: botMsg.emotion,
        confidence: botMsg.confidence,
        strategy: botMsg.strategy,
        risk_level: botMsg.risk_level,
        safety_trigger: botMsg.safety_trigger,
        crisis_resources: botMsg.crisis_resources,
        reasoning_path: botMsg.reasoning_path,
      });
      
      // If voice mode is active, speak the response
      if (voiceMode && response.response) {
        speak(response.response);
      }
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

  function handleVoiceTranscript(finalTranscript) {
    setText(finalTranscript || '');
  }

  function toggleVoiceMode() {
    if (isSpeaking) {
      stopSpeaking();
    }
    setVoiceMode(!voiceMode);
  }

  function startCallMode() {
    setCallMode(true);
    setVoiceMode(true);
    startCall();
  }

  function endCallMode() {
    endCall();
    // Keep call UI visible for 2s, then return to chat
    setTimeout(() => {
      setCallMode(false);
      setVoiceMode(false);
    }, 2000);
  }

  async function handleVoiceSend() {
    if (loading || isSpeaking) return;
    const captured = voiceInputRef.current?.stopAndGetTranscript?.() || text;
    const trimmed = (captured || '').trim();
    if (!trimmed) return;
    await onSend(trimmed);
    voiceInputRef.current?.clearCapturedText?.();
    if (voiceMode) {
      setTimeout(() => {
        voiceInputRef.current?.startListeningNow?.();
      }, 350);
    }
  }

  return (
    <div className="chat-wrap">
      <header className="chat-header">
        <div>
          <h2>Conversation Console</h2>
          <p>Emotion-aware response engine</p>
        </div>

        <div className="chat-actions">
          {!callMode && (
            <button
              type="button"
              className="start-call-button"
              onClick={startCallMode}
              disabled={loading || callMode}
              aria-label="Start phone call"
              title="Start a phone call"
            >
              <Phone size={16} aria-hidden="true" />
              Call
            </button>
          )}
          {!callMode && (
            <button
              type="button"
              className={`mirror-toggle ${panelOpen ? 'active' : ''}`}
              onClick={() => setPanelOpen(!panelOpen)}
              aria-label="Toggle Magic Mirror panel"
              title="Show emotional insights"
            >
              <Lightbulb size={16} aria-hidden="true" />
            </button>
          )}
          {!callMode && voiceMode && (
            <button
              type="button"
              className={`settings-toggle ${settingsOpen ? 'active' : ''}`}
              onClick={() => setSettingsOpen(!settingsOpen)}
              aria-label="Toggle voice settings"
              title="Adjust voice parameters"
            >
              <Settings2 size={16} aria-hidden="true" />
            </button>
          )}
          {!callMode && messages.length > 0 && (
            <button
              type="button"
              className="ghost-button"
              onClick={onClearChat}
              aria-label="Clear all chat messages"
            >
              <Trash2 size={15} aria-hidden="true" />
              Clear chat
            </button>
          )}
        </div>
      </header>

      {callMode && (
        <CallMode
          onEndCall={endCallMode}
          isLoading={loading}
          callState={callState}
          duration={duration}
          isMuted={isMuted}
          speakerOn={speakerOn}
          callTranscript={callTranscript}
          formatDuration={formatDuration}
          toggleMute={toggleMute}
          toggleSpeaker={toggleSpeaker}
          addToCallTranscript={addToCallTranscript}
        />
      )}

      {!callMode && panelOpen && latestMetadata && (
        <aside className="magic-mirror-panel" aria-label="Magic Mirror: Emotional insights">
          <div className="mirror-content">
            <h3>Your Emotional State</h3>
            <p className="mirror-insight">
              {translateEmotionToHuman(latestMetadata.emotion, latestMetadata.confidence)}
            </p>

            <hr className="mirror-divider" />

            <h4>How I'm responding</h4>
            <p className="mirror-strategy">
              {translateStrategyToHuman(latestMetadata.strategy)}
            </p>

            {latestMetadata.risk_level && latestMetadata.risk_level !== 'low' && (
              <>
                <hr className="mirror-divider" />
                <p className="mirror-risk">
                  {translateRiskToHuman(latestMetadata.risk_level)}
                </p>
              </>
            )}

            {latestMetadata.safety_trigger && latestMetadata.crisis_resources?.length > 0 && (
              <>
                <hr className="mirror-divider" />
                <h4>Immediate Support</h4>
                <div className="crisis-resources">
                  {latestMetadata.crisis_resources.map((resource, idx) => (
                    <div key={idx} className="resource-item">
                      <strong>{resource.title}:</strong> {resource.guidance}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </aside>
      )}

      {!callMode && settingsOpen && voiceMode && (
        <VoiceSettings
          settings={voiceSettings}
          onSettingsChange={setVoiceSettings}
          onClose={() => setSettingsOpen(false)}
        />
      )}

      {!callMode && (
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
          <MessageBubble 
            key={`${msg.ts}-${index}`} 
            message={msg}
            reasoning_path={msg.reasoning_path}
            risk_level={msg.risk_level}
            safety_trigger={msg.safety_trigger}
          />
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
      )}

      {!callMode && (
        <>
          {voiceMode ? (
            <div className="voice-mode-wrapper">
              <VoiceInput 
                ref={voiceInputRef}
                onTranscriptReady={handleVoiceTranscript}
                disabled={loading || isSpeaking}
                autoStart={voiceMode}
              />
              <form
                className="input-row voice-input-row"
                onSubmit={async (e) => {
                  e.preventDefault();
                  await handleVoiceSend();
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
                  placeholder="Voice or text message"
                  aria-label="Type or use voice"
                  disabled={isSpeaking}
                />
                <button
                  type="button"
                  className={`voice-mode-toggle voice-input-toggle ${voiceMode ? 'active' : ''}`}
                  onClick={toggleVoiceMode}
                  aria-label={voiceMode ? 'Disable voice mode' : 'Enable voice mode'}
                  title={voiceMode ? 'Switch to text mode' : 'Switch to voice mode'}
                >
                  <Mic size={16} aria-hidden="true" />
                </button>
                <button
                  type="submit"
                  disabled={!text.trim() || loading || isSpeaking}
                  aria-label={loading ? 'Sending message' : 'Send message'}
                  title="Stop listening and send"
                >
                  <SendHorizontal size={16} aria-hidden="true" />
                  {loading ? 'Sending...' : 'Send'}
                </button>
              </form>
            </div>
          ) : (
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
                type="button"
                className={`voice-mode-toggle voice-input-toggle ${voiceMode ? 'active' : ''}`}
                onClick={toggleVoiceMode}
                aria-label={voiceMode ? 'Disable voice mode' : 'Enable voice mode'}
                title={voiceMode ? 'Switch to text mode' : 'Switch to voice mode'}
              >
                <Mic size={16} aria-hidden="true" />
              </button>
              <button
                type="submit"
                disabled={!text.trim() || loading}
                aria-label={loading ? 'Sending message' : 'Send message'}
              >
                <SendHorizontal size={16} aria-hidden="true" />
                {loading ? 'Sending...' : 'Send'}
              </button>
            </form>
          )}
        </>
      )}
    </div>
  );
}

export default ChatWindow;
