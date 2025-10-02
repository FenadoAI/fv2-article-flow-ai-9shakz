import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { MessageSquare, X, Send, Bot } from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const API = `${API_BASE}/api`;

export default function AdminAssistant({ onCategoryCreated, onArticleCreated }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! I'm your AI assistant. I can help you:\n• Create articles\n• Show latest articles\n• Create categories\n• Rename categories\n• List categories\n\nTry: 'Rename category technology to Tech'"
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");

    // Add user message to chat
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(`${API}/admin/assistant/chat`, {
        message: userMessage
      });

      // Add assistant response
      setMessages(prev => [...prev, {
        role: "assistant",
        content: response.data.response
      }]);

      // If category was created or renamed, notify parent to refresh
      if ((response.data.action_taken === "create_category" || response.data.action_taken === "rename_category") && onCategoryCreated) {
        onCategoryCreated();
      }

      // If article was created, notify parent to refresh
      if (response.data.action_taken === "create_article" && onArticleCreated) {
        onArticleCreated();
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
          size="icon"
        >
          <Bot className="h-6 w-6" />
        </Button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <Card className="fixed bottom-6 right-6 w-96 h-[500px] shadow-xl flex flex-col">
          <CardHeader className="flex-row items-center justify-between space-y-0 pb-3 border-b">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              <CardTitle className="text-lg">AI Assistant</CardTitle>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(false)}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      msg.role === "user"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-100 text-gray-900"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3">
                    <p className="text-sm text-gray-500">Thinking...</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={loading}
                  className="flex-1"
                />
                <Button
                  onClick={sendMessage}
                  disabled={loading || !inputMessage.trim()}
                  size="icon"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}
