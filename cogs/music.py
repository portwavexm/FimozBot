import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import re
import logging
import asyncio

from utils.spotify import SpotifyAPI
from utils.playlist_store import PlaylistStore

log = logging.getLogger(__name__)
URL_REGEX = re.compile(
    r'https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}'
    r'\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)'
)

# ──────────────────────────────────────────────────────────
#  ЦВЕТОВАЯ ПАЛИТРА
# ──────────────────────────────────────────────────────────
COLOR_MAIN    = 0x5865F2
COLOR_SUCCESS = 0x57F287
COLOR_ERROR   = 0xED4245
COLOR_WARN    = 0xFEE75C
COLOR_MUTED   = 0x4F545C
COLOR_NOW     = 0xEB459E

# ──────────────────────────────────────────────────────────
#  УТИЛИТЫ
# ──────────────────────────────────────────────────────────
def fmt_time(ms: int) -> str:
    s = ms // 1000
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def make_progress_bar(position_ms: int, length_ms: int, width: int = 18) -> str:
    if length_ms <= 0:
        return "─" * width
    ratio  = min(position_ms / length_ms, 1.0)
    filled = round(ratio * width)
    return "─" * filled + "●" + "─" * (width - filled)


def get_thumbnail(track: wavelink.Playable) -> str | None:
    return getattr(track, "artwork", None) or getattr(track, "thumbnail", None)


# ──────────────────────────────────────────────────────────
#  EMBED-БИЛДЕРЫ
# ──────────────────────────────────────────────────────────
def embed_now_playing(
    track: wavelink.Playable,
    player: wavelink.Player,
    requester: discord.Member | None = None,
) -> discord.Embed:
    title_text  = track.title  or "Неизвестный трек"
    author_text = track.author or "Неизвестный исполнитель"

    pos_ms   = int(getattr(player, "position", 0) or 0)
    length   = track.length or 0
    bar      = make_progress_bar(pos_ms, length)
    time_str = f"`{fmt_time(pos_ms)}` {bar} `{fmt_time(length)}`"

    mode = getattr(player.queue, "mode", wavelink.QueueMode.normal)
    if mode == wavelink.QueueMode.loop:
        loop_icon = "🔂"
    elif mode == wavelink.QueueMode.loop_all:
        loop_icon = "🔁"
    else:
        loop_icon = "➡️"

    pause_icon = "⏸️" if player.paused else "▶️"
    vol        = getattr(player, "volume", 100)
    queue_len  = len(player.queue)

    link = f"[{title_text}]({track.uri})" if track.uri else title_text

    embed = discord.Embed(color=COLOR_NOW)
    embed.set_author(
        name="♪  Сейчас играет",
        icon_url="https://i.imgur.com/sJ0eTkN.gif",
    )
    embed.description = f"### {link}\n**{author_text}**\n\n{time_str}"

    thumb = get_thumbnail(track)
    embed.set_thumbnail(url=thumb if thumb else "attachment://default_thumbnail.png")

    embed.add_field(name="Состояние", value=f"{pause_icon} {'Пауза' if player.paused else 'Играет'}", inline=True)
    embed.add_field(name="Повтор",    value=loop_icon,                                                inline=True)
    embed.add_field(name="Громкость", value=f"🔊 {vol}%",                                             inline=True)
    embed.add_field(name="В очереди", value=f"🎶 {queue_len} трек(ов)",                               inline=True)

    if requester:
        embed.set_footer(
            text=f"Добавил: {requester.display_name}",
            icon_url=requester.display_avatar.url,
        )
    return embed


def embed_added_track(
    track: wavelink.Playable,
    position: int,
    requester: discord.Member | None = None,
) -> discord.Embed:
    length = fmt_time(track.length) if track.length else "—"
    link   = f"[{track.title}]({track.uri})" if track.uri else track.title

    embed = discord.Embed(
        description=f"**{link}**\n{track.author or 'Неизвестный исполнитель'} · `{length}`",
        color=COLOR_SUCCESS,
    )
    embed.set_author(name="✅  Добавлено в очередь")

    thumb = get_thumbnail(track)
    embed.set_thumbnail(url=thumb if thumb else "attachment://default_thumbnail.png")
    embed.add_field(name="Позиция в очереди", value=f"#{position}", inline=True)

    if requester:
        embed.set_footer(
            text=f"Добавил: {requester.display_name}",
            icon_url=requester.display_avatar.url,
        )
    return embed


def embed_added_playlist(count: int, name: str = "плейлист") -> discord.Embed:
    embed = discord.Embed(
        description=f"Добавлено **{count}** треков из {name}.",
        color=COLOR_SUCCESS,
    )
    embed.set_author(name="✅  Плейлист загружен")
    return embed


def embed_queue(player: wavelink.Player, page: int = 0, page_size: int = 10) -> discord.Embed:
    embed = discord.Embed(color=COLOR_MAIN)
    embed.set_author(name="🎶  Очередь воспроизведения")

    queue_list  = list(player.queue)
    total       = len(queue_list)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page        = max(0, min(page, total_pages - 1))
    start       = page * page_size
    slice_      = queue_list[start : start + page_size]

    lines = []
    for i, t in enumerate(slice_, start + 1):
        length = fmt_time(t.length) if t.length else "—"
        link   = f"[{t.title}]({t.uri})" if t.uri else t.title
        lines.append(f"`{i:02d}.` {link} · `{length}`")

    current_line = ""
    if player.current:
        length = fmt_time(player.current.length) if player.current.length else "—"
        link   = f"[{player.current.title}]({player.current.uri})" if player.current.uri else player.current.title
        current_line = f"**▶️ Сейчас:** {link} · `{length}`\n\n"

    embed.description = current_line + ("\n".join(lines) if lines else "*Очередь пуста*")

    footer_parts = [f"Страница {page + 1}/{total_pages}  ·  Треков: {total}"]
    total_ms = sum(t.length or 0 for t in queue_list)
    if total_ms:
        footer_parts.append(f"Общая длина: {fmt_time(total_ms)}")
    embed.set_footer(text=" · ".join(footer_parts))

    return embed


