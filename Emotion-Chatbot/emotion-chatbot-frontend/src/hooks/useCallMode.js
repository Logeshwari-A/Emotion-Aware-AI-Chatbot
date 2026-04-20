/**
 * useCallMode: Custom hook for phone call mode management
 * Handles call state, duration, mute, speaker, and transcript
 */

import { useEffect, useRef, useState } from 'react';

export function useCallMode() {
  const [callState, setCallState] = useState('idle'); // idle, connecting, connected, ended
  const [duration, setDuration] = useState(0); // seconds
  const [isMuted, setIsMuted] = useState(false);
  const [speakerOn, setSpeakerOn] = useState(true);
  const [callTranscript, setCallTranscript] = useState([]);

  const durationIntervalRef = useRef(null);
  const callStartTimeRef = useRef(null);

  // Auto-increment duration every second during call
  useEffect(() => {
    if (callState === 'connected') {
      durationIntervalRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    }

    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [callState]);

  // Format duration as MM:SS
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  // Start call
  const startCall = () => {
    setCallState('connecting');
    callStartTimeRef.current = Date.now();
    setDuration(0);
    setCallTranscript([]);
    setIsMuted(false);
    setSpeakerOn(true);

    // Simulate connection established after 1.5s
    setTimeout(() => {
      setCallState('connected');
    }, 1500);
  };

  // End call
  const endCall = () => {
    setCallState('ended');
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }

    // Reset to idle after 2s (for UI feedback)
    setTimeout(() => {
      setCallState('idle');
      setDuration(0);
      setCallTranscript([]);
    }, 2000);
  };

  // Toggle mute
  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  // Toggle speaker
  const toggleSpeaker = () => {
    setSpeakerOn(!speakerOn);
  };

  // Add message to call transcript
  const addToCallTranscript = (sender, text) => {
    setCallTranscript((prev) => [...prev, { sender, text, timestamp: Date.now() }]);
  };

  // Clear call transcript
  const clearCallTranscript = () => {
    setCallTranscript([]);
  };

  // Get call status text
  const getStatusText = () => {
    switch (callState) {
      case 'idle':
        return 'Ready to call';
      case 'connecting':
        return 'Connecting...';
      case 'connected':
        return 'Call connected';
      case 'ended':
        return 'Call ended';
      default:
        return 'Unknown';
    }
  };

  return {
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
    clearCallTranscript,
    getStatusText,
  };
}
