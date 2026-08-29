import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeChunk:
    source_id: str
    source: str
    section: str
    content: str
    priority: int


class KnowledgeBaseLoader:
    """讀取 manifest.json 指定的 Markdown，並依標題切成知識片段。"""

    HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+?)\s*$")

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = (
            base_dir
            if base_dir is not None
            else Path(__file__).resolve().parent / "knowledge_base"
        )

        self.manifest_path = self.base_dir / "manifest.json"

    def load(self) -> list[KnowledgeChunk]:
        manifest = self._load_manifest()
        chunks: list[KnowledgeChunk] = []

        for document in manifest["documents"]:
            if not document.get("index", False):
                continue

            relative_path = Path(document["path"])
            document_path = self.base_dir / relative_path

            if not document_path.exists():
                raise FileNotFoundError(
                    f"知識庫文件不存在：{document_path}"
                )

            text = document_path.read_text(encoding="utf-8")
            text = self._remove_frontmatter(text)

            document_chunks = self._split_markdown(
                text=text,
                source=relative_path.as_posix(),
                priority=document.get("priority", 0),
            )

            chunks.extend(document_chunks)

        return chunks

    def _load_manifest(self) -> dict:
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"找不到 manifest.json：{self.manifest_path}"
            )

        return json.loads(
            self.manifest_path.read_text(encoding="utf-8")
        )

    @staticmethod
    def _remove_frontmatter(text: str) -> str:
        """移除 Markdown 開頭的 YAML frontmatter。"""

        if not text.startswith("---"):
            return text

        parts = text.split("---", 2)

        if len(parts) != 3:
            return text

        return parts[2].lstrip()

    def _split_markdown(
        self,
        text: str,
        source: str,
        priority: int,
    ) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []

        current_section = "文件摘要"
        current_lines: list[str] = []
        chunk_number = 1

        def save_chunk() -> None:
            nonlocal chunk_number

            content = "\n".join(current_lines).strip()

            if not content:
                return

            source_name = (
                source.removesuffix(".md")
                .replace("/", ".")
            )

            chunks.append(
                KnowledgeChunk(
                    source_id=f"{source_name}.{chunk_number:03d}",
                    source=source,
                    section=current_section,
                    content=f"{current_section}\n{content}",
                    priority=priority,
                )
            )

            chunk_number += 1

        for line in text.splitlines():
            heading_match = self.HEADING_PATTERN.match(line)

            if heading_match:
                save_chunk()

                current_section = heading_match.group(2).strip()
                current_lines = []
                continue

            current_lines.append(line)

        save_chunk()

        return chunks


if __name__ == "__main__":
    loader = KnowledgeBaseLoader()
    knowledge_chunks = loader.load()

    print(f"成功載入 {len(knowledge_chunks)} 個知識片段")

    for chunk in knowledge_chunks[:5]:
        print()
        print(f"來源 ID：{chunk.source_id}")
        print(f"來源文件：{chunk.source}")
        print(f"段落：{chunk.section}")
        print(f"內容預覽：{chunk.content[:100]}")