def embed_playlist_list(playlists: list[dict]) -> discord.Embed:
    embed = discord.Embed(title="Плейлисты сервера", color=COLOR_MAIN)
    if not playlists:
        embed.description = "Плейлистов нет."
        return embed

    lines = []
    for pl in playlists[:25]:
        desc = f" — {pl['description']}" if pl.get("description") else ""
        lines.append(f"**{pl['name']}** ({len(pl['tracks'])} треков){desc}")

    embed.description = "\n".join(lines)
    if len(playlists) > 25:
        embed.set_footer(text=f"Показано 25 из {len(playlists)} плейлистов")
    return embed


def embed_playlist_details(playlist: dict) -> discord.Embed:
    embed = discord.Embed(title=f"Плейлист: {playlist['name']}", color=COLOR_MAIN)
    if playlist.get("description"):
        embed.description = playlist["description"]

    embed.add_field(name="Треков", value=str(len(playlist["tracks"])), inline=True)
    embed.add_field(name="Владелец", value=f"<@{playlist['owner_id']}>", inline=True)

    if playlist["tracks"]:
        lines = []
        for idx, track in enumerate(playlist["tracks"][:15], start=1):
            label = track.get("label") or track.get("query")
            lines.append(f"`{idx}.` {label}")
        embed.add_field(name="Содержимое", value="\n".join(lines), inline=False)
        if len(playlist["tracks"]) > 15:
            embed.set_footer(text=f"Показано 15 из {len(playlist['tracks'])} треков")
    else:
        embed.add_field(name="Содержимое", value="Плейлист пуст.", inline=False)

    return embed


def embed_simple(text: str, color: int = COLOR_MUTED, icon: str = "ℹ️") -> discord.Embed:
    return discord.Embed(description=f"{icon}  {text}", color=color)


def embed_error(text: str) -> discord.Embed:
    return embed_simple(text, COLOR_ERROR, "❌")


# ──────────────────────────────────────────────────────────
#  MODAL: ДОБАВИТЬ ТРЕК / ПЛЕЙЛИСТ
#  Без style= — davey не поддерживает TextInputStyle
# ──────────────────────────────────────────────────────────
class AddTrackModal(discord.ui.Modal, title="➕  Добавить трек или плейлист"):
    query = discord.ui.TextInput(
        label="Название, ссылка или Spotify URL",
        placeholder="Imagine Dragons Believer  или  https://open.spotify.com/...",
        max_length=500,
    )

    def __init__(self, cog: "Music"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        query_str = self.query.value.strip()

        vc = interaction.user.voice
        if not vc or not vc.channel:
            await interaction.followup.send(
                embed=embed_error("Вы не в голосовом канале."), ephemeral=True
            )
            return

        guild = interaction.guild
        if guild.voice_client:
            player: wavelink.Player = guild.voice_client
            if player.channel != vc.channel:
                await player.move_to(vc.channel)
        else:
            player = await vc.channel.connect(cls=wavelink.Player, self_deaf=True)

        self.cog.last_channels[guild.id]   = interaction.channel
        self.cog.last_requesters[guild.id] = interaction.user

        try:
            is_spotify = self.cog.spotify_api and await self.cog.spotify_api.is_spotify_url(query_str)
            tracks = await self.cog._load_playables(query_str)
            if not tracks:
                await interaction.followup.send(
                    embed=embed_error("Ничего не найдено."), ephemeral=True
                )
                return
            if len(tracks) == 1:
                track = tracks[0]
                pos   = len(player.queue) + 1
                await player.queue.put_wait(track)
                await interaction.followup.send(
                    embed=embed_added_track(track, pos, interaction.user), ephemeral=True
                )
            else:
                added = 0
                for track in tracks:
                    try:
                        await player.queue.put_wait(track)
                        added += 1
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        log.warning(f"Пропущен трек {track.title if hasattr(track, 'title') else '?'}: {e}")
                await interaction.followup.send(
                    embed=embed_added_playlist(added, "плейлист"), ephemeral=True
                )

            if not player.playing:
                next_track = player.queue.get()
                await player.play(next_track)

        except commands.CommandError as e:
            await interaction.followup.send(embed=embed_error(str(e)), ephemeral=True)
        except Exception as e:
            log.error(f"AddTrackModal error: {e}", exc_info=True)
            await interaction.followup.send(embed=embed_error("Непредвиденная ошибка."), ephemeral=True)


# ──────────────────────────────────────────────────────────
#  VIEW: ПАГИНАЦИЯ ОЧЕРЕДИ
# ──────────────────────────────────────────────────────────
class QueueView(discord.ui.View):
    PAGE_SIZE = 10

    def __init__(self, cog: "Music", guild_id: int, page: int = 0):
        super().__init__(timeout=120)
        self.cog      = cog
        self.guild_id = guild_id
        self.page     = page
        self._update_buttons()

    def _player(self) -> wavelink.Player | None:
        guild = self.cog.bot.get_guild(self.guild_id)
        return guild.voice_client if guild else None

    def _total_pages(self) -> int:
        p = self._player()
        if not p:
            return 1
        total = len(p.queue)
        return max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def _update_buttons(self):
        total = self._total_pages()
        self.btn_prev_page.disabled  = self.page <= 0
        self.btn_next_page.disabled  = self.page >= total - 1
        self.btn_page_label.label    = f"{self.page + 1} / {total}"

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def btn_prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._update_buttons()
        p = self._player()
        if not p:
            await interaction.response.edit_message(embed=embed_error("Плеер недоступен."), view=None)
            return
        await interaction.response.edit_message(
            embed=embed_queue(p, self.page, self.PAGE_SIZE), view=self
        )

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True)
    async def btn_page_label(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def btn_next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self._total_pages() - 1, self.page + 1)
        self._update_buttons()
        p = self._player()
        if not p:
            await interaction.response.edit_message(embed=embed_error("Плеер недоступен."), view=None)
            return
        await interaction.response.edit_message(
            embed=embed_queue(p, self.page, self.PAGE_SIZE), view=self
        )

    @discord.ui.button(emoji="🔀", label="Шаффл", style=discord.ButtonStyle.secondary)
    async def btn_shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p or len(p.queue) < 2:
            await interaction.response.send_message(
                embed=embed_simple("Нужно минимум 2 трека.", COLOR_WARN, "⚠️"), ephemeral=True
            )
            return
        p.queue.shuffle()
        self._update_buttons()
        await interaction.response.edit_message(
            embed=embed_queue(p, self.page, self.PAGE_SIZE), view=self
        )

    @discord.ui.button(emoji="🗑️", label="Очистить", style=discord.ButtonStyle.danger)
    async def btn_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p:
            await interaction.response.send_message(
                embed=embed_error("Плеер недоступен."), ephemeral=True
            )
            return
        count = len(p.queue)
        p.queue.clear()
        self.stop()
        await interaction.response.edit_message(
            embed=embed_simple(f"Из очереди удалено {count} трек(ов).", COLOR_MUTED, "🗑️"),
            view=None,
        )


