import asyncio
from types import SimpleNamespace
from pathlib import Path

from cogs.music import Music, PlaylistBrowseView


class DummyResponse:
    def __init__(self):
        self.calls = []

    async def defer(self, ephemeral=False):
        self.calls.append(("defer", ephemeral))


class DummyFollowup:
    def __init__(self):
        self.messages = []

    async def send(self, **kwargs):
        self.messages.append(kwargs)


class DummyChannel:
    def __init__(self, name="music"):
        self.name = name


class DummyVoice:
    def __init__(self, channel):
        self.channel = channel


class DummyUser:
    def __init__(self, user_id=1, channel=None):
        self.id = user_id
        self.voice = DummyVoice(channel) if channel else None


class DummyGuild:
    def __init__(self, guild_id=10, voice_client=None):
        self.id = guild_id
        self.voice_client = voice_client


class DummyInteraction:
    def __init__(self, guild, user, channel=None):
        self.guild = guild
        self.user = user
        self.channel = channel or DummyChannel()
        self.response = DummyResponse()
        self.followup = DummyFollowup()


class DummyQueue:
    def __init__(self, items=None):
        self.items = list(items or [])
        self.mode = None

    async def put_wait(self, item):
        self.items.append(item)

    def get(self):
        if not self.items:
            return None
        return self.items.pop(0)

    def clear(self):
        self.items.clear()

    def __len__(self):
        return len(self.items)


class DummyPlayer:
    def __init__(self, channel, queue=None):
        self.channel = channel
        self.queue = queue or DummyQueue()
        self.playing = False
        self.current = None
        self.play_calls = []

    async def play(self, track):
        self.playing = True
        self.current = track
        self.play_calls.append(track)

    async def stop(self):
        self.playing = False
        self.current = None


def make_cog(tmp_path: Path):
    bot = SimpleNamespace(config={"PLAYLIST_STORE_PATH": str(tmp_path / "playlists.json")})
    return Music(bot)


def run(coro):
    asyncio.run(coro)


def test_playlist_create_and_add_work(tmp_path: Path, monkeypatch):
    cog = make_cog(tmp_path)
    interaction = DummyInteraction(guild=DummyGuild(42), user=DummyUser(7))

    async def fake_build_track_label(query):
        return query

    monkeypatch.setattr(cog, "_build_track_label", fake_build_track_label)

    run(cog.playlist_create.callback(cog, interaction, name="Chill", description="For evening"))
    run(cog.playlist_add.callback(cog, interaction, name="Chill", query="https://example.com/track-1"))

    playlist = cog.playlist_store.get_playlist(42, "Chill")

    assert playlist is not None
    assert playlist["name"] == "Chill"
    assert playlist["description"] == "For evening"
    assert playlist["tracks"] == [
        {"query": "https://example.com/track-1", "label": "https://example.com/track-1"}
    ]
    assert len(interaction.response.calls) == 2
    assert all(call[1] is True for call in interaction.response.calls)
    assert len(interaction.followup.messages) == 2
    assert "создан" in interaction.followup.messages[0]["embed"].description.lower()
    assert "добавлен" in interaction.followup.messages[1]["embed"].description.lower()


def test_playlist_play_enqueues_tracks_and_starts_playback(tmp_path: Path, monkeypatch):
    cog = make_cog(tmp_path)
    channel = DummyChannel("music")
    player = DummyPlayer(channel, queue=DummyQueue())
    guild = DummyGuild(55, voice_client=player)
    interaction = DummyInteraction(guild=guild, user=DummyUser(9, channel=channel))

    cog.playlist_store.create_playlist(55, "Morning", 9, "")
    cog.playlist_store.add_track(55, "Morning", "query-1")
    cog.playlist_store.add_track(55, "Morning", "query-2")

    tracks = [
        SimpleNamespace(title="Track 1", uri="https://example.com/1"),
        SimpleNamespace(title="Track 2", uri="https://example.com/2"),
    ]

    async def fake_load_playables(query):
        if query == "query-1":
            return [tracks[0]]
        if query == "query-2":
            return [tracks[1]]
        return []

    monkeypatch.setattr(cog, "_load_playables", fake_load_playables)

    run(cog.playlist_play.callback(cog, interaction, name="Morning"))

    assert len(player.queue) == 1
    assert player.play_calls == [tracks[0]]
    assert player.current == tracks[0]
    assert len(interaction.followup.messages) == 1
    assert "добавлено" in interaction.followup.messages[0]["embed"].description.lower()


def test_playlist_browse_refresh_after_delete(tmp_path: Path):
    cog = make_cog(tmp_path)
    cog.playlist_store.create_playlist(1, "First", 100)
    cog.playlist_store.create_playlist(1, "Second", 100)

    playlists = cog.playlist_store.list_playlists(1)
    view = PlaylistBrowseView(cog, 1, playlists)

    assert view.selected == "first"

    cog.playlist_store.delete_playlist(1, "First")
    view.playlists = cog.playlist_store.list_playlists(1)

    view._refresh_select()

    assert view.selected == "second"
    assert [option.label for option in view.select.options] == ["Second"]


def test_playlist_browse_refresh_handles_empty_list(tmp_path: Path):
    cog = make_cog(tmp_path)
    cog.playlist_store.create_playlist(1, "Only", 100)

    view = PlaylistBrowseView(cog, 1, cog.playlist_store.list_playlists(1))

    cog.playlist_store.delete_playlist(1, "Only")
    view.playlists = cog.playlist_store.list_playlists(1)

    view._refresh_select()

    assert view.selected is None
    assert view.select.disabled is True
    assert [option.label for option in view.select.options] == ["Плейлистов нет"]
    assert view.btn_play.disabled is True
    assert view.btn_show.disabled is True
    assert view.btn_delete.disabled is True
