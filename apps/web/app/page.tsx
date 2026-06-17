"use client";

import { FormEvent, useState } from "react";
import { FileText, Loader2, MessageSquareText, Send, Upload } from "lucide-react";

import { askQuestion, ChatResponse, createTranscript, TranscriptCreated } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: ChatResponse["citations"];
};

export default function Home() {
  const [title, setTitle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [session, setSession] = useState<TranscriptCreated | null>(null);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState("");

  async function handleTranscriptSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsIndexing(true);

    try {
      const created = await createTranscript({
        title: title || "Untitled video",
        source_url: sourceUrl || undefined,
        transcript
      });
      setSession(created);
      setMessages([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not index transcript.");
    } finally {
      setIsIndexing(false);
    }
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session || !question.trim()) {
      return;
    }

    const userQuestion = question.trim();
    setQuestion("");
    setError("");
    setIsAsking(true);
    setMessages((current) => [...current, { role: "user", content: userQuestion }]);

    try {
      const response = await askQuestion({
        session_id: session.session_id,
        message: userQuestion
      });
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          citations: response.citations
        }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not answer question.");
    } finally {
      setIsAsking(false);
    }
  }

  async function handleFile(file: File | null) {
    if (!file) {
      return;
    }

    const text = await file.text();
    setTranscript(text);
    if (!title) {
      setTitle(file.name.replace(/\.[^/.]+$/, ""));
    }
  }

  return (
    <main className="min-h-screen bg-paper">
      <div className="mx-auto grid min-h-screen max-w-7xl grid-cols-1 lg:grid-cols-[420px_1fr]">
        <section className="border-b border-line bg-white p-5 lg:border-b-0 lg:border-r">
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-ink text-white">
              <MessageSquareText size={20} />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Transcript Chat</h1>
              <p className="text-sm text-neutral-500">Index a transcript and ask grounded questions.</p>
            </div>
          </div>

          <form onSubmit={handleTranscriptSubmit} className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm font-medium">Video title</span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="w-full rounded-md border border-line bg-white px-3 py-2 outline-none focus:border-accent"
                placeholder="System design interview guide"
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-sm font-medium">YouTube link</span>
              <input
                value={sourceUrl}
                onChange={(event) => setSourceUrl(event.target.value)}
                className="w-full rounded-md border border-line bg-white px-3 py-2 outline-none focus:border-accent"
                placeholder="https://www.youtube.com/watch?v=..."
              />
            </label>

            <label className="flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-line bg-neutral-50 px-3 py-3 text-sm font-medium hover:bg-neutral-100">
              <Upload size={17} />
              Upload .txt, .srt, or .vtt transcript
              <input
                type="file"
                accept=".txt,.srt,.vtt"
                className="hidden"
                onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-sm font-medium">Transcript</span>
              <textarea
                value={transcript}
                onChange={(event) => setTranscript(event.target.value)}
                className="h-[360px] w-full resize-none rounded-md border border-line bg-white px-3 py-2 text-sm leading-6 outline-none focus:border-accent"
                placeholder="Paste transcript text here..."
                required
              />
            </label>

            <button
              type="submit"
              disabled={isIndexing || transcript.trim().length < 20}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isIndexing ? <Loader2 className="animate-spin" size={17} /> : <FileText size={17} />}
              Index transcript
            </button>
          </form>
        </section>

        <section className="flex min-h-screen flex-col">
          <div className="border-b border-line bg-white px-5 py-4">
            {session ? (
              <div>
                <p className="text-sm font-semibold">{session.title}</p>
                <p className="text-sm text-neutral-500">{session.chunks_count} searchable chunks ready</p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-semibold">No transcript indexed</p>
                <p className="text-sm text-neutral-500">Paste or upload a transcript to start chatting.</p>
              </div>
            )}
          </div>

          {error ? (
            <div className="m-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div className="flex-1 space-y-4 overflow-y-auto p-5">
            {messages.length === 0 ? (
              <div className="grid h-full place-items-center text-center">
                <div className="max-w-md">
                  <h2 className="text-2xl font-semibold">Ask anything from the transcript</h2>
                  <p className="mt-2 text-neutral-500">
                    Try questions about key ideas, definitions, steps, examples, or a quick summary.
                  </p>
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <article
                  key={`${message.role}-${index}`}
                  className={
                    message.role === "user"
                      ? "ml-auto max-w-2xl rounded-md bg-ink px-4 py-3 text-white"
                      : "max-w-3xl rounded-md border border-line bg-white px-4 py-3"
                  }
                >
                  <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                  {message.citations?.length ? (
                    <div className="mt-4 space-y-2 border-t border-line pt-3">
                      {message.citations.map((citation) => (
                        <details key={citation.chunk_id} className="text-sm">
                          <summary className="cursor-pointer font-medium text-accent">
                            {citation.timestamp ? `Source ${citation.timestamp}` : `Source ${citation.chunk_id}`}
                          </summary>
                          <p className="mt-2 line-clamp-4 text-neutral-600">{citation.text}</p>
                        </details>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))
            )}
          </div>

          <form onSubmit={handleAsk} className="border-t border-line bg-white p-4">
            <div className="flex gap-3">
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                disabled={!session}
                className="min-w-0 flex-1 rounded-md border border-line px-3 py-2 outline-none focus:border-accent disabled:bg-neutral-100"
                placeholder={session ? "Ask a question..." : "Index a transcript first"}
              />
              <button
                type="submit"
                disabled={!session || isAsking || !question.trim()}
                className="grid h-11 w-11 place-items-center rounded-md bg-accent text-white disabled:cursor-not-allowed disabled:opacity-50"
                aria-label="Send question"
              >
                {isAsking ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}

