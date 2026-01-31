import { useCallback, useEffect, useRef, useState } from "react";

export type SidebarMode = "collapsed" | "narrow" | "wide";

function getDefaultMode(): SidebarMode {
  const width = window.innerWidth;
  if (width < 768) return "collapsed";
  if (width <= 1280) return "narrow";
  return "wide";
}

export function useSidebarState() {
  const [mode, setMode] = useState<SidebarMode>(getDefaultMode);

  const userHasChosen = useRef(false);

  const choose = useCallback((m: SidebarMode) => {
    setMode(m);
    userHasChosen.current = true;
  }, []);

  const toggle = useCallback(() => {
    choose(mode === "wide" ? "narrow" : "wide");
  }, [mode, choose]);

  const expand = useCallback(() => {
    choose("wide");
  }, [choose]);

  // Debounced resize listener
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    const handleResize = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const width = window.innerWidth;

        // Auto-collapse below 768 always applies
        if (width < 768) {
          setMode("collapsed");
          return;
        }

        // If user hasn't manually chosen, derive from viewport
        if (!userHasChosen.current) {
          setMode(width <= 1280 ? "narrow" : "wide");
        }
      }, 150);
    };

    window.addEventListener("resize", handleResize);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return {
    mode,
    toggle,
    expand,
    isWide: mode === "wide",
    isNarrow: mode === "narrow",
    isCollapsed: mode === "collapsed",
  };
}
