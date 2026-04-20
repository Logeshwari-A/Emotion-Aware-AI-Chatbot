/**
 * CallMode: Phone call interface with status, controls, and transcript
 */

import { useEffect, useState } from 'react';
import { useVoice } from '../hooks/useVoice.js';
import { sendMessage } from '../services/api.js';

function CallMode({
  onEndCall,
  isLoading,
  callState,
  duration,
  isMuted,
  speakerOn,
  callTranscript,
  formatDuration,
  toggleMute,
  toggleSpeaker,
  addToCallTranscript,
}) {
  const {
    startListening,
    stopListening,
    transcript,
    interimTranscript,
    isListening,
    isSpeaking,
    speak,
    error,
    clearError,
    retryListening,
    clearTranscript,
  } = useVoice({
    // Keep listening stable in call mode and avoid early auto-finalization.
    silenceTimeoutMs: 2500,
    maxUtteranceDurationMs: 90000,
    minUtteranceDurationMs: 300,
  });

  const [localLoading, setLocalLoading] = useState(false);
  const [pendingSubmit, setPendingSubmit] = useState(false);

  useEffect(() => {
    if (callState !== 'connected') {
      stopListening();
      clearError();
      clearTranscript();
      setPendingSubmit(false);
    }
  }, [callState, stopListening, clearError, clearTranscript]);

  useEffect(() => {
    if (isMuted) {
      stopListening();
      setPendingSubmit(false);
    }
  }, [isMuted, stopListening]);

  useEffect(() => {
    // Submit only after user explicitly clicks "Done Speaking" and recognition has stopped.
    if (!pendingSubmit || isListening || callState !== 'connected') {
      return;
    }

    const text = (transcript || interimTranscript || '').trim();
    setPendingSubmit(false);

    if (!text) {
      clearError();
      return;
    }

    const run = async () => {
      setLocalLoading(true);
      try {
        addToCallTranscript('user', text);
        const response = await sendMessage(text, 'user1');
        const reply = response?.response || 'I am here with you. Could you repeat that once?';
        addToCallTranscript('bot', reply);
        if (speakerOn) {
          speak(reply);
        }
      } catch (e) {
        addToCallTranscript('bot', 'Connection issue right now. Please say that again.');
      } finally {
        setLocalLoading(false);
        clearTranscript();
      }
    };

    run();
  }, [
    pendingSubmit,
    isListening,
    callState,
    transcript,
    interimTranscript,
    addToCallTranscript,
    speakerOn,
    speak,
    clearTranscript,
    clearError,
  ]);

  const handleMuteToggle = () => {
    if (callState !== 'connected') return;
    if (!isMuted) {
      stopListening();
      clearError();
      setPendingSubmit(false);
    }
    toggleMute();
  };

  const handleStartListening = () => {
    if (callState !== 'connected' || isMuted || localLoading || isListening) return;
    clearError();
    clearTranscript();
    startListening();
  };

  const handleDoneSpeaking = () => {
    if (callState !== 'connected' || localLoading || isMuted) return;
    setPendingSubmit(true);
    stopListening();
  };

  const getStatusIndicator = () => {
    switch (callState) {
      case 'connecting':
        return <span className="call-status-connecting">Connecting...</span>;
      case 'connected':
        return <span className="call-status-connected">Connected</span>;
      case 'ended':
        return <span className="call-status-ended">Call ended</span>;
      default:
        return null;
    }
  };

  return (
    <div className="call-mode-wrapper">
      <div className="call-header">
        <div className="call-info">
          <div className="call-status-container">{getStatusIndicator()}</div>
          <div className="call-duration">
            <span className="duration-label">Duration:</span>
            <span className="duration-value">{formatDuration(duration)}</span>
          </div>
        </div>

        <div className="call-indicators">
          {isMuted && <span className="mute-indicator">Muted</span>}
          {!speakerOn && <span className="speaker-indicator">Speaker off</span>}
          {isListening && <span className="listening-indicator">Listening</span>}
          {isSpeaking && <span className="speaking-indicator">Speaking</span>}
        </div>
      </div>

      {callState === 'connected' && !isMuted && (
        <div className="voice-status">
          {transcript || interimTranscript ? (
            <p className="voice-interim">You: {transcript || interimTranscript}</p>
          ) : (
            <p className="voice-waiting">Click Start Listening, speak, then click Done Speaking.</p>
          )}
        </div>
      )}

      {error && (
        <div className="call-error-message">
          <p className="error-text">{error}</p>
          {callState === 'connected' && !isMuted && (
            <button
              type="button"
              className="retry-listen-button"
              onClick={retryListening}
              disabled={localLoading}
            >
              Retry Listening
            </button>
          )}
        </div>
      )}

      <div className="call-controls">
        <button
          type="button"
          className="listen-button"
          onClick={handleStartListening}
          disabled={callState !== 'connected' || localLoading || isMuted || isListening}
          aria-label="Start listening"
        >
          Start Listening
        </button>

        <button
          type="button"
          className="done-speaking-button"
          onClick={handleDoneSpeaking}
          disabled={
            callState !== 'connected' ||
            localLoading ||
            isMuted ||
            !(isListening || transcript || interimTranscript)
          }
          aria-label="Done speaking"
        >
          Done Speaking
        </button>

        <button
          type="button"
          className={`mute-button ${isMuted ? 'muted' : ''}`}
          onClick={handleMuteToggle}
          disabled={callState !== 'connected' || localLoading}
          aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>

        <button
          type="button"
          className="end-call-button"
          onClick={onEndCall}
          disabled={callState === 'idle' || isLoading || localLoading}
          aria-label="End call"
        >
          End Call
        </button>
      </div>

      <div className="call-transcript">
        <h4 className="transcript-title">Call Transcript</h4>
        <div className="transcript-messages" role="log" aria-live="polite">
          {callTranscript.length === 0 ? (
            <p className="transcript-empty">
              {callState === 'connecting'
                ? 'Connecting to support agent...'
                : 'No messages yet. Unmute to start speaking.'}
            </p>
          ) : (
            callTranscript.map((msg, idx) => (
              <div key={idx} className={`transcript-bubble transcript-${msg.sender}`}>
                <span className="transcript-sender">{msg.sender === 'user' ? 'You' : 'Support'}:</span>
                <span className="transcript-text">{msg.text}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default CallMode;
