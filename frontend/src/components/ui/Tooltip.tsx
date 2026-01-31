import {
  type ReactElement,
  useCallback,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

interface TooltipProps {
  content: string;
  children: ReactElement;
  side?: "right";
  enabled?: boolean;
}

export default function Tooltip({
  content,
  children,
  side = "right",
  enabled = true,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);

  const show = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setCoords({
      top: rect.top + rect.height / 2,
      left: rect.right + 8,
    });
    setVisible(true);
  }, []);

  const hide = useCallback(() => {
    setVisible(false);
  }, []);

  if (!enabled) return children;

  return (
    <>
      <span
        ref={triggerRef}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        className="inline-flex"
      >
        {children}
      </span>
      {visible &&
        createPortal(
          <div
            style={{
              position: "fixed",
              top: coords.top,
              left: side === "right" ? coords.left : undefined,
              transform: "translateY(-50%)",
            }}
            className="bg-text-primary text-white text-xs px-2 py-1 rounded-md whitespace-nowrap shadow-lg z-[100] pointer-events-none"
            role="tooltip"
          >
            {content}
          </div>,
          document.body,
        )}
    </>
  );
}
