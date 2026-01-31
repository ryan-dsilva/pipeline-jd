import type { Job, JobCreate, JobDetail, Section, SectionDefinition } from "./types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Jobs ────────────────────────────────────────────────────────

export const createJob = (data: JobCreate) =>
  request<Job>("/jobs", { method: "POST", body: JSON.stringify(data) });

export const listJobs = (params?: { stage?: string; search?: string }) => {
  const sp = new URLSearchParams();
  if (params?.stage) sp.set("stage", params.stage);
  if (params?.search) sp.set("search", params.search);
  const qs = sp.toString();
  return request<Job[]>(`/jobs${qs ? `?${qs}` : ""}`);
};

export const getJob = (id: string) => request<JobDetail>(`/jobs/${id}`);

export const deleteJob = (id: string) =>
  request<void>(`/jobs/${id}`, { method: "DELETE" });

export const updateJobStage = (id: string, stage: string) =>
  request<Job>(`/jobs/${id}/stage`, {
    method: "PUT",
    body: JSON.stringify({ stage }),
  });

export const reExtractJob = (jobId: string) =>
  request<Job>(`/jobs/${jobId}/extract`, { method: "POST" });

export const updateJob = (
  jobId: string,
  data: { company?: string; role?: string }
) =>
  request<Job>(`/jobs/${jobId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

// ── Pipeline ────────────────────────────────────────────────────

export function startAnalysis(jobId: string): EventSource {
  return new EventSource(`${BASE}/pipeline/${jobId}/analyze`, );
}

export function startCoverLetter(jobId: string): EventSource {
  return new EventSource(`${BASE}/pipeline/${jobId}/cover-letter`);
}

export function pipelineStatus(jobId: string): EventSource {
  return new EventSource(`${BASE}/pipeline/${jobId}/status`);
}

// SSE via POST (for analyze/cover-letter which are POST endpoints)
export async function startPipelineSSE(
  jobId: string,
  phase: "analyze" | "cover-letter",
  onEvent: (data: unknown) => void,
  onDone: () => void,
  onError: (err: unknown) => void,
): Promise<AbortController> {
  const controller = new AbortController();
  try {
    const res = await fetch(`${BASE}/pipeline/${jobId}/${phase}`, {
      method: "POST",
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`Pipeline start failed: ${res.status}`);
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    (async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            const match = line.match(/^data: (.+)$/m);
            if (match) {
              try {
                const parsed = JSON.parse(match[1]);
                if (parsed.done) {
                  onDone();
                  return;
                }
                onEvent(parsed);
              } catch { /* skip non-JSON */ }
            }
          }
        }
        onDone();
      } catch (err) {
        if (!controller.signal.aborted) onError(err);
      }
    })();
  } catch (err) {
    if (!controller.signal.aborted) onError(err);
  }
  return controller;
}

// ── Sections ────────────────────────────────────────────────────

export const getSectionDefinitions = () =>
  request<SectionDefinition[]>("/section-definitions");

export const listSections = (jobId: string) =>
  request<Section[]>(`/sections/${jobId}`);

export const getSection = (jobId: string, key: string) =>
  request<Section>(`/sections/${jobId}/${key}`);

export const updateSection = (jobId: string, key: string, content_md: string) =>
  request<Section>(`/sections/${jobId}/${key}`, {
    method: "PUT",
    body: JSON.stringify({ content_md }),
  });

export const regenerateSection = (jobId: string, key: string) =>
  request<Section>(`/sections/${jobId}/${key}/generate`, { method: "POST" });

export const toggleLock = (jobId: string, key: string, is_locked: boolean) =>
  request<Section>(`/sections/${jobId}/${key}/lock`, {
    method: "POST",
    body: JSON.stringify({ is_locked }),
  });

// ── Chat ────────────────────────────────────────────────────────

export async function sendChatMessage(
  jobId: string,
  message: string,
  history: { role: string; content: string }[],
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (err: unknown) => void,
): Promise<AbortController> {
  const controller = new AbortController();
  try {
    const res = await fetch(`${BASE}/chat/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    (async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            const match = line.match(/^data: (.+)$/m);
            if (match) {
              if (match[1] === "[DONE]") {
                onDone();
                return;
              }
              onChunk(match[1]);
            }
          }
        }
        onDone();
      } catch (err) {
        if (!controller.signal.aborted) onError(err);
      }
    })();
  } catch (err) {
    if (!controller.signal.aborted) onError(err);
  }
  return controller;
}
