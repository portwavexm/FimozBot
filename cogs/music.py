import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import re
import logging
import asyncio

from utils.spotify import SpotifyAPI

log = logging.getLogger(__name__)
URL_REGEX = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)')

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spotify_api: SpotifyAPI = None
        self.last_channels = {}  # guild_id -> текстовый канал для уведомлений

    async def cog_load(self):
        # Инициализация Spotify
        sp_id = self.bot.config.get("SPOTIFY_CLIENT_ID")
        sp_secret = self.bot.config.get("SPOTIFY_CLIENT_SECRET")
        if sp_id and sp_secret:
            self.spotify_api = SpotifyAPI(self.bot, sp_id, sp_secret)
            try:
                await self.spotify_api.initialize()
                log.info("Spotify готов")
            except Exception as e:
                log.error(f"Spotify ошибка: {e}")
                self.spotify_api = None
        # Инициализация Lavalink
        await self._init_wavelink()

    async def _init_wavelink(self):
        host = self.bot.config.get("LAVALINK_HOST", "localhost")
        port = self.bot.config.get("LAVALINK_PORT", 2333)
        password = self.bot.config.get("LAVALINK_PASSWORD")
        node = wavelink.Node(uri=f"http://{host}:{port}", password=password)
        await wavelink.Pool.connect(client=self.bot, nodes=[node])
        log.info("Wavelink подключён")

    @staticmethod
    async def _get_player(interaction: discord.Interaction):
        vc = interaction.user.voice
        if not vc or not vc.channel:
            raise commands.CommandError("Вы не в голосовом канале.")
        guild = interaction.guild
        if guild.voice_client:
            player = guild.voice_client
            if player.channel != vc.channel:
                await player.move_to(vc.channel)
            return player
        return await vc.channel.connect(cls=wavelink.Player, self_deaf=True)

    async def _get_track(self, query: str):
        if URL_REGEX.match(query):
            tracks = await wavelink.Playable.search(query)
        else:
            tracks = await wavelink.Playable.search(f"ytsearch:{query}")
        if not tracks:
            raise commands.CommandError("Ничего не найдено.")
        return tracks[0] if isinstance(tracks, list) else tracks

    async def _play_next(self, player: wavelink.Player):
        """Воспроизвести следующий трек из очереди (с учётом повтора)"""
        if not player.queue:
            await asyncio.sleep(60)
            if not player.queue and not player.playing:
                await player.disconnect()
                self.last_channels.pop(player.guild.id, None)
            return

        # Если включён повтор трека, добавляем текущий трек обратно в начало очереди
        if hasattr(player.queue, 'loop_mode') and player.queue.loop_mode == wavelink.QueueLoopMode.track:
            if player.current:
                await player.queue.put_front(player.current)

        next_track = await player.queue.get_wait()
        await player.play(next_track)

        channel = self.last_channels.get(player.guild.id)
        if channel:
            dur = (next_track.length // 1000) if hasattr(next_track, 'length') else 0
            if dur:
                m, s = divmod(dur, 60)
                await channel.send(f"🎵 **Сейчас играет:** {next_track.title}\n⏱️ {m}:{s:02d}")
            else:
                await channel.send(f"🎵 **Сейчас играет:** {next_track.title}")

    # ---------- ОБРАБОТЧИК ОКОНЧАНИЯ ТРЕКА ----------
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        """Автоматический переход к следующему треку"""
        player = payload.player
        if not player:
            return
        reason = str(payload.reason) if payload.reason else ""
        # Не переключать, если трек остановлен вручную или заменён
        if "STOPPED" in reason or "REPLACED" in reason:
            return
        # Если включён повтор очереди, добавляем текущий трек обратно в конец очереди
        if hasattr(player.queue, 'loop_mode') and player.queue.loop_mode == wavelink.QueueLoopMode.queue:
            if player.current:
                await player.queue.put_wait(player.current)
        await self._play_next(player)

    # ---------- КОМАНДЫ ----------
    @app_commands.command(name="play", description="Воспроизвести музыку (YouTube, SoundCloud, Spotify)")
    @app_commands.describe(query="Название трека, ссылка или Spotify URL")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            self.last_channels[interaction.guild.id] = interaction.channel

            # Обработка Spotify
            is_spotify = self.spotify_api and await self.spotify_api.is_spotify_url(query)
            if is_spotify:
                tracks_data, typ = await self.spotify_api.process_url(query)
                if not tracks_data:
                    await interaction.followup.send("❌ Не удалось загрузить из Spotify.")
                    return
                if typ == "track":
                    track = await self._get_track(tracks_data[0]["search_query"])
                    await player.queue.put_wait(track)
                    await interaction.followup.send(f"✅ Добавлено: **{tracks_data[0]['title']}**")
                else:
                    added = 0
                    for td in tracks_data:
                        try:
                            t = await self._get_track(td["search_query"])
                            await player.queue.put_wait(t)
                            added += 1
                            await asyncio.sleep(0.2)
                        except Exception as e:
                            log.warning(f"Ошибка добавления {td['title']}: {e}")
                    await interaction.followup.send(f"✅ Добавлено {added} треков из плейлиста/альбома.")
            else:
                track = await self._get_track(query)
                await player.queue.put_wait(track)
                await interaction.followup.send(f"✅ Добавлено в очередь: **{track.title}**")

            if not player.playing:
                await self._play_next(player)

        except commands.CommandError as e:
            await interaction.followup.send(str(e))
        except Exception as e:
            log.error(f"Play error: {e}", exc_info=True)
            await interaction.followup.send("❌ Ошибка при воспроизведении.")

    @app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            if not player.playing:
                await interaction.followup.send("Ничего не играет.")
                return
            await player.stop()  # вызовет событие on_wavelink_track_end
            await interaction.followup.send("⏭️ Пропущено.")
        except Exception as e:
            await interaction.followup.send(f"❌ {e}")

    @app_commands.command(name="stop", description="Остановить и очистить очередь")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            player = await self._get_player(interaction)
            player.queue.clear()
            if player.playing:
                await player.stop()
            await player.disconnect()
            self.last_channels.pop(interaction.guild.id, None)
            await interaction.followup.send("🛑 Остановлено и отключено.")
        except:
            await interaction.followup.send("Не в канале.")

    @app_commands.command(name="pause", description="Поставить на паузу")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await self._get_player(interaction)
        if player.paused:
            await interaction.followup.send("Уже на паузе.")
            return
        await player.pause(True)
        await interaction.followup.send("⏸️ Пауза.")

    @app_commands.command(name="resume", description="Продолжить воспроизведение")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await self._get_player(interaction)
        if not player.paused:
            await interaction.followup.send("Не на паузе.")
            return
        await player.pause(False)
        await interaction.followup.send("▶️ Продолжено.")

    @app_commands.command(name="queue", description="Показать текущую очередь")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await self._get_player(interaction)
        if not player.queue:
            await interaction.followup.send("Очередь пуста.")
            return
        lines = []
        for i, t in enumerate(player.queue, 1):
            lines.append(f"{i}. **{t.title}**")
            if i >= 10:
                break
        embed = discord.Embed(title="🎶 Очередь", description="\n".join(lines), color=discord.Color.blue())
        if player.playing:
            embed.add_field(name="Сейчас играет", value=player.current.title, inline=False)
        if len(player.queue) > 10:
            embed.set_footer(text=f"и ещё {len(player.queue)-10} треков")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="clear", description="Очистить очередь")
    async def clear(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await self._get_player(interaction)
        count = len(player.queue)
        player.queue.clear()
        await interaction.followup.send(f"🗑️ Очищено {count} треков.")

    @app_commands.command(name="shuffle", description="Перемешать очередь")
    async def shuffle(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await self._get_player(interaction)
        if len(player.queue) < 2:
            await interaction.followup.send("Нужно минимум 2 трека.")
            return
        player.queue.shuffle()
        await interaction.followup.send("🔀 Очередь перемешана.")

    @app_commands.command(name="loop", description="Установить повтор")
    @app_commands.describe(mode="off / track / queue")
    async def loop(self, interaction: discord.Interaction, mode: str):
        await interaction.response.defer()
        player = await self._get_player(interaction)
        mode = mode.lower()
        if mode == "off":
            if hasattr(player.queue, 'loop_mode'):
                player.queue.loop_mode = None
            await interaction.followup.send("⏹️ Повтор выключен.")
        elif mode == "track":
            if hasattr(player.queue, 'loop_mode'):
                player.queue.loop_mode = wavelink.QueueLoopMode.track
            await interaction.followup.send("🔂 Повтор трека включён.")
        elif mode == "queue":
            if hasattr(player.queue, 'loop_mode'):
                player.queue.loop_mode = wavelink.QueueLoopMode.queue
            await interaction.followup.send("🔁 Повтор очереди включён.")
        else:
            await interaction.followup.send("Неверный режим. Используйте: off, track, queue")

    @app_commands.command(name="now", description="Показать текущий трек")
    async def now(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await self._get_player(interaction)
        if not player.playing:
            await interaction.followup.send("Ничего не играет.")
            return
        track = player.current
        dur = (track.length // 1000) if hasattr(track, 'length') else 0
        embed = discord.Embed(title="🎵 Сейчас играет", description=track.title, color=discord.Color.purple())
        if track.uri:
            embed.add_field(name="Ссылка", value=f"[Открыть]({track.uri})", inline=False)
        if dur:
            m, s = divmod(dur, 60)
            embed.add_field(name="Длительность", value=f"{m}:{s:02d}", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="volume", description="Изменить громкость (0-100)")
    async def volume(self, interaction: discord.Interaction, level: int):
        await interaction.response.defer()
        if not 0 <= level <= 100:
            await interaction.followup.send("Громкость должна быть от 0 до 100.")
            return
        player = await self._get_player(interaction)
        await player.set_volume(level)
        await interaction.followup.send(f"🔊 Громкость: {level}%")

    @app_commands.command(name="join", description="Присоединиться к вашему голосовому каналу")
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._get_player(interaction)
        await interaction.followup.send("✅ Присоединился.")

    @app_commands.command(name="leave", description="Покинуть голосовой канал")
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not interaction.guild.voice_client:
            await interaction.followup.send("Не в канале.")
            return
        await interaction.guild.voice_client.disconnect()
        self.last_channels.pop(interaction.guild.id, None)
        await interaction.followup.send("👋 Покинул канал.")

    @app_commands.command(name="sync", description="Синхронизировать слеш-команды (только владелец)")
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id != self.bot.owner_id:
            await interaction.response.send_message("❌ Только владелец может использовать эту команду.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            await self.bot.tree.sync()
            await interaction.followup.send("✅ Команды синхронизированы.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))