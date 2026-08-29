from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.schema import MetadataMode, TextNode
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

from knowledge_base_loader import KnowledgeBaseLoader


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
PERSIST_DIR = BASE_DIR / "storage" / "rag_index"
EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class RetrievalResult:
    source_id: str
    source: str
    section: str
    content: str
    score: float | None


class RagService:
    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

        if not project_id:
            raise RuntimeError(".env 缺少 GOOGLE_CLOUD_PROJECT")

        self.embed_model = GoogleGenAIEmbedding(
            model_name=EMBEDDING_MODEL,
            vertexai_config={
                "project": project_id,
                "location": location,
            },
        )
        self.index = self._load_or_build_index()

    def _load_or_build_index(self) -> VectorStoreIndex:
        index_store = PERSIST_DIR / "index_store.json"

        if index_store.exists():
            storage_context = StorageContext.from_defaults(
                persist_dir=str(PERSIST_DIR)
            )
            print(f"載入既有索引：{PERSIST_DIR}")
            return load_index_from_storage(
                storage_context,
                embed_model=self.embed_model,
            )

        print("尚未找到索引，開始建立 Embedding...")
        chunks = KnowledgeBaseLoader(KNOWLEDGE_BASE_DIR).load()

        if not chunks:
            raise RuntimeError("知識庫沒有可建立索引的內容")

        nodes: list[TextNode] = []
        for chunk in chunks:
            node_id = sha256(
                f"{chunk.source_id}\n{chunk.section}\n{chunk.content}".encode("utf-8")
            ).hexdigest()

            nodes.append(
                TextNode(
                    id_=node_id,
                    text=chunk.content,
                    metadata={
                        "source_id": chunk.source_id,
                        "source": chunk.source,
                        "section": chunk.section,
                        "priority": chunk.priority,
                    },
                    excluded_embed_metadata_keys=["source", "priority"],
                    excluded_llm_metadata_keys=["priority"],
                )
            )

        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=self.embed_model,
            show_progress=True,
        )
        PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(persist_dir=str(PERSIST_DIR))
        print(f"已建立 {len(nodes)} 個知識片段，索引保存於：{PERSIST_DIR}")
        return index

    def retrieve(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[RetrievalResult]:
        question = question.strip()
        if not question:
            raise ValueError("問題不可為空白")

        retriever = self.index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(question)

        return [
            RetrievalResult(
                source_id=str(item.node.metadata.get("source_id", "")),
                source=str(item.node.metadata.get("source", "")),
                section=str(item.node.metadata.get("section", "")),
                content=item.node.get_content(metadata_mode=MetadataMode.NONE),
                score=float(item.score) if item.score is not None else None,
            )
            for item in nodes
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description="測試個人知識庫的 Embedding 檢索")
    parser.add_argument("question", nargs="?", help="要搜尋的問題")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()

    question = args.question or input("請輸入測試問題：").strip()
    service = RagService()
    results = service.retrieve(question, top_k=args.top_k)

    print(f'\n問題：{question}')
    for number, result in enumerate(results, start=1):
        score = f"{result.score:.4f}" if result.score is not None else "N/A"
        print(f"\n[{number}] score={score}")
        print(f"來源：{result.source} / {result.section}")
        print(result.content)


if __name__ == "__main__":
    main()