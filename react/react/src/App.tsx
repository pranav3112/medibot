import { useState, useRef, useEffect, useCallback } from 'react'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import Sidebar from './components/Sidebar'
import HamburgerButton from './components/HamburgerButton'
import { chatService } from './services/chatService'
import './App.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatSession {
  id: string
  title: string
  timestamp: Date
  messages: Message[]
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [chatSessions, setChatSessions] = useState<ChatSession[]>(() => {
    // Load chat sessions from sessionStorage on initial load (clears when browser closes)
    const saved = sessionStorage.getItem('chatSessions')
    return saved ? JSON.parse(saved).map((session: any) => ({
      ...session,
      timestamp: new Date(session.timestamp),
      messages: session.messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }))
    })) : []
  })
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Function to save current session
  const saveCurrentSession = useCallback(() => {
    if (messages.length > 0) {
      const sessionId = currentSessionId || Date.now().toString()
      const sessionTitle = messages[0]?.content.slice(0, 50) + '...' || 'New Chat'
      
      const newSession: ChatSession = {
        id: sessionId,
        title: sessionTitle,
        timestamp: new Date(),
        messages: [...messages]
      }
      
      setChatSessions(prev => {
        // Check if session already exists (update) or is new (add)
        const existingIndex = prev.findIndex(session => session.id === sessionId)
        if (existingIndex >= 0) {
          // Update existing session
          const updated = [...prev]
          updated[existingIndex] = newSession
          return updated
        } else {
          // Add new session
          return [newSession, ...prev]
        }
      })
      
      setCurrentSessionId(sessionId)
    }
  }, [messages, currentSessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Save chat sessions to sessionStorage (clears when browser closes)
  useEffect(() => {
    sessionStorage.setItem('chatSessions', JSON.stringify(chatSessions))
  }, [chatSessions])

  // Auto-save session when messages change (with debounce)
  useEffect(() => {
    if (messages.length > 0) {
      const timeoutId = setTimeout(() => {
        saveCurrentSession()
      }, 2000) // Save 2 seconds after last message

      return () => clearTimeout(timeoutId)
    }
  }, [messages, saveCurrentSession])

  // Close sidebar when clicking anywhere outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isSidebarOpen) {
        const target = event.target as HTMLElement
        const sidebar = document.querySelector('.sidebar')
        const hamburger = document.querySelector('.hamburger-button')
        
        // Close sidebar if clicking outside sidebar and hamburger button
        if (sidebar && !sidebar.contains(target) && hamburger && !hamburger.contains(target)) {
          setIsSidebarOpen(false)
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isSidebarOpen])

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await chatService.sendMessage(message)
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date()
      }

      setMessages(prev => {
        const updatedMessages = [...prev, assistantMessage]
        // Auto-save session after getting response
        setTimeout(() => {
          saveCurrentSession()
        }, 100)
        return updatedMessages
      })
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => {
        const updatedMessages = [...prev, errorMessage]
        // Auto-save session even on error
        setTimeout(() => {
          saveCurrentSession()
        }, 100)
        return updatedMessages
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleSidebar = () => {
    setIsSidebarOpen(true) // Only open, don't toggle
  }

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false)
  }

  const handleSelectChat = (chatId: string) => {
    // Save current session before switching
    saveCurrentSession()
    
    const session = chatSessions.find(s => s.id === chatId)
    if (session) {
      setMessages(session.messages)
      setCurrentSessionId(chatId)
      setIsSidebarOpen(false)
    }
  }

  const handleNewChat = () => {
    // Save current session if there are messages
    saveCurrentSession()
    
    // Start new chat
    setMessages([])
    setCurrentSessionId(null) // Reset to null for new session
    setIsSidebarOpen(false)
  }

  return (
    <div className="app">
      {/* Hamburger Button */}
      <HamburgerButton onClick={handleToggleSidebar} isOpen={isSidebarOpen} />
      
      {/* Sidebar */}
      <Sidebar 
        isOpen={isSidebarOpen}
        onClose={handleCloseSidebar}
        chatHistory={chatSessions}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
      />
      
      {/* Header */}
      <header className="main-header">
        <h1 className="main-title">
          Healthcare AI Agent
        </h1>
        <p className="subtitle">
          Ask Chatbot!
        </p>
      </header>

      {/* Chat Messages Container */}
      <div className="chat-container">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <p>👋 Hi! How can I assist you today?</p>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
          
          {isLoading && (
            <div className="message bot-message">
              <div className="message-content">
                <strong>🤖 Assistant:</strong> <span className="typing-indicator">Thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Bottom Input Bar */}
      <ChatInput 
        onSendMessage={handleSendMessage}
        disabled={isLoading}
        placeholder="Ask me anything..."
      />
    </div>
  )
}

export default App
