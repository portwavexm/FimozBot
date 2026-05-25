from pathlib import Path

from utils.playlist_store import PlaylistStore


def test_create_add_list_and_delete_playlist(tmp_path: Path):
    store_path = tmp_path / "playlists.json"
    store = PlaylistStore(store_path)

    created = store.create_playlist(123, "Lo-Fi", 42, "Для релакса")
    assert created is True

    added = store.add_track(123, "Lo-Fi", "https://example.com/track-1", "Track 1")
    assert added is True

    playlists = store.list_playlists(123)
    assert len(playlists) == 1
    assert playlists[0]["name"] == "Lo-Fi"
    assert playlists[0]["description"] == "Для релакса"
    assert playlists[0]["owner_id"] == 42
    assert playlists[0]["tracks"] == [
        {"query": "https://example.com/track-1", "label": "Track 1"}
    ]

    removed = store.remove_track(123, "Lo-Fi", 0)
    assert removed is True
    assert store.get_playlist(123, "Lo-Fi")["tracks"] == []

    deleted = store.delete_playlist(123, "Lo-Fi")
    assert deleted is True
    assert store.list_playlists(123) == []


def test_playlist_store_persists_between_instances(tmp_path: Path):
    store_path = tmp_path / "playlists.json"

    first = PlaylistStore(store_path)
    assert first.create_playlist(777, "Roadtrip", 99, "Песни в дорогу") is True
    assert first.add_track(777, "Roadtrip", "ytsearch:lofi beats", "Lo-fi beats") is True

    second = PlaylistStore(store_path)
    playlists = second.list_playlists(777)

    assert len(playlists) == 1
    assert playlists[0]["name"] == "Roadtrip"
    assert playlists[0]["tracks"] == [
        {"query": "ytsearch:lofi beats", "label": "Lo-fi beats"}
    ]


def test_rename_playlist_keeps_tracks(tmp_path: Path):
    store = PlaylistStore(tmp_path / "playlists.json")

    assert store.create_playlist(321, "Old Name", 1) is True
    assert store.add_track(321, "Old Name", "https://example.com/track-2") is True

    renamed = store.rename_playlist(321, "Old Name", "New Name")
    assert renamed is True

    playlist = store.get_playlist(321, "New Name")
    assert playlist is not None
    assert playlist["name"] == "New Name"
    assert playlist["tracks"] == [{"query": "https://example.com/track-2", "label": "https://example.com/track-2"}]
    assert store.get_playlist(321, "Old Name") is None
