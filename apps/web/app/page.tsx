"use client";

import Image from "next/image";
import { FormEvent, ReactNode, useState } from "react";
import { CheckCircle2, FileText, Loader2, MessageSquareText, Send, Upload } from "lucide-react";

import { askQuestion, ChatResponse, createTranscript, importYouTubeVideo, TranscriptCreated } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: ChatResponse["citations"];
};

const avatars = {
  user: {
    src: "/avatars/user.png",
    alt: "User"
  },
  assistant: {
    src: "/avatars/assistant.png",
    alt: "Assistant"
  }
} as const;

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
  const [successMessage, setSuccessMessage] = useState("");

  async function handleTranscriptSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccessMessage("");
    setIsIndexing(true);

    try {
      const created = transcript.trim()
        ? await createTranscript({
            title: title || "Untitled video",
            source_url: sourceUrl || undefined,
            transcript
          })
        : await importYouTubeVideo({
            url: sourceUrl,
            title: title || undefined
          });
      setSession(created);
      setMessages([]);
      setQuestion("");
      setTitle("");
      setSourceUrl("");
      setTranscript("");
      setSuccessMessage(`${created.title} indexed successfully with ${created.chunks_count} searchable chunks.`);
    } catch (err) {
      setSuccessMessage("");
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
      <div className="mx-auto grid min-h-screen max-w-7xl  grid-cols-1 lg:grid-cols-[420px_1fr]">
        <section className="border-b border-line  bg-blue-100 p-5 lg:border-b-0 lg:border-r">
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-blue-600 text-white">
              <MessageSquareText size={20} />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Youtube Chatbot</h1>
              <p className="text-sm text-neutral-500">Paste a YouTube link or upload a transcript</p>
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

            <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border bg-blue-400 border-dashed border-line  px-3 py-3 text-sm font-medium hover:bg-blue-200">
              <Upload size={17} />
              Upload .txt /.srt /.vtt transcript
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
                placeholder="Optional if the YouTube video has captions. Paste transcript text here as fallback..."
              />
            </label>

            <button
              type="submit"
              disabled={isIndexing || (!sourceUrl.trim() && transcript.trim().length < 20)}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isIndexing ? <Loader2 className="animate-spin" size={17} /> : <FileText size={17} />}
              {transcript.trim() ? "Index transcript" : "Index YouTube video"}
            </button>
          </form>
        </section>

        <section className="flex min-h-screen flex-col">
          <div className="border-b border-line  px-5 py-4">
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

          {successMessage ? (
            <div
              role="status"
              className="m-5 flex items-start gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900 shadow-sm"
            >
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
              <div>
                <p className="font-semibold">Transcript indexed</p>
                <p className="mt-0.5 text-emerald-700">{successMessage}</p>
              </div>
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
              messages.map((message, index) => {
                const isUser = message.role === "user";
                const avatar = isUser ? avatars.user : avatars.assistant;

                return (
                  <div
                    key={`${message.role}-${index}`}
                    className={`flex items-start gap-3 ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    {!isUser ? (
                      <Image
                        src={avatar.src}
                        alt={avatar.alt}
                        width={36}
                        height={36}
                        className="mt-1 h-10 w-10 shrink-0 rounded-full border border-black border-line bg-white"
                      />
                    ) : null}

                    <article
                      className={
                        isUser
                          ? "max-w-[calc(100%-3rem)] rounded-lg bg-blue-500 px-4 py-3 text-white sm:max-w-2xl"
                          : "max-w-[calc(100%-3rem)] rounded-lg border border-line bg-white px-4 py-3 sm:max-w-3xl"
                      }
                    >
                      <MarkdownMessage content={message.content} isUser={isUser} />
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

                    {isUser ? (
                      <Image
                        src={avatar.src}
                        alt={avatar.alt}
                        width={36}
                        height={36}
                        className="mt-1 h-9 w-9 shrink-0 rounded-full border border-black border-line bg-white"
                      />
                    ) : null}
                  </div>
                );
              })
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

function MarkdownMessage({ content, isUser }: { content: string; isUser: boolean }) {
  const blocks = parseMarkdownBlocks(content);
  const linkText = isUser ? "text-white" : "text-accent";
  const codeClass = isUser ? "bg-white/20 text-white" : "bg-neutral-100 text-ink";

  return (
    <div className="text-sm leading-6">
      {blocks.map((block, index) => {
        if (block.type === "unordered-list") {
          return (
            <ul key={index} className="mb-3 ml-5 list-disc space-y-1 last:mb-0">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex} className="pl-1">
                  {renderInlineMarkdown(item, linkText, codeClass)}
                </li>
              ))}
            </ul>
          );
        }

        if (block.type === "ordered-list") {
          return (
            <ol key={index} className="mb-3 ml-5 list-decimal space-y-1 last:mb-0">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex} className="pl-1">
                  {renderInlineMarkdown(item, linkText, codeClass)}
                </li>
              ))}
            </ol>
          );
        }

        return (
          <p key={index} className="mb-2 whitespace-pre-wrap last:mb-0">
            {renderInlineMarkdown(block.text, linkText, codeClass)}
          </p>
        );
      })}
    </div>
  );
}

type MarkdownBlock =
  | { type: "paragraph"; text: string }
  | { type: "unordered-list"; items: string[] }
  | { type: "ordered-list"; items: string[] };

function parseMarkdownBlocks(content: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = [];
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  let paragraph: string[] = [];

  function flushParagraph() {
    if (paragraph.length) {
      blocks.push({ type: "paragraph", text: paragraph.join("\n") });
      paragraph = [];
    }
  }

  for (const line of lines) {
    const unordered = line.match(/^\s*[-*]\s+(.+)$/);
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);

    if (!line.trim()) {
      flushParagraph();
      continue;
    }

    if (unordered) {
      flushParagraph();
      const previous = blocks[blocks.length - 1];
      if (previous?.type === "unordered-list") {
        previous.items.push(unordered[1]);
      } else {
        blocks.push({ type: "unordered-list", items: [unordered[1]] });
      }
      continue;
    }

    if (ordered) {
      flushParagraph();
      const previous = blocks[blocks.length - 1];
      if (previous?.type === "ordered-list") {
        previous.items.push(ordered[1]);
      } else {
        blocks.push({ type: "ordered-list", items: [ordered[1]] });
      }
      continue;
    }

    paragraph.push(line);
  }

  flushParagraph();
  return blocks;
}

function renderInlineMarkdown(text: string, linkClass: string, codeClass: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*([^*]+)\*\*|__([^_]+)__|`([^`]+)`|\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|\*([^*]+)\*|_([^_]+)_)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }

    if (match[2] || match[3]) {
      nodes.push(
        <strong key={match.index} className="font-semibold">
          {match[2] ?? match[3]}
        </strong>
      );
    } else if (match[4]) {
      nodes.push(
        <code key={match.index} className={`rounded px-1.5 py-0.5 font-mono text-[0.85em] ${codeClass}`}>
          {match[4]}
        </code>
      );
    } else if (match[5] && match[6]) {
      nodes.push(
        <a key={match.index} className={`${linkClass} underline underline-offset-2`} href={match[6]} rel="noreferrer" target="_blank">
          {match[5]}
        </a>
      );
    } else {
      nodes.push(
        <em key={match.index} className="italic">
          {match[7] ?? match[8]}
        </em>
      );
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }

  return nodes;
}