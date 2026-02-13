import json
import random
from pathlib import Path
from typing import Iterable


class FunContentManager:
    def __init__(
        self,
        lang: str = "de",
        include_types: Iterable[str] = ("fact", "joke"),
        max_length: int = 120,
    ):
        self.lang = (lang or "de").lower()
        self.include_types = set(include_types or ("fact", "joke"))
        self.max_length = int(max_length)
        self._items = self._load_items()
        self._bag = []
        self._rng = random.SystemRandom()

    def _data_file_candidates(self):
        root = Path(__file__).resolve().parent.parent
        primary = root / "data" / f"fun_content_{self.lang}.json"
        fallback = root / "data" / "fun_content_de.json"
        return [primary, fallback]

    def _load_items(self):
        file_path = None
        for candidate in self._data_file_candidates():
            if candidate.exists():
                file_path = candidate
                break
        if not file_path:
            return []

        raw = json.loads(file_path.read_text(encoding="utf-8"))
        items = []
        for entry in raw:
            text = str(entry.get("text", "")).strip()
            entry_type = str(entry.get("type", "")).strip().lower()
            if not text or entry_type not in self.include_types:
                continue
            if len(text) > self.max_length:
                text = text[: self.max_length - 1].rstrip() + "..."
            items.append({"type": entry_type, "text": text})
        return items

    def _refill_bag(self):
        self._bag = list(self._items)
        self._rng.shuffle(self._bag)

    def next_text(self) -> str:
        if not self._items:
            return ""
        if not self._bag:
            self._refill_bag()
        item = self._bag.pop()
        return item["text"]
