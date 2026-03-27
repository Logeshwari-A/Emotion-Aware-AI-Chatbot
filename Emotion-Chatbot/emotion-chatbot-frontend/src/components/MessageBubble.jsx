function MessageBubble({ message }) {
  const isUser = message.sender === 'user';

  return (
    <article className={`bubble-row ${isUser ? 'user-row' : 'bot-row'}`}>
      <div className={`bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`}>
        <p>{message.text}</p>
      </div>
    </article>
  );
}

export default MessageBubble;
