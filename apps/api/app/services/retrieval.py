from dataclasses import dataclass

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


@dataclass
class SearchResult:
    document: Document
    score: float

    @property
    def chunk_id(self) -> str:
        return str(self.document.metadata.get("chunk_id", "chunk"))

    @property
    def text(self) -> str:
        return self.document.page_content


class RagIndex:
    def __init__(self, transcript: str, source: str | None = None) -> None:
        settings = get_settings()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.documents = self._create_documents(transcript, source)
        self.embeddings = _build_embeddings()
        self.vector_store = FAISS.from_documents(self.documents, self.embeddings)
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.retrieval_k},
        )

    @property
    def chunks_count(self) -> int:
        return len(self.documents)

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        if top_k is not None:
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": top_k},
            )
        else:
            retriever = self.retriever

        documents = retriever.invoke(query)
        return [
            SearchResult(document=document, score=1.0 / rank)
            for rank, document in enumerate(documents, start=1)
        ]

    def _create_documents(self, transcript: str, source: str | None) -> list[Document]:
        base_document = Document(
            page_content=transcript,
            metadata={"source": source or "manual-transcript"},
        )
        documents = self.splitter.split_documents([base_document])

        for index, document in enumerate(documents, start=1):
            document.metadata["chunk_id"] = f"chunk-{index}"

        return documents


def _build_embeddings() -> Embeddings:
    settings = get_settings()
    provider = settings.embedding_provider.lower().strip()

    if provider == "openai" and settings.openai_api_key:
        from langchain_openai import OpenAIEmbeddings

        print(
            f"[rag] Using OpenAIEmbeddings model={settings.openai_embedding_model}.",
            flush=True,
        )
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )

    if provider == "openai" and not settings.openai_api_key:
        print("[rag] OPENAI_API_KEY missing. Falling back to Hugging Face embeddings.", flush=True)

    from langchain_huggingface import HuggingFaceEmbeddings

    print(f"[rag] Using HuggingFaceEmbeddings model={settings.embedding_model}.", flush=True)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )
