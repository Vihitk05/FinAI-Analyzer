"use client";

import { useState, useRef, useEffect } from "react";
import { Send, X, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";

// Pass `customId` for a single report or `companyId` for a company dashboard.
// Both talk to POST /query/ and answer only from the verified dataset.
export const ChatBot = ({ customId, companyId }) => {
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
    const question = inputValue.trim();
    if (!question || isLoading) return;

    const userMessage = { text: question, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const body = companyId
        ? { query: question, company_id: companyId }
        : { query: question, custom_id: customId };
      const data = await api.post("/query/", body);
      setMessages((prev) => [
        ...prev,
        {
          text: data.response,
          sender: "bot",
          insufficientContext: data.insufficient_context,
          citedPages: data.cited_pages || [],
          missingInformation: data.missing_information || "",
          claims: data.claims || [],
          corrected: data.corrected_for_unsupported_claims,
        },
      ]);
    } catch (error) {
      const message =
        error instanceof ApiError && error.status === 401
          ? "Your session has expired. Please sign in again."
          : "Sorry, I couldn't process your request. Please try again.";
      setMessages((prev) => [...prev, { text: message, sender: "bot" }]);
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
            <h3 className="font-semibold uppercase tracking-wide">FinAI Assistant</h3>
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
                      className={`max-w-xs whitespace-pre-wrap break-words p-3 rounded-lg ${message.sender === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-800"}`}
                    >
                      {message.text}
                      {message.sender === "bot" && (message.claims?.length || message.missingInformation || message.corrected) ? (
                        <div className="mt-2 border-t border-gray-300 pt-2 text-[11px] text-gray-500">
                          {message.claims?.length ? (
                            <div className="mb-1 flex flex-wrap gap-1">
                              {[...new Set(message.claims.map((c) => c.type))].map((type) => (
                                <span key={type} className="rounded-full bg-white px-2 py-0.5 capitalize ring-1 ring-gray-300">{type}</span>
                              ))}
                            </div>
                          ) : null}
                          {message.corrected ? <p className="text-amber-700">Adjusted to match source-verified figures.</p> : null}
                          {message.missingInformation ? <p>Not in the verified data: {message.missingInformation}</p> : null}
                          <p className="mt-1 text-gray-400">Grounded in the verified dataset.</p>
                        </div>
                      ) : null}
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