class PlaylistSelect(discord.ui.Select):
    def __init__(self, playlists: list[dict]):
        options = []
        for pl in playlists[:25]:
            desc = f"{len(pl['tracks'])} треков"
            if pl.get("description"):
                desc += f" · {pl['description'][:40]}"
            options.append(
                discord.SelectOption(
                    label=pl["name"],
                    description=desc,
                    value=pl["key"],
                )
            )
        super().__init__(placeholder="Выберите плейлист...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not view:
            return
        view.selected = self.values[0]
        view._update_buttons()
        await interaction.response.edit_message(embed=view.build_embed(), view=view)


class PlaylistBrowseView(discord.ui.View):
    def __init__(self, cog: "Music", guild_id: int, playlists: list[dict]):
        super().__init__(timeout=120)
        self.cog = cog
        self.guild_id = guild_id
        self.playlists = playlists
        self.selected = playlists[0]["key"] if playlists else None
        self.select = PlaylistSelect(playlists)
        self.add_item(self.select)
        self._update_buttons()

    def _playlist(self) -> dict | None:
        return next((pl for pl in self.playlists if pl["key"] == self.selected), None)

    def _make_options(self) -> list[discord.SelectOption]:
        return [
            discord.SelectOption(
                label=pl["name"],
                description=(f"{len(pl['tracks'])} треков" + (f" · {pl['description'][:40]}" if pl.get("description") else "")),
                value=pl["key"],
            )
            for pl in self.playlists[:25]
        ]

    def _update_buttons(self) -> None:
        active = self._playlist() is not None
        self.btn_play.disabled = not active
        self.btn_show.disabled = not active
        self.btn_delete.disabled = not active

    def _refresh_select(self) -> None:
        if self.playlists:
            self.select.disabled = False
            self.select.options = self._make_options()
            self.selected = self.playlists[0]["key"]
        else:
            self.select.disabled = True
            self.select.options = [
                discord.SelectOption(
                    label="Плейлистов нет",
                    description="Список пуст",
                    value="__empty__",
                )
            ]
            self.selected = None
        self._update_buttons()

    def build_embed(self) -> discord.Embed:
        if not self.playlists:
            return embed_simple("Плейлистов нет.", COLOR_WARN, "📭")
        playlist = self._playlist()
        if not playlist:
            return embed_playlist_list(self.playlists)

        embed = discord.Embed(
            title=f"Плейлист: {playlist['name']}",
            description=(
                f"{len(playlist['tracks'])} треков"
                + (f"\n{playlist['description']}" if playlist.get("description") else "")
            ),
            color=COLOR_MAIN,
        )
        embed.set_footer(text="Выберите плейлист в меню и нажмите кнопку")
        return embed

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="Воспроизвести", style=discord.ButtonStyle.success)
    async def btn_play(self, interaction: discord.Interaction, button: discord.ui.Button):
        playlist = self._playlist()
        if not playlist:
            await interaction.response.send_message(embed=embed_error("Выберите плейлист."), ephemeral=True)
            return
        try:
            player = await self.cog._get_player(interaction)
            self.cog.last_channels[interaction.guild.id] = interaction.channel
            self.cog.last_requesters[interaction.guild.id] = interaction.user
            added, failed = await self.cog._enqueue_query_list(player, [item["query"] for item in playlist["tracks"]])
            if failed:
                log.warning(f"Плейлист '{playlist['name']}' пропустил {len(failed)} запросов")
            await interaction.response.send_message(embed=embed_added_playlist(added, playlist['name']), ephemeral=True)
            await self.cog._start_playback_if_idle(player)
        except commands.CommandError as e:
            await interaction.response.send_message(embed=embed_error(str(e)), ephemeral=True)
        except Exception as e:
            log.error(f"Playlist browse play error: {e}", exc_info=True)
            await interaction.response.send_message(embed=embed_error("Не удалось воспроизвести плейлист."), ephemeral=True)

    @discord.ui.button(label="Показать", style=discord.ButtonStyle.secondary)
    async def btn_show(self, interaction: discord.Interaction, button: discord.ui.Button):
        playlist = self._playlist()
        if not playlist:
            await interaction.response.send_message(embed=embed_error("Выберите плейлист."), ephemeral=True)
            return
        await interaction.response.send_message(embed=embed_playlist_details(playlist), ephemeral=True)

    @discord.ui.button(label="Удалить", style=discord.ButtonStyle.danger)
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        playlist = self._playlist()
        if not playlist:
            await interaction.response.send_message(embed=embed_error("Выберите плейлист."), ephemeral=True)
            return
        if interaction.user.id != playlist["owner_id"] and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                embed=embed_error("Только автор или модератор может удалить плейлист."), ephemeral=True
            )
            return
        self.cog.playlist_store.delete_playlist(self.guild_id, playlist["name"])
        self.playlists = self.cog.playlist_store.list_playlists(self.guild_id)
        self._refresh_select()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(
            embed=embed_simple(f"Плейлист **{playlist['name']}** удалён.", COLOR_SUCCESS, "🗑️"),
            ephemeral=True,
        )


# ──────────────────────────────────────────────────────────
#  VIEW: КНОПКИ ПЛЕЕРА (Now Playing)
# ──────────────────────────────────────────────────────────
class PlayerView(discord.ui.View):
    """
    Строка 1: ⏮  ⏸/▶  ⏭  🔁  🔀
    Строка 2: 🛑  📋  ➕
    """

    def __init__(self, cog: "Music", guild_id: int):
        super().__init__(timeout=None)
        self.cog      = cog
        self.guild_id = guild_id

    def _player(self) -> wavelink.Player | None:
        guild = self.cog.bot.get_guild(self.guild_id)
        return guild.voice_client if guild else None

    async def _check(self, interaction: discord.Interaction) -> bool:
        p = self._player()
        if not p:
            await interaction.response.send_message(
                embed=embed_error("Бот не в голосовом канале."), ephemeral=True
            )
            return False
        vc = interaction.user.voice
        if not vc or vc.channel != p.channel:
            await interaction.response.send_message(
                embed=embed_error("Зайдите в тот же голосовой канал, что и бот."), ephemeral=True
            )
            return False
        return True

    # ── Строка 1 ─────────────────────────────────────────

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Перемотать трек в начало."""
        if not await self._check(interaction):
            return
        p = self._player()
        await p.seek(0)
        await interaction.response.send_message(
            embed=embed_simple("Трек перемотан в начало.", COLOR_MUTED, "⏮️"), ephemeral=True
        )

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0)
    async def btn_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Пауза / Возобновить."""
        if not await self._check(interaction):
            return
        p = self._player()
        if p.paused:
            await p.pause(False)
            button.emoji = discord.PartialEmoji.from_str("⏸️")
            button.style = discord.ButtonStyle.primary
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                embed=embed_simple("Воспроизведение возобновлено.", COLOR_SUCCESS, "▶️"),
                ephemeral=True,
            )
        else:
            await p.pause(True)
            button.emoji = discord.PartialEmoji.from_str("▶️")
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                embed=embed_simple("Воспроизведение приостановлено.", COLOR_MUTED, "⏸️"),
                ephemeral=True,
            )

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Пропустить трек."""
        if not await self._check(interaction):
            return
        p = self._player()

        skipped = p.current
        if not await self.cog._has_pending_track(p):
            await interaction.response.send_message(
                embed=embed_simple("Ничего не играет.", COLOR_WARN, "⚠️"), ephemeral=True
            )
            return

        try:
            await asyncio.wait_for(self.cog._advance_player(p), timeout=5)
        except Exception as e:
            log.warning(f"btn_skip fallback failed: {e}")
            await interaction.response.send_message(
                embed=embed_error("Не удалось переключить трек. Попробуйте ещё раз."),
                ephemeral=True,
            )
            return

        title = skipped.title if skipped else "текущий трек"
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"⏭️  Пропущено: **{title}**",
                color=COLOR_MUTED,
            ),
            ephemeral=True,
        )

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=0)
    async def btn_loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Циклически: off → track → queue → off."""
        if not await self._check(interaction):
            return
        p    = self._player()
        mode = p.queue.mode
        if mode == wavelink.QueueMode.normal:
            p.queue.mode = wavelink.QueueMode.loop
            button.emoji = discord.PartialEmoji.from_str("🔂")
            button.style = discord.ButtonStyle.success
            msg  = "Повтор текущего трека включён."
            icon = "🔂"
        elif mode == wavelink.QueueMode.loop:
            p.queue.mode = wavelink.QueueMode.loop_all
            button.emoji = discord.PartialEmoji.from_str("🔁")
            button.style = discord.ButtonStyle.success
            msg  = "Повтор всей очереди включён."
            icon = "🔁"
        else:
            p.queue.mode = wavelink.QueueMode.normal
            button.emoji = discord.PartialEmoji.from_str("🔁")
            button.style = discord.ButtonStyle.secondary
            msg  = "Повтор выключен."
            icon = "➡️"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            embed=embed_simple(msg, COLOR_MUTED, icon), ephemeral=True
        )

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=0)
    async def btn_shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Перемешать очередь."""
        if not await self._check(interaction):
            return
        p = self._player()
        if len(p.queue) < 2:
            await interaction.response.send_message(
                embed=embed_simple("Нужно минимум 2 трека в очереди.", COLOR_WARN, "⚠️"),
                ephemeral=True,
            )
            return
        p.queue.shuffle()
        await interaction.response.send_message(
            embed=embed_simple(
                f"Очередь из {len(p.queue)} треков перемешана.", COLOR_SUCCESS, "🔀"
            ),
            ephemeral=True,
        )

    # ── Строка 2 ─────────────────────────────────────────

    @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.danger, row=1)
    async def btn_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Остановить и покинуть канал."""
        if not await self._check(interaction):
            return
        p = self._player()
        p.queue.clear()
        await p.stop()
        await p.disconnect()
        self.cog.last_channels.pop(self.guild_id, None)
        self.cog.last_requesters.pop(self.guild_id, None)
        self.cog.now_playing_messages.pop(self.guild_id, None)
        self.stop()
        await interaction.response.edit_message(view=None)
        await interaction.followup.send(
            embed=embed_simple(
                "Воспроизведение остановлено, бот покинул канал.", COLOR_ERROR, "🛑"
            ),
            ephemeral=True,
        )

    @discord.ui.button(emoji="📋", label="Очередь", style=discord.ButtonStyle.secondary, row=1)
    async def btn_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Показать очередь."""
        p = self._player()
        if not p:
            await interaction.response.send_message(
                embed=embed_error("Бот не в канале."), ephemeral=True
            )
            return
        if not p.queue and not p.playing:
            await interaction.response.send_message(
                embed=embed_simple("Очередь пуста.", COLOR_WARN, "📭"), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embed_queue(p, page=0),
            view=QueueView(self.cog, self.guild_id, page=0),
            ephemeral=True,
        )

    @discord.ui.button(emoji="➕", label="Добавить", style=discord.ButtonStyle.secondary, row=1)
    async def btn_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Открыть окно добавления трека."""
        if not await self._check(interaction):
            return
        await interaction.response.send_modal(AddTrackModal(self.cog))


# ──────────────────────────────────────────────────────────
#  ОТПРАВКА КАРТОЧКИ NOW PLAYING
# ──────────────────────────────────────────────────────────
async def send_now_playing(
    channel: discord.TextChannel,
    track: wavelink.Playable,
    player: wavelink.Player,
    requester: discord.Member | None = None,
    cog: "Music | None" = None,
) -> discord.Message | None:
    embed = embed_now_playing(track, player, requester)
    view  = PlayerView(cog, player.guild.id) if cog else None
    thumb = get_thumbnail(track)

    try:
        if thumb:
            msg = await channel.send(embed=embed, view=view)
        else:
            try:
                file = discord.File(
                    "config/assets/default_thumbnail.png",
                    filename="default_thumbnail.png",
                )
                msg = await channel.send(embed=embed, file=file, view=view)
            except FileNotFoundError:
                msg = await channel.send(embed=embed, view=view)
        return msg
    except Exception as e:
        log.warning(f"send_now_playing error: {e}")
        return None


# ──────────────────────────────────────────────────────────
#  COG
# ──────────────────────────────────────────────────────────
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spotify_api: SpotifyAPI | None = None
        self.playlist_store = PlaylistStore(
            self.bot.config.get("PLAYLIST_STORE_PATH", "config/playlists.json")
        )
        self.last_channels:        dict[int, discord.TextChannel] = {}
        self.last_requesters:      dict[int, discord.Member]      = {}
        self.now_playing_messages: dict[int, discord.Message]     = {}

    async def cog_load(self):
        sp_id     = self.bot.config.get("SPOTIFY_CLIENT_ID")
        sp_secret = self.bot.config.get("SPOTIFY_CLIENT_SECRET")
        if sp_id and sp_secret:
            self.spotify_api = SpotifyAPI(self.bot, sp_id, sp_secret)
            try:
                await self.spotify_api.initialize()
                log.info("Spotify готов")
            except Exception as e:
                log.error(f"Spotify ошибка: {e}")
                self.spotify_api = None
        await self._init_wavelink()

    async def _init_wavelink(self):
        host     = self.bot.config.get("LAVALINK_HOST", "localhost")
        port     = self.bot.config.get("LAVALINK_PORT", 2333)
        password = self.bot.config.get("LAVALINK_PASSWORD")
        node     = wavelink.Node(uri=f"http://{host}:{port}", password=password)
        await wavelink.Pool.connect(client=self.bot, nodes=[node])
        log.info("Wavelink подключён")

    # ── ХЕЛПЕРЫ ──────────────────────────────────────────
    @staticmethod
    async def _get_player(interaction: discord.Interaction) -> wavelink.Player:
        vc = interaction.user.voice
        if not vc or not vc.channel:
            raise commands.CommandError("Вы не в голосовом канале.")
        guild = interaction.guild
        if guild.voice_client:
            player: wavelink.Player = guild.voice_client
            if player.channel != vc.channel:
                await player.move_to(vc.channel)
            return player
        return await vc.channel.connect(cls=wavelink.Player, self_deaf=True)

    async def _get_track(self, query: str) -> wavelink.Playable:
        playables = await self._load_playables(query)
        if not playables:
            raise commands.CommandError("Ничего не найдено.")
        return playables[0]

    async def _load_playables(self, query: str) -> list[wavelink.Playable]:
        try:
            if self.spotify_api and await self.spotify_api.is_spotify_url(query):
                tracks_data, typ = await self.spotify_api.process_url(query)
                if not tracks_data:
                    raise commands.CommandError("Не удалось загрузить из Spotify.")
                playables: list[wavelink.Playable] = []
                for td in tracks_data:
                    try:
                        track = await self._get_track(td["search_query"])
                        playables.append(track)
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        log.warning(f"Пропущен трек {td.get('title', '?')}: {e}")
                return playables

            if URL_REGEX.match(query):
                results = await wavelink.Playable.search(query)
                if hasattr(results, "tracks") and results.tracks:
                    return list(results.tracks)
                if isinstance(results, list):
                    if len(results) > 1:
                        return results
                    return results
                return [results]

            results = await wavelink.Playable.search(f"ytmsearch:{query}")
            if not results:
                results = await wavelink.Playable.search(f"ytsearch:{query}")
            if not results:
                results = await wavelink.Playable.search(f"scsearch:{query}")
        except wavelink.LavalinkLoadException as e:
            log.error(f"Lavalink load error: {e}")
            raise commands.CommandError(
                "Не удалось загрузить трек. Источник недоступен — попробуйте другую ссылку."
            )
        except Exception as e:
            log.error(f"Track search error: {e}")
            raise commands.CommandError("Ошибка поиска. Попробуйте ещё раз.")

        if not results:
            raise commands.CommandError("Ничего не найдено.")
        if isinstance(results, list):
            return [results[0]]
        return [results]

    async def _build_track_label(self, query: str) -> str:
        if self.spotify_api and await self.spotify_api.is_spotify_url(query):
            tracks_data, typ = await self.spotify_api.process_url(query)
            if tracks_data and isinstance(tracks_data, list):
                return tracks_data[0].get("title", query) if typ == "track" else query
        try:
            track = await self._get_track(query)
            return track.title or query
        except Exception:
            return query

    async def _start_playback_if_idle(self, player: wavelink.Player) -> None:
        if player.playing:
            return

        if not player.queue:
            return

        next_track = player.queue.get()
        if next_track is None:
            return

        try:
            await asyncio.wait_for(player.play(next_track), timeout=10)
        except asyncio.TimeoutError:
            log.warning("Старт следующего трека превысил таймаут.")
            raise

    async def _has_pending_track(self, player: wavelink.Player) -> bool:
        return bool(player.queue) or getattr(player, "current", None) is not None

    async def _advance_player(self, player: wavelink.Player) -> bool:
        if not player:
            return False

        if not await self._has_pending_track(player):
            await player.stop()
            return False

        try:
            await asyncio.wait_for(player.stop(), timeout=5)
        except Exception:
            pass

        next_track = player.queue.get()
        if next_track is None:
            return False

        try:
            await asyncio.wait_for(player.play(next_track), timeout=10)
        except asyncio.TimeoutError:
            log.warning("Переход к следующему треку превысил таймаут.")
            raise

        return True

    async def _enqueue_query_list(self, player: wavelink.Player, queries: list[str]) -> tuple[int, list[str]]:
        added = 0
        failed: list[str] = []

        for query in queries:
            try:
                tracks = await self._load_playables(query)
            except Exception as e:
                failed.append(query)
                log.warning(f"Пропущен запрос '{query}': {e}")
                continue

            for track in tracks:
                await player.queue.put_wait(track)
                added += 1
                await asyncio.sleep(0.1)

        return added, failed

    async def _send_added(
        self,
        interaction: discord.Interaction,
        track: wavelink.Playable,
        pos: int,
    ):
        embed = embed_added_track(track, pos, interaction.user)
        thumb = get_thumbnail(track)
        if thumb:
            await interaction.followup.send(embed=embed)
        else:
            try:
                file = discord.File(
                    "config/assets/default_thumbnail.png",
                    filename="default_thumbnail.png",
                )
                await interaction.followup.send(embed=embed, file=file)
            except FileNotFoundError:
                await interaction.followup.send(embed=embed)

    # ── СОБЫТИЯ ──────────────────────────────────────────
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Карточка Now Playing при каждой смене трека."""
        player    = payload.player
        track     = payload.track
        channel   = self.last_channels.get(player.guild.id)
        requester = self.last_requesters.get(player.guild.id)

        # Убираем кнопки с предыдущего сообщения
        old_msg = self.now_playing_messages.pop(player.guild.id, None)
        if old_msg:
            try:
                await old_msg.edit(view=None)
            except Exception:
                pass

        if channel and track:
            try:
                msg = await send_now_playing(channel, track, player, requester, cog=self)
                if msg:
                    self.now_playing_messages[player.guild.id] = msg
            except Exception as e:
                log.warning(f"Не удалось отправить Now Playing: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Wavelink 3.x сам управляет очередью.
           Здесь только отключение при пустой очереди и безопасный переход к следующему треку."""
        player = payload.player
        if not player:
            return

        if not player.playing and await self._has_pending_track(player):
            try:
                await self._start_playback_if_idle(player)
            except Exception as e:
                log.warning(f"Не удалось автоматически продолжить после окончания трека: {e}")
                return

        if not player.queue and not player.playing:
            await asyncio.sleep(60)
            if not player.queue and not player.playing:
                await player.disconnect()
                self.last_channels.pop(player.guild.id, None)
                self.last_requesters.pop(player.guild.id, None)
                self.now_playing_messages.pop(player.guild.id, None)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Уведомление об ошибке трека и безопасный переход к следующему."""
        player  = payload.player
        channel = self.last_channels.get(player.guild.id)
        log.error(f"Track exception: {payload.exception}")
        if channel:
            try:
                await channel.send(embed=embed_error("Ошибка воспроизведения трека, пропускаю..."))
            except Exception:
                pass

        try:
            await self._advance_player(player)
        except Exception as e:
            log.error(f"Не удалось перейти к следующему треку после ошибки: {e}", exc_info=True)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        """Плеер неактивен — отключаемся."""
        await player.disconnect()
        self.last_channels.pop(player.guild.id, None)
        self.last_requesters.pop(player.guild.id, None)
        self.now_playing_messages.pop(player.guild.id, None)

    # ── КОМАНДЫ ──────────────────────────────────────────
    @app_commands.command(name="play", description="Воспроизвести музыку (YouTube, SoundCloud, Spotify)")
    @app_commands.describe(query="Название трека, ссылка или Spotify URL")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            self.last_channels[interaction.guild.id]   = interaction.channel
            self.last_requesters[interaction.guild.id] = interaction.user

            tracks = await self._load_playables(query)
            if not tracks:
                await interaction.followup.send(embed=embed_error("Ничего не найдено."))
                return
            if len(tracks) == 1:
                track = tracks[0]
                pos   = len(player.queue) + 1
                await player.queue.put_wait(track)
                await self._send_added(interaction, track, pos)
            else:
                added = 0
                for track in tracks:
                    try:
                        await player.queue.put_wait(track)
                        added += 1
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        log.warning(f"Пропущен трек {track.title if hasattr(track, 'title') else '?'}: {e}")
                await interaction.followup.send(embed=embed_added_playlist(added, "плейлист"))

            await self._start_playback_if_idle(player)

        except commands.CommandError as e:
            await interaction.followup.send(embed=embed_error(str(e)))
        except Exception as e:
            log.error(f"Play error: {e}", exc_info=True)
            await interaction.followup.send(embed=embed_error("Непредвиденная ошибка при воспроизведении."))

    # Application command group for playlist operations
    playlist = app_commands.Group(name="playlist", description="Пользовательские плейлисты")

    @playlist.command(name="create", description="Создать пользовательский плейлист")
    @app_commands.describe(name="Название плейлиста", description="Описание плейлиста")
    async def playlist_create(
        self,
        interaction: discord.Interaction,
        name: str,
        description: str = "",
    ):
        await interaction.response.defer(ephemeral=True)
        if not self.playlist_store.create_playlist(interaction.guild.id, name, interaction.user.id, description):
            await interaction.followup.send(embed=embed_error("Плейлист с таким именем уже существует."))
            return
        await interaction.followup.send(embed=embed_simple(f"Плейлист **{name}** создан.", COLOR_SUCCESS, "✅"))

    @playlist.command(name="delete", description="Удалить пользовательский плейлист")
    @app_commands.describe(name="Название плейлиста")
    async def playlist_delete(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        if not self.playlist_store.delete_playlist(interaction.guild.id, name):
            await interaction.followup.send(embed=embed_error("Плейлист не найден."))
            return
        await interaction.followup.send(embed=embed_simple(f"Плейлист **{name}** удалён.", COLOR_SUCCESS, "🗑️"))

    @playlist.command(name="rename", description="Переименовать плейлист")
    @app_commands.describe(old_name="Текущее название", new_name="Новое название")
    async def playlist_rename(self, interaction: discord.Interaction, old_name: str, new_name: str):
        await interaction.response.defer(ephemeral=True)
        if not self.playlist_store.rename_playlist(interaction.guild.id, old_name, new_name):
            await interaction.followup.send(embed=embed_error("Не удалось переименовать плейлист. Возможно, новое имя уже занято или старый плейлист не найден."))
            return
        await interaction.followup.send(embed=embed_simple(f"Плейлист **{old_name}** переименован в **{new_name}**.", COLOR_SUCCESS, "✏️"))

    @playlist.command(name="add", description="Добавить трек или ссылку в плейлист")
    @app_commands.describe(name="Название плейлиста", query="Название, ссылка или Spotify URL")
    async def playlist_add(self, interaction: discord.Interaction, name: str, query: str):
        await interaction.response.defer(ephemeral=True)
        playlist = self.playlist_store.get_playlist(interaction.guild.id, name)
        if not playlist:
            await interaction.followup.send(embed=embed_error("Плейлист не найден."))
            return
        label = await self._build_track_label(query)
        self.playlist_store.add_track(interaction.guild.id, name, query, label)
        await interaction.followup.send(embed=embed_simple(f"Трек добавлен в **{playlist['name']}**.", COLOR_SUCCESS, "➕"))

    @playlist.command(name="remove", description="Удалить трек из плейлиста по номеру")
    @app_commands.describe(name="Название плейлиста", index="Номер трека в плейлисте")
    async def playlist_remove(self, interaction: discord.Interaction, name: str, index: int):
        await interaction.response.defer(ephemeral=True)
        playlist = self.playlist_store.get_playlist(interaction.guild.id, name)
        if not playlist:
            await interaction.followup.send(embed=embed_error("Плейлист не найден."))
            return
        if not self.playlist_store.remove_track(interaction.guild.id, name, index - 1):
            await interaction.followup.send(embed=embed_error("Неправильный номер трека."))
            return
        await interaction.followup.send(embed=embed_simple(f"Трек #{index} удалён из **{playlist['name']}**.", COLOR_SUCCESS, "🗑️"))

    @playlist.command(name="list", description="Показать свои плейлисты на сервере")
    async def playlist_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        playlists = self.playlist_store.list_playlists(interaction.guild.id)
        if not playlists:
            await interaction.followup.send(embed=embed_simple("Плейлистов нет.", COLOR_WARN, "📭"))
            return
        view = PlaylistBrowseView(self, interaction.guild.id, playlists)
        message = await interaction.followup.send(
            embed=view.build_embed(),
            view=view,
            ephemeral=True,
        )
        view.message = message

    @playlist.command(name="show", description="Показать треки в плейлисте")
    @app_commands.describe(name="Название плейлиста")
    async def playlist_show(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        playlist = self.playlist_store.get_playlist(interaction.guild.id, name)
        if not playlist:
            await interaction.followup.send(embed=embed_error("Плейлист не найден."))
            return
        if not playlist["tracks"]:
            await interaction.followup.send(embed=embed_simple("Плейлист пуст.", COLOR_WARN, "📭"))
            return
        await interaction.followup.send(embed=embed_playlist_details(playlist))

    @playlist.command(name="play", description="Воспроизвести сохранённый плейлист")
    @app_commands.describe(name="Название плейлиста")
    async def playlist_play(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        playlist = self.playlist_store.get_playlist(interaction.guild.id, name)
        if not playlist:
            await interaction.followup.send(embed=embed_error("Плейлист не найден."))
            return
        if not playlist["tracks"]:
            await interaction.followup.send(embed=embed_simple("Плейлист пуст.", COLOR_WARN, "📭"))
            return
        try:
            player = await self._get_player(interaction)
            self.last_channels[interaction.guild.id]   = interaction.channel
            self.last_requesters[interaction.guild.id] = interaction.user
            added, failed = await self._enqueue_query_list(player, [item["query"] for item in playlist["tracks"]])
            if failed:
                log.warning(f"Плейлист '{playlist['name']}' пропустил {len(failed)} запросов")
            await interaction.followup.send(embed=embed_added_playlist(added, playlist['name']))
            await self._start_playback_if_idle(player)
        except commands.CommandError as e:
            await interaction.followup.send(embed=embed_error(str(e)))
        except Exception as e:
            log.error(f"Playlist play error: {e}", exc_info=True)
            await interaction.followup.send(embed=embed_error("Не удалось воспроизвести плейлист."))

    @app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            skipped = player.current
            if not await self._has_pending_track(player):
                await interaction.followup.send(embed=embed_simple("Ничего не играет.", COLOR_WARN, "⚠️"))
                return
            try:
                await asyncio.wait_for(self._advance_player(player), timeout=5)
            except Exception as e:
                log.warning(f"Slash skip fallback failed: {e}")
                await interaction.followup.send(embed=embed_error("Не удалось переключить трек. Попробуйте ещё раз."))
                return
            title = skipped.title if skipped else "текущий трек"
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"⏭️  Пропущено: **{title}**",
                    color=COLOR_MUTED,
                )
            )
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="stop", description="Остановить и очистить очередь")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            player.queue.clear()
            await player.stop()
            await player.disconnect()
            self.last_channels.pop(interaction.guild.id, None)
            self.last_requesters.pop(interaction.guild.id, None)
            self.now_playing_messages.pop(interaction.guild.id, None)
            await interaction.followup.send(
                embed=embed_simple("Воспроизведение остановлено, бот покинул канал.", COLOR_ERROR, "🛑")
            )
        except Exception:
            await interaction.followup.send(embed=embed_error("Бот не в голосовом канале."))

    @app_commands.command(name="pause", description="Поставить на паузу")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            if player.paused:
                await interaction.followup.send(embed=embed_simple("Уже на паузе.", COLOR_WARN, "⚠️"))
                return
            await player.pause(True)
            await interaction.followup.send(embed=embed_simple("Воспроизведение приостановлено.", COLOR_MUTED, "⏸️"))
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="resume", description="Продолжить воспроизведение")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            if not player.paused:
                await interaction.followup.send(embed=embed_simple("Трек не на паузе.", COLOR_WARN, "⚠️"))
                return
            await player.pause(False)
            await interaction.followup.send(embed=embed_simple("Воспроизведение возобновлено.", COLOR_SUCCESS, "▶️"))
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="queue", description="Показать текущую очередь")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            if not player.queue and not player.playing:
                await interaction.followup.send(embed=embed_simple("Очередь пуста.", COLOR_WARN, "📭"))
                return
            await interaction.followup.send(
                embed=embed_queue(player, page=0),
                view=QueueView(self, interaction.guild.id, page=0),
            )
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="clear", description="Очистить очередь")
    async def clear(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            count  = len(player.queue)
            player.queue.clear()
            await interaction.followup.send(
                embed=embed_simple(f"Из очереди удалено {count} трек(ов).", COLOR_MUTED, "🗑️")
            )
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="shuffle", description="Перемешать очередь")
    async def shuffle(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            if len(player.queue) < 2:
                await interaction.followup.send(embed=embed_simple("Нужно минимум 2 трека в очереди.", COLOR_WARN, "⚠️"))
                return
            player.queue.shuffle()
            await interaction.followup.send(
                embed=embed_simple(f"Очередь из {len(player.queue)} треков перемешана.", COLOR_SUCCESS, "🔀")
            )
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="loop", description="Установить режим повтора")
    @app_commands.describe(mode="off · track · queue")
    async def loop(self, interaction: discord.Interaction, mode: str):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            mode   = mode.lower()
            if mode == "off":
                player.queue.mode = wavelink.QueueMode.normal
                await interaction.followup.send(embed=embed_simple("Повтор выключен.", COLOR_MUTED, "➡️"))
            elif mode == "track":
                player.queue.mode = wavelink.QueueMode.loop
                await interaction.followup.send(embed=embed_simple("Повтор текущего трека включён.", COLOR_SUCCESS, "🔂"))
            elif mode == "queue":
                player.queue.mode = wavelink.QueueMode.loop_all
                await interaction.followup.send(embed=embed_simple("Повтор всей очереди включён.", COLOR_SUCCESS, "🔁"))
            else:
                await interaction.followup.send(embed=embed_error("Неверный режим. Доступные: `off`, `track`, `queue`"))
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="now", description="Показать текущий трек")
    async def now(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            if not player.playing or not player.current:
                await interaction.followup.send(embed=embed_simple("Ничего не играет.", COLOR_WARN, "🔇"))
                return
            track     = player.current
            requester = self.last_requesters.get(interaction.guild.id)
            embed     = embed_now_playing(track, player, requester)
            view      = PlayerView(self, interaction.guild.id)
            thumb     = get_thumbnail(track)
            if thumb:
                await interaction.followup.send(embed=embed, view=view)
            else:
                try:
                    file = discord.File(
                        "config/assets/default_thumbnail.png",
                        filename="default_thumbnail.png",
                    )
                    await interaction.followup.send(embed=embed, file=file, view=view)
                except FileNotFoundError:
                    await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="volume", description="Изменить громкость (0–100)")
    @app_commands.describe(level="Уровень громкости от 0 до 100")
    async def volume(self, interaction: discord.Interaction, level: int):
        await interaction.response.defer()
        try:
            if not 0 <= level <= 100:
                await interaction.followup.send(embed=embed_error("Громкость должна быть от 0 до 100."))
                return
            player = await self._get_player(interaction)
            await player.set_volume(level)
            bars  = round(level / 10)
            scale = "█" * bars + "░" * (10 - bars)
            await interaction.followup.send(
                embed=embed_simple(f"[{scale}] **{level}%**", COLOR_MAIN, "🔊")
            )
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="join", description="Присоединиться к вашему голосовому каналу")
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            await interaction.followup.send(
                embed=embed_simple(f"Подключился к **{player.channel.name}**.", COLOR_SUCCESS, "🎙️")
            )
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="leave", description="Покинуть голосовой канал")
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            if not interaction.guild.voice_client:
                await interaction.followup.send(embed=embed_error("Бот не в голосовом канале."))
                return
            await interaction.guild.voice_client.disconnect()
            self.last_channels.pop(interaction.guild.id, None)
            self.last_requesters.pop(interaction.guild.id, None)
            self.now_playing_messages.pop(interaction.guild.id, None)
            await interaction.followup.send(embed=embed_simple("Покинул голосовой канал.", COLOR_MUTED, "👋"))
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

    @app_commands.command(name="sync", description="Синхронизировать слеш-команды (только владелец)")
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id != self.bot.owner_id:
            await interaction.response.send_message(
                embed=embed_error("Только владелец может использовать эту команду."), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        try:
            await self.bot.tree.sync()
            await interaction.followup.send(
                embed=embed_simple("Слеш-команды успешно синхронизированы.", COLOR_SUCCESS, "✅"),
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(embed=embed_error(f"Ошибка синхронизации: {e}"), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))