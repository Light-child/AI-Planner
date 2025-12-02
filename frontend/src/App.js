import React, { useState, useEffect, useRef } from "react";
import {
  Calendar,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
  ListTodo,
  Link,
  X,
} from "lucide-react";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        'Hi! I can help you manage your calendar and tasks. Try saying something like "Schedule a meeting tomorrow at 2pm" or "Create a task to finish homework".',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [showTasksModal, setShowTasksModal] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check connection status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/auth/status`);
      const data = await response.json();
      setIsConnected(data.authenticated || false);
    } catch (error) {
      console.error("Auth check failed:", error);
      setIsConnected(false);
    }
  };

  const quickActions = [
    { icon: Calendar, label: "Schedule Event", prompt: "Schedule a new event" },
    { icon: ListTodo, label: "Create Task", prompt: "Create a new task" },
    { icon: Link, label: "View Tasks", action: "viewTasks" },
  ];

  const handleQuickAction = (action) => {
    if (action.action === "viewTasks") {
      fetchTasks();
      setShowTasksModal(true);
    } else if (action.prompt) {
      setInput(action.prompt);
    }
  };

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/schedule`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: currentInput,
          history: messages,
        }),
      });

      const data = await response.json();

      const assistantMessage = {
        role: "assistant",
        content: data.response || "I processed your request successfully!",
        timestamp: new Date(),
        status: data.status || "success",
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: "assistant",
        content:
          "Sorry, I encountered an error. Please make sure the backend is running and try again.",
        timestamp: new Date(),
        status: "error",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleAuth = () => {
    window.open(`${API_URL}/auth`, "_blank", "width=600,height=700");

    // Check auth status after a delay
    setTimeout(() => {
      checkAuthStatus();
    }, 2000);
  };

  const fetchTasks = async () => {
    setLoadingTasks(true);
    try {
      // DEMO DATA - Remove this and uncomment the fetch below for production
      const demoTasks = [
        {
          title: "Finish Math Homework",
          notes: "Complete chapters 5-7 exercises",
          due: "2024-12-05T23:59:59Z",
          completed: false,
          linked_events: [
            {
              title: "Math Study Session",
              start: "2024-12-03T14:00:00Z",
            },
            {
              title: "Math Homework Deadline Reminder",
              start: "2024-12-05T20:00:00Z",
            },
          ],
        },
        {
          title: "Buy groceries",
          notes: "Milk, eggs, bread, and vegetables",
          due: "2024-12-02T18:00:00Z",
          completed: false,
          linked_events: [
            {
              title: "Grocery Shopping Trip",
              start: "2024-12-02T15:00:00Z",
            },
          ],
        },
        {
          title: "Submit project proposal",
          notes: "AI Scheduler project documentation",
          due: "2024-12-01T17:00:00Z",
          completed: true,
          linked_events: [
            {
              title: "Project Work Session",
              start: "2024-11-28T10:00:00Z",
            },
            {
              title: "Final Review Meeting",
              start: "2024-11-30T16:00:00Z",
            },
            {
              title: "Submission Deadline",
              start: "2024-12-01T17:00:00Z",
            },
          ],
        },
        {
          title: "Call dentist for appointment",
          notes: null,
          due: "2024-12-03T12:00:00Z",
          completed: false,
          linked_events: [],
        },
      ];

      setTimeout(() => {
        setTasks(demoTasks);
        setLoadingTasks(false);
      }, 800);

      // PRODUCTION CODE - Uncomment this when ready:
      // const response = await fetch(`${API_URL}/tasks`);
      // const data = await response.json();
      // setTasks(data.tasks || []);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
      setTasks([]);
      setLoadingTasks(false);
    }
  };

  return (
    <div className="w-full h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <Calendar className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">AI Scheduler</h1>
              <p className="text-xs text-gray-500">
                Your intelligent scheduling assistant
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className="text-sm text-gray-600">
              {isConnected ? "Connected" : "Disconnected"}
            </span>
            {!isConnected && (
              <button
                onClick={handleAuth}
                className="ml-2 px-3 py-1 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 transition-colors"
              >
                Connect
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex gap-2 overflow-x-auto">
          {quickActions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => handleQuickAction(action)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors whitespace-nowrap"
            >
              <action.icon className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-gray-700">
                {action.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((message, idx) => (
          <div
            key={idx}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-md rounded-lg px-4 py-3 ${
                message.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-white text-gray-800 shadow-sm border border-gray-200"
              }`}
            >
              <div className="flex items-start gap-2">
                {message.role === "assistant" && message.status && (
                  <div className="mt-1">
                    {message.status === "success" && (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    )}
                    {message.status === "error" && (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                  </div>
                )}
                <div className="flex-1">
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p
                    className={`text-xs mt-1 ${
                      message.role === "user"
                        ? "text-indigo-200"
                        : "text-gray-400"
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-lg px-4 py-3 shadow-sm border border-gray-200">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
                <span className="text-sm text-gray-600">Processing...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your request... (e.g., 'Schedule a meeting tomorrow at 2pm')"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            disabled={!isConnected || isLoading}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || !isConnected || isLoading}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Try natural commands like "Add dentist appointment next Friday at 3pm"
          or "Create a task to buy groceries"
        </p>
      </div>

      {/* Tasks Modal */}
      {showTasksModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <ListTodo className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-gray-800">
                  Your Tasks & Linked Events
                </h2>
              </div>
              <button
                onClick={() => setShowTasksModal(false)}
                className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {loadingTasks ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
                </div>
              ) : tasks.length === 0 ? (
                <div className="text-center py-12">
                  <ListTodo className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No tasks found</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Create a task to get started!
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {tasks.map((task, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-1">
                          <CheckCircle2
                            className={`w-5 h-5 ${
                              task.completed
                                ? "text-green-500"
                                : "text-gray-300"
                            }`}
                          />
                        </div>
                        <div className="flex-1">
                          <h3
                            className={`font-medium ${
                              task.completed
                                ? "text-gray-400 line-through"
                                : "text-gray-800"
                            }`}
                          >
                            {task.title}
                          </h3>
                          {task.notes && (
                            <p className="text-sm text-gray-500 mt-1">
                              {task.notes}
                            </p>
                          )}
                          {task.due && (
                            <p className="text-xs text-gray-400 mt-1">
                              Due: {new Date(task.due).toLocaleDateString()}
                            </p>
                          )}

                          {/* Linked Events */}
                          {task.linked_events &&
                            task.linked_events.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-gray-100">
                                <div className="flex items-center gap-2 mb-2">
                                  <Link className="w-4 h-4 text-indigo-600" />
                                  <span className="text-xs font-medium text-gray-600">
                                    Linked Events ({task.linked_events.length})
                                  </span>
                                </div>
                                <div className="space-y-2">
                                  {task.linked_events.map((event, eventIdx) => (
                                    <div
                                      key={eventIdx}
                                      className="bg-indigo-50 rounded px-3 py-2 text-sm"
                                    >
                                      <div className="flex items-center gap-2">
                                        <Calendar className="w-3 h-3 text-indigo-600" />
                                        <span className="font-medium text-indigo-900">
                                          {event.title}
                                        </span>
                                      </div>
                                      {event.start && (
                                        <p className="text-xs text-indigo-600 mt-1">
                                          {new Date(
                                            event.start
                                          ).toLocaleString()}
                                        </p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setShowTasksModal(false)}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
