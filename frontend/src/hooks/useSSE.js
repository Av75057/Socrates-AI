import { useCallback, useEffect, useRef, useState } from "react";
import { getToken } from "../api/client.js";

function parseEventData(raw) {
  if (raw == null || raw === "") return "";
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function parseSseBlock(block) {
  const lines = block.split("\n");
  let event = "message";
  const data = [];
  for (const line of lines) {
    if (!line) continue;
    if (line.startsWith("event:")) {
      event = line.slice(6).trim() || "message";
      continue;
    }
    if (line.startsWith("data:")) {
      data.push(line.slice(5).trimStart());
    }
  }
  return { event, data: parseEventData(data.join("\n")) };
}

export function useSSE(url, options = {}) {
  const abortControllerRef = useRef(null);
  const [streaming, setStreaming] = useState(false);

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setStreaming(false);
  }, []);

  useEffect(() => cancel, [cancel]);

  const send = useCallback(
    async (body, handlers = {}) => {
      cancel();
      const controller = new AbortController();
      abortControllerRef.current = controller;
      setStreaming(true);

      const {
        onOpen,
        onMeta,
        onChunk,
        onDone,
        onError,
      } = handlers;

      try {
        const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
        const token = getToken();
        if (token) headers.Authorization = `Bearer ${token}`;

        const response = await fetch(url, {
          method: "POST",
          headers,
          ...options,
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || response.statusText || "Request failed");
        }

        if (!response.body) {
          throw new Error("Streaming is not supported in this browser.");
        }

        onOpen?.(response);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let finalPayload = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let boundary = buffer.indexOf("\n\n");
          while (boundary >= 0) {
            const rawEvent = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            const parsed = parseSseBlock(rawEvent);
            if (parsed.event === "meta") onMeta?.(parsed.data);
            else if (parsed.event === "chunk") onChunk?.(parsed.data);
            else if (parsed.event === "done") {
              finalPayload = parsed.data;
              onDone?.(parsed.data);
            } else if (parsed.event === "error") {
              const message =
                parsed.data && typeof parsed.data === "object" && "message" in parsed.data
                  ? parsed.data.message
                  : String(parsed.data || "Streaming failed");
              throw new Error(message);
            }
            boundary = buffer.indexOf("\n\n");
          }
        }

        if (buffer.trim()) {
          const parsed = parseSseBlock(buffer.trim());
          if (parsed.event === "done") {
            finalPayload = parsed.data;
            onDone?.(parsed.data);
          }
        }

        return finalPayload;
      } catch (error) {
        if (error?.name === "AbortError") {
          throw error;
        }
        onError?.(error);
        throw error;
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
        setStreaming(false);
      }
    },
    [cancel, options, url],
  );

  return { send, cancel, streaming };
}
