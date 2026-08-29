from knowledge_base_loader import KnowledgeBaseLoader


def test_loads_unique_public_knowledge_chunks() -> None:
    chunks = KnowledgeBaseLoader().load()
    source_ids = [chunk.source_id for chunk in chunks]

    assert len(chunks) == 67
    assert len(source_ids) == len(set(source_ids))
    assert all(chunk.source != "09_missing_information.md" for chunk in chunks)
    assert any("Firestore 後台" in chunk.content for chunk in chunks)
