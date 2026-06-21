const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 30000;

export type TranscriptCreated = {
  session_id: string;
  title: string;
  chunks_count: number;
};

export type Citation = {
  chunk_id: string;
  text: string;
  start_seconds: number | null;
  end_seconds: number | null;
  timestamp: string | null;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
};

export async function createTranscript(payload: {
  title: string;
  source_url?: string;
  transcript: string;
}): Promise<TranscriptCreated> {
  return fetchJson<TranscriptCreated>(`${API_URL}/api/transcripts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

export async function importYouTubeVideo(payload: {
  url: string;
  title?: string;
}): Promise<TranscriptCreated> {
  return fetchJson<TranscriptCreated>(`${API_URL}/api/youtube/import`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

export async function askQuestion(payload: {
  session_id: string;
  message: string;
}): Promise<ChatResponse> {
  return fetchJson<ChatResponse>(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

async function fetchJson<T>(url: string, init: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...init,
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    return response.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out. Check the backend terminal logs and try again.");
    }

    throw err;
  } finally {
    clearTimeout(timeout);
  }
}
