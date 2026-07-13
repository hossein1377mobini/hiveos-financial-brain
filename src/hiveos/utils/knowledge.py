"""
Knowledge Manager - manages the product knowledge base for HiveOS.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()

class KnowledgeManager:
    """Manages HiveOS product knowledge base."""
    
    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = Path(knowledge_dir)
    
    def get_document(self, path: str) -> Optional[str]:
        """Read a knowledge document by relative path."""
        full_path = self.knowledge_dir / path
        if not full_path.exists():
            console.print(f"⚠️  Knowledge document not found: {path}")
            return None
        return full_path.read_text(encoding="utf-8")
    
    def list_documents(self, prefix: str = "") -> List[Path]:
        """List all knowledge documents, optionally filtered by prefix."""
        if prefix:
            return list(self.knowledge_dir.glob(f"{prefix}**/*.md"))
        return list(self.knowledge_dir.rglob("*.md"))
    
    def get_structure(self) -> Dict[str, Any]:
        """Get the knowledge base directory tree."""
        return self._dir_to_dict(self.knowledge_dir)
    
    def _dir_to_dict(self, path: Path) -> Dict[str, Any]:
        """Convert a directory to a nested dict structure."""
        result = {}
        for item in sorted(path.iterdir()):
            if item.name.startswith("."):
                continue
            if item.is_dir():
                children = self._dir_to_dict(item)
                if children:
                    result[item.name] = children
            elif item.suffix in (".md", ".yaml", ".yml", ".json"):
                result[item.name] = str(item.relative_to(self.knowledge_dir))
        return result
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge documents for a query string."""
        results = []
        for doc in self.knowledge_dir.rglob("*.md"):
            content = doc.read_text(encoding="utf-8")
            if query.lower() in content.lower():
                results.append({
                    "path": str(doc.relative_to(self.knowledge_dir)),
                    "match_count": content.lower().count(query.lower()),
                })
        return sorted(results, key=lambda r: r["match_count"], reverse=True)
