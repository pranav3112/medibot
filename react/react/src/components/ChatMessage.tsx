import React from 'react';
import './ChatMessage.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const formatTextResponse = (content: string) => {
    const parts = content.split(/(?=\d+\))/);
    
    return (
      <div className="formatted-response">
        {parts.map((part, index) => {
          if (!part.trim()) return null;
          const match = part.match(/(\d+\))\s*(.*)/s);
          if (match) {
            const [, number, content] = match;
            return (
              <div key={index} className="response-point">
                <span className="point-number">{number}</span>
                <span className="point-content">{content}</span>
              </div>
            );
          }
          return (
            <div key={index} className="response-text">
              {part}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`message ${message.role === 'user' ? 'user-message' : 'bot-message'}`}>
      <div className="message-content">
        {message.role === 'user' ? (
          <div className="user-content">
            <span className="user-icon">👤</span>
            <span className="user-text">{message.content}</span>
          </div>
        ) : (
          <>
            <div className="message-header">
              🩺 MediTriage:
            </div>
            {formatTextResponse(message.content)}
          </>
        )}
      </div>
      <div className="message-timestamp">
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
};

export default ChatMessage;