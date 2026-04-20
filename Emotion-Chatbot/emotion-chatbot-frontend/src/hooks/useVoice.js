/**
 * useVoice: Custom hook for Web Speech API integration
 * Handles Speech-to-Text and Text-to-Speech with graceful fallback
 * Supports configurable silence timeout for utterance finalization (Stage 5)
 */

import { useEffect, useRef, useState } from 'react';

export function useVoice(options = {}) {
  const {
    silenceTimeoutMs = 1000,
    maxUtteranceDurationMs = 12000,
    minUtteranceDurationMs = 800,
    autoFinalizeOnSilence = true,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState(null);

  const recognitionRef = useRef(null);
  const utteranceRef = useRef(null);
  const silenceTimeoutRef = useRef(null);
  const finalTranscriptRef = useRef('');
  const listeningStartTimeRef = useRef(null);
  const retryTimeoutRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesis = window.speechSynthesis;

    const supported = !!(SpeechRecognition && speechSynthesis);
    setIsSupported(supported);

    if (!supported) {
      setError('Speech-to-Text and Text-to-Speech not supported in your browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      finalTranscriptRef.current = '';
      setTranscript('');
      setInterimTranscript('');
      listeningStartTimeRef.current = Date.now();
    };

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPart = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          final += transcriptPart + ' ';
        } else {
          interim += transcriptPart;
        }
      }

      if (final) {
        finalTranscriptRef.current += final;
        setTranscript(finalTranscriptRef.current.trim());
      }

      setInterimTranscript(interim);

      const listeningDuration = Date.now() - listeningStartTimeRef.current;
      if (listeningDuration > maxUtteranceDurationMs) {
        recognition.stop();
        return;
      }

      if (autoFinalizeOnSilence) {
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }

        silenceTimeoutRef.current = setTimeout(() => {
          const durationSoFar = Date.now() - listeningStartTimeRef.current;
          if (finalTranscriptRef.current.trim() && durationSoFar >= minUtteranceDurationMs) {
            recognition.stop();
          }
        }, silenceTimeoutMs);
      }
    };

    recognition.onerror = (event) => {
      const errorMsg = event.error;
      if (errorMsg === 'no-speech') {
        setError('No speech detected. Please try again.');
      } else if (errorMsg === 'audio-capture') {
        setError('No microphone access. Please check permissions.');
      } else if (errorMsg === 'network') {
        setError('Network error. Please check your connection.');
      } else {
        setError(`Speech recognition error: ${errorMsg}`);
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (recognition) {
        recognition.abort();
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
    };
  }, [autoFinalizeOnSilence, maxUtteranceDurationMs, minUtteranceDurationMs, silenceTimeoutMs]);

  const startListening = () => {
    if (!recognitionRef.current || !isSupported || isListening) return;
    setError(null);
    try {
      recognitionRef.current.start();
    } catch {
      // Ignore duplicate starts from rapid UI clicks.
    }
  };

  const stopListening = () => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {
      // Ignore stop errors if recognition is already ended.
    }
  };

  const abortListening = () => {
    if (!recognitionRef.current) return;
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
    }
    try {
      recognitionRef.current.abort();
    } catch {
      // Ignore abort errors when recognition is already idle.
    }
    setIsListening(false);
    finalTranscriptRef.current = '';
    setTranscript('');
    setInterimTranscript('');
  };

  const clearError = () => {
    setError(null);
  };

  const retryListening = () => {
    if (!recognitionRef.current || !isSupported) return;
    setError(null);
    finalTranscriptRef.current = '';
    setTranscript('');
    setInterimTranscript('');
    try {
      recognitionRef.current.abort();
    } catch {
      // Ignore abort race conditions.
    }
    retryTimeoutRef.current = setTimeout(() => {
      startListening();
    }, 300);
  };

  const speak = (text) => {
    if (!window.speechSynthesis) {
      setError('Text-to-Speech not supported');
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = (event) => {
      setIsSpeaking(false);
      setError(`Text-to-Speech error: ${event.error}`);
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const clearTranscript = () => {
    setTranscript('');
    setInterimTranscript('');
    finalTranscriptRef.current = '';
  };

  return {
    isListening,
    isSpeaking,
    transcript,
    interimTranscript,
    isSupported,
    error,
    startListening,
    stopListening,
    abortListening,
    clearError,
    retryListening,
    speak,
    stopSpeaking,
    clearTranscript,
  };
}
