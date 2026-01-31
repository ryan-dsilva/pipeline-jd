import { useRef, useState, useMemo } from "react";
import { marked } from "marked";
import type { ChatMessage } from "../lib/types";
import { sendChatMessage } from "../lib/api";
import Input from "./ui/Input";
import Button from "./ui/Button";

interface ChatBarProps {
  jobId: string;
}

export default function ChatBar({ jobId }: ChatBarProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || streaming) return;

    setExpanded(true);
    const userMsg: ChatMessage = { role: "user", content: text };
    const history = [...messages];
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    controllerRef.current = await sendChatMessage(
      jobId,
      text,
      history,
      (chunk) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = {
              ...last,
              content: last.content + chunk,
            };
          }
          return updated;
        });
        scrollToBottom();
      },
      () => setStreaming(false),
      () => setStreaming(false),
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleStop = () => {
    controllerRef.current?.abort();
    setStreaming(false);
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="border-t border-border-light bg-white">
      {/* Expandable conversation panel */}
      {expanded && hasMessages && (
        <div className="max-h-80 overflow-y-auto px-4 py-3 space-y-3 border-b border-border-light">
          {messages.map((msg, i) => (
            <ChatMessageBubble key={i} message={msg} />
          ))}
          {streaming && messages[messages.length - 1]?.role === "assistant" && messages[messages.length - 1]?.content === "" && (
            <div className="flex justify-start">
              <div className="bg-bg-off-white rounded-lg px-3 py-2">
                <span className="text-sm text-text-secondary animate-pulse">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      {/* Input bar */}
      <div className="px-4 py-3">
        <div className="flex gap-2">
          {expanded && hasMessages && (
            <button
              onClick={() => setExpanded(false)}
              className="px-2 py-1.5 text-text-secondary hover:text-text-primary shrink-0"
              title="Collapse chat"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => hasMessages && setExpanded(true)}
            placeholder="Ask about this role..."
            className="flex-1"
          />
          {streaming ? (
            <Button
              onClick={handleStop}
              variant="ghost"
              size="sm"
            >
              Stop
            </Button>
          ) : (
            <Button
              onClick={handleSend}
              disabled={!input.trim()}
              size="sm"
            >
              Send
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  // Assistant content comes from our own Claude backend, not arbitrary user HTML
  const html = useMemo(() => {
    if (message.role === "assistant" && message.content) {
      return marked.parse(message.content) as string;
    }
    return "";
  }, [message.role, message.content]);

  return (
    <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          message.role === "user"
            ? "bg-brand-primary text-white"
            : "bg-bg-off-white text-text-primary"
        }`}
      >
        {message.role === "assistant" && html ? (
          <div
            className="prose prose-sm max-w-none [&_a]:text-brand-primary"
            // Safe: content originates from our own Claude API backend
            dangerouslySetInnerHTML={{ __html: html }}
          />
        ) : (
          <div className="whitespace-pre-wrap">{message.content}</div>
        )}
      </div>
    </div>
  );
}
