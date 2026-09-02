import json
from pathlib import Path

from knowledge_base_loader import KnowledgeBaseLoader


BASE_DIR = Path(__file__).resolve().parents[1]
DOCSTORE_PATH = BASE_DIR / "storage" / "rag_index" / "docstore.json"


def test_loads_unique_public_knowledge_chunks() -> None:
    chunks = KnowledgeBaseLoader().load()
    source_ids = [chunk.source_id for chunk in chunks]

    assert chunks
    assert len(source_ids) == len(set(source_ids))
    assert all(chunk.source != "09_missing_information.md" for chunk in chunks)
    assert any("Firestore 後台" in chunk.content for chunk in chunks)


def test_persisted_index_matches_current_knowledge_base() -> None:
    chunks = KnowledgeBaseLoader().load()
    docstore = json.loads(DOCSTORE_PATH.read_text(encoding="utf-8"))
    indexed_nodes = docstore["docstore/data"].values()
    indexed_source_ids = {
        node["__data__"]["metadata"]["source_id"]
        for node in indexed_nodes
    }

    assert indexed_source_ids == {chunk.source_id for chunk in chunks}
