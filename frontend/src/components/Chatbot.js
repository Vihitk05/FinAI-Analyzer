"use client";

import { useState, useRef, useEffect } from "react";
import { Send, X, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export const ChatBot = ({ customId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const toggleChat = () => setIsOpen(!isOpen);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = { text: inputValue, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/query/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: inputValue,
          custom_id: customId,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        { text: data.response, sender: "bot" },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          text: "Sorry, I couldn't process your request. Please try again.",
          sender: "bot",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {isOpen ? (
        <div className="w-80 h-[500px] bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col">
          <div className="bg-blue-600 text-white p-3 rounded-t-lg flex justify-between items-center">
            <h3 className="font-semibold">FinAI Assistant</h3>
            <button onClick={toggleChat} className="text-white hover:text-blue-200">
              <X size={18} />
            </button>
          </div>
          <div className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <p>Ask me anything about this financial analysis</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-xs p-3 rounded-lg ${message.sender === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-800"}`}
                    >
                      {message.text}
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 p-3 rounded-lg">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                      <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce delay-75"></div>
                      <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce delay-150"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          <div className="p-3 border-t border-gray-200">
          <div className="flex items-center">
            <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your question..."
                className="flex-1 h-[40px] border border-gray-300 rounded-l-lg px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
            />
            <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="rounded-l-none bg-blue-600 hover:bg-blue-700 h-[40px]"
            >
                <Send size={18} />
            </Button>
            </div>
          </div>
        </div>
      ) : (
        <Button
          onClick={toggleChat}
          className="rounded-full h-14 w-14 bg-blue-600 hover:bg-blue-700 shadow-lg"
        >
          <MessageCircle size={24} />
        </Button>
      )}
    </div>
  );
};