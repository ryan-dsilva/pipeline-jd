import { useCallback, useRef, useState } from "react";
import type { PipelineEvent, SectionStatus } from "../lib/types";
import { startPipelineSSE } from "../lib/api";

interface UseSSEReturn {
  statuses: Record<string, SectionStatus>;
  running: boolean;
  error: string | null;
  start: (jobId: string, phase: "analyze" | "cover-letter") => void;
  stop: () => void;
}

export function useSSE(): UseSSEReturn {
  const [statuses, setStatuses] = useState<Record<string, SectionStatus>>({});
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setRunning(false);
  }, []);

  const start = useCallback(
    (jobId: string, phase: "analyze" | "cover-letter") => {
      stop();
      setStatuses({});
      setError(null);
      setRunning(true);

      startPipelineSSE(
        jobId,
        phase,
        (data) => {
          const event = data as PipelineEvent;
          setStatuses((prev) => ({
            ...prev,
            [event.section_key]: event.status,
          }));
        },
        () => setRunning(false),
        (err) => {
          setError(String(err));
          setRunning(false);
        },
      ).then((ctrl) => {
        controllerRef.current = ctrl;
      });
    },
    [stop],
  );

  return { statuses, running, error, start, stop };
}
