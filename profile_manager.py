"""Local profile storage (one profile, one JSON file).

The file lives at ``<data_dir>/profile.json``. It is NOT encrypted and there is
no login: anyone who can read your Windows user folder can read it. Do not use
this as a multi-user or cloud store.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

from modules.validator import validate_profile

log = logging.getLogger("intelliform.profile")


class ProfileCorruptError(Exception):
    """The profile file exists but cannot be read."""


class ProfileManager:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.path = self.data_dir / "profile.json"
        self._lock = threading.Lock()

    def load(self) -> dict | None:
        """Return ``{"profile": {...}, "updated_at": str}`` or None if no profile."""
        with self._lock:
            if not self.path.is_file():
                return None
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                profile = payload["profile"]
                if not isinstance(profile, dict):
                    raise ValueError("profile is not an object")
            except (OSError, ValueError, KeyError) as exc:
                log.warning("profile file unreadable: %s", type(exc).__name__)
                raise ProfileCorruptError("The saved profile file could not be read.") from exc
            return {"profile": profile, "updated_at": payload.get("updated_at", "")}

    def save(self, data) -> tuple[dict | None, dict]:
        """Validate and save. Returns ``(saved_record, errors)``."""
        clean, errors = validate_profile(data)
        if errors:
            return None, errors
        record = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "profile": clean,
        }
        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self.data_dir, prefix=".profile-", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(record, handle, indent=2, ensure_ascii=False)
                os.replace(tmp, self.path)  # atomic: never leaves a half-written file
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
        log.info("profile saved (%d fields)", len(clean))
        return {"profile": clean, "updated_at": record["updated_at"]}, {}

    def delete(self) -> bool:
        with self._lock:
            if self.path.is_file():
                self.path.unlink()
                log.info("profile deleted")
                return True
            return False
