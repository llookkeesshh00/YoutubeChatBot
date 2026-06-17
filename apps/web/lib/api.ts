const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  const response = await fetch(`${API_URL}/api/transcripts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function askQuestion(payload: {
  session_id: string;
  message: string;
}): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

