/**
 * VoiceInput: Microphone button, transcript display, and voice state controls
 */

import { forwardRef, useEffect, useImperativeHandle } from 'react';
import { useVoice } from '../hooks/useVoice.js';
import { Mic, Square, X, Volume2 } from 'lucide-react';

const VoiceInput = forwardRef(function VoiceInput({ onTranscriptReady, disabled = false, autoStart = true }, ref) {
  const {
    isListening,
    isSpeaking,
    transcript,
    interimTranscript,
    isSupported,
    error,
    startListening,
    stopListening,
    abortListening,
    clearTranscript,
  } = useVoice({
    autoFinalizeOnSilence: false,
    maxUtteranceDurationMs: 120000,
    minUtteranceDurationMs: 300,
  });

  const mergedText = (transcript || interimTranscript || '').trim();

  useEffect(() => {
    if (onTranscriptReady) {
      onTranscriptReady(mergedText);
    }
  }, [mergedText, onTranscriptReady]);

  useEffect(() => {
    if (autoStart && !disabled && !isListening && !isSpeaking) {
      startListening();
    }
  }, [autoStart, disabled, isListening, isSpeaking, startListening]);

  useImperativeHandle(ref, () => ({
    stopAndGetTranscript: () => {
      stopListening();
      return (transcript || interimTranscript || '').trim();
    },
    startListeningNow: () => {
      if (!disabled) {
        startListening();
      }
    },
    clearCapturedText: () => {
      clearTranscript();
    },
  }), [disabled, startListening, stopListening, transcript, interimTranscript, clearTranscript]);

  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleAbort = () => {
    abortListening();
  };

  if (!isSupported) {
    return (
      <div className="voice-input-disabled">
        <p>Voice features not available in your browser. Text chat works normally.</p>
      </div>
    );
  }

  return (
    <div className="voice-input-wrapper">
      <div className="voice-controls">
        <button
          type="button"
          className={`mic-button ${isListening ? 'listening' : ''}`}
          onClick={handleMicClick}
          disabled={disabled || isSpeaking}
          aria-label={isListening ? 'Pause listening' : 'Resume listening'}
          title={isListening ? 'Pause listening' : 'Resume listening'}
        >
          {isListening ? <Square size={14} aria-hidden="true" /> : <Mic size={16} aria-hidden="true" />}
          {isListening ? 'Listening' : 'Resume'}
        </button>

        {isListening && (
          <button
            type="button"
            className="voice-cancel-button"
            onClick={handleAbort}
            aria-label="Cancel voice input"
            title="Cancel and clear"
          >
            <X size={14} aria-hidden="true" />
          </button>
        )}
      </div>

      {(isListening || transcript || interimTranscript) && (
        <div className="voice-transcript" role="status" aria-live="polite">
          {transcript && <p className="transcript-final">{transcript}</p>}
          {interimTranscript && (
            <p className="transcript-interim">{interimTranscript}</p>
          )}
          {!transcript && !interimTranscript && isListening && (
            <p className="transcript-placeholder">Listening... press Send when finished speaking.</p>
          )}
        </div>
      )}

      {error && (
        <p className="voice-error" role="alert">
          {error}
        </p>
      )}

      {isSpeaking && (
        <div className="voice-speaking" role="status">
          <span className="speaking-indicator"><Volume2 size={14} aria-hidden="true" /> Speaking...</span>
        </div>
      )}
    </div>
  );
});

export default VoiceInput;
