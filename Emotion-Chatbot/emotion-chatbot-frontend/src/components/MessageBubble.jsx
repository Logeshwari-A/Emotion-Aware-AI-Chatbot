import { useState } from 'react';
import { buildReasoningPathHuman } from '../utils/emotionTranslator.js';
import { ShieldAlert } from 'lucide-react';

function MessageBubble({ message, reasoning_path, risk_level, safety_trigger }) {
  const isUser = message.sender === 'user';
  const [showTooltip, setShowTooltip] = useState(false);
  
  const reasoningText = reasoning_path ? buildReasoningPathHuman(reasoning_path) : null;

  return (
    <article className={`bubble-row ${isUser ? 'user-row' : 'bot-row'}`}>
      <div className={`bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`}>
        <p>{message.text}</p>
      </div>
      
      {!isUser && reasoningText && (
        <div className="tooltip-wrapper">
          <button
            type="button"
            className="why-button"
            onClick={() => setShowTooltip(!showTooltip)}
            aria-label="Show reasoning behind this response"
            title="Why did I respond this way?"
          >
            Why?
          </button>
          
          {showTooltip && (
            <div className="why-tooltip" role="tooltip">
              <p>{reasoningText}</p>
              {safety_trigger && (
                <p className="tooltip-safety"><ShieldAlert size={13} aria-hidden="true" /> Safety override active</p>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  );
}

export default MessageBubble;
