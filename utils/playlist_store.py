import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class PlaylistStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: Dict[str, Any] = {"guilds": {}}
        self._ensure_file()
        self.load()

    def _ensure_file(self) -> None:
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> None:
        try:
            text = self.path.read_text(encoding="utf-8")
            self.data = json.loads(text) if text.strip() else {"guilds": {}}
        except Exception:
            self.data = {"guilds": {}}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _guild(self, guild_id: int) -> Dict[str, Any]:
        guild_key = str(guild_id)
        if guild_key not in self.data["guilds"]:
            self.data["guilds"][guild_key] = {"playlists": {}}
        return self.data["guilds"][guild_key]

    def _playlist_key(self, name: str) -> str:
        return name.strip().lower()

    def create_playlist(self, guild_id: int, name: str, owner_id: int, description: str = "") -> bool:
        guild = self._guild(guild_id)
        key = self._playlist_key(name)
        if key in guild["playlists"]:
            return False
        guild["playlists"][key] = {
            "name": name.strip(),
            "description": description.strip(),
            "owner_id": owner_id,
            "tracks": [],
        }
        self.save()
        return True

    def delete_playlist(self, guild_id: int, name: str) -> bool:
        guild = self._guild(guild_id)
        key = self._playlist_key(name)
        if key not in guild["playlists"]:
            return False
        guild["playlists"].pop(key)
        self.save()
        return True

    def add_track(self, guild_id: int, name: str, query: str, label: str | None = None) -> bool:
        playlist = self.get_playlist(guild_id, name)
        if not playlist:
            return False
        playlist["tracks"].append({"query": query.strip(), "label": label or query.strip()})
        self.save()
        return True

    def remove_track(self, guild_id: int, name: str, index: int) -> bool:
        playlist = self.get_playlist(guild_id, name)
        if not playlist:
            return False
        if index < 0 or index >= len(playlist["tracks"]):
            return False
        playlist["tracks"].pop(index)
        self.save()
        return True

    def get_playlist(self, guild_id: int, name: str) -> Optional[Dict[str, Any]]:
        guild = self._guild(guild_id)
        return guild["playlists"].get(self._playlist_key(name))

    def list_playlists(self, guild_id: int) -> List[Dict[str, Any]]:
        guild = self._guild(guild_id)
        return [
            {"key": key, **playlist}
            for key, playlist in guild["playlists"].items()
        ]

    def rename_playlist(self, guild_id: int, old_name: str, new_name: str) -> bool:
        guild = self._guild(guild_id)
        old_key = self._playlist_key(old_name)
        if old_key not in guild["playlists"]:
            return False
        new_key = self._playlist_key(new_name)
        if new_key in guild["playlists"] and new_key != old_key:
            return False
        playlist = guild["playlists"].pop(old_key)
        playlist["name"] = new_name.strip()
        guild["playlists"][new_key] = playlist
        self.save()
        return True
