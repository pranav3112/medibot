import React from 'react';
import './Sidebar.css';

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  chatHistory: ChatSession[];
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  onClose, 
  chatHistory, 
  onSelectChat, 
  onNewChat 
}) => {
  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={onClose} />}
      <div className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <button className="new-chat-button" onClick={onNewChat}>
            <span className="plus-icon">+</span>
            New Chat
          </button>
        </div>
        
        <div className="sidebar-content">
          <div className="chat-history">
            <h3>Chat History</h3>
            {chatHistory.length === 0 ? (
              <p className="no-history">No previous conversations</p>
            ) : (
              <div className="chat-list">
                {chatHistory.map((chat) => (
                  <div 
                    key={chat.id} 
                    className="chat-item"
                    onClick={() => onSelectChat(chat.id)}
                  >
                    <div className="chat-title">{chat.title}</div>
                    <div className="chat-timestamp">
                      {chat.timestamp.toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;