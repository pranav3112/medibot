interface ChatResponse {
  answer: string;
  source_documents: {
    page_content: string;
    metadata: {
      [key: string]: any;
    };
  }[];
}

const API_URL = 'http://localhost:8000';

export const chatService = {
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },
};