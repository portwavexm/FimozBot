import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
import asyncio
from typing import Dict, List, Optional, Tuple

from discord.ext import commands

log = logging.getLogger(__name__)

class SpotifyAPI:
    """A service class to handle all Spotify interactions."""
    def __init__(self, bot: commands.Bot, client_id: str, client_secret: str):
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.sp = None
        
        # Regex patterns for matching Spotify URLs
        self.track_pattern = re.compile(r"https?://open\.spotify\.com/track/([a-zA-Z0-9]+)")
        self.playlist_pattern = re.compile(r"https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)")
        self.album_pattern = re.compile(r"https?://open\.spotify\.com/album/([a-zA-Z0-9]+)")
        self.artist_pattern = re.compile(r"https?://open\.spotify\.com/artist/([a-zA-Z0-9]+)")

    async def initialize(self):
        """Initialize the Spotipy client with credentials."""
        await asyncio.to_thread(self._sync_initialize)
        log.info("SpotifyAPI client initialized successfully.")

    def _sync_initialize(self):
        """Synchronous method to set up the Spotify client."""
        if not self.client_id or not self.client_secret:
            log.error("Spotify client ID or secret is missing!")
            raise ValueError("Spotify credentials are not set.")
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    async def fetch_track(self, url: str) -> Optional[Dict]:
        """Fetch a single track's metadata."""
        match = self.track_pattern.match(url)
        if not match:
            return None
        track_id = match.group(1)
        try:
            track = await asyncio.to_thread(self.sp.track, track_id)
            artists = ", ".join([artist["name"] for artist in track["artists"]])
            track_name = track["name"]
            search_query = f"{track_name} {artists}"
            return {
                "title": f"{artists} - {track_name}",
                "search_query": search_query,
                "duration": track["duration_ms"] // 1000,
                "uri": url
            }
        except Exception as e:
            log.error(f"Failed to fetch Spotify track: {e}")
            return None

    async def fetch_playlist(self, url: str) -> List[Dict]:
        """Fetch all tracks from a Spotify playlist."""
        match = self.playlist_pattern.match(url)
        if not match:
            return []
        playlist_id = match.group(1)
        tracks_list = []
        
        try:
            # First, get playlist metadata
            playlist_info = await asyncio.to_thread(self.sp.playlist, playlist_id)
            playlist_name = playlist_info["name"]
            
            results = await asyncio.to_thread(self.sp.playlist_items, playlist_id, limit=100, offset=0)
            tracks = results["items"]
            
            while results["next"]:
                results = await asyncio.to_thread(self.sp.next, results)
                tracks.extend(results["items"])
            
            for item in tracks:
                track = item["track"]
                if track:
                    artists = ", ".join([artist["name"] for artist in track["artists"]])
                    track_name = track["name"]
                    search_query = f"{track_name} {artists}"
                    tracks_list.append({
                        "title": f"{artists} - {track_name}",
                        "search_query": search_query,
                        "duration": track["duration_ms"] // 1000,
                        "uri": track["external_urls"]["spotify"]
                    })
            
            log.info(f"Fetched {len(tracks_list)} tracks from Spotify playlist: {playlist_name}")
            return tracks_list
        except Exception as e:
            log.error(f"Failed to fetch Spotify playlist: {e}")
            return []

    async def fetch_album(self, url: str) -> List[Dict]:
        """Fetch all tracks from a Spotify album."""
        match = self.album_pattern.match(url)
        if not match:
            return []
        album_id = match.group(1)
        tracks_list = []
        
        try:
            album_info = await asyncio.to_thread(self.sp.album, album_id)
            album_name = album_info["name"]
            
            results = await asyncio.to_thread(self.sp.album_tracks, album_id, limit=50)
            tracks = results["items"]
            
            while results["next"]:
                results = await asyncio.to_thread(self.sp.next, results)
                tracks.extend(results["items"])
            
            # We need artist info for each track, so we fetch them individually
            for track in tracks:
                artists = ", ".join([artist["name"] for artist in track["artists"]])
                track_name = track["name"]
                search_query = f"{track_name} {artists}"
                tracks_list.append({
                    "title": f"{artists} - {track_name}",
                    "search_query": search_query,
                    "duration": track["duration_ms"] // 1000,
                    "uri": track["external_urls"]["spotify"]
                })
            
            log.info(f"Fetched {len(tracks_list)} tracks from Spotify album: {album_name}")
            return tracks_list
        except Exception as e:
            log.error(f"Failed to fetch Spotify album: {e}")
            return []

    async def is_spotify_url(self, url: str) -> bool:
        """Check if a URL is a Spotify URL."""
        return bool(self.track_pattern.match(url) or 
                   self.playlist_pattern.match(url) or 
                   self.album_pattern.match(url) or 
                   self.artist_pattern.match(url))

    async def process_url(self, url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Main method to process a Spotify URL and return tracks and type."""
        if self.track_pattern.match(url):
            track = await self.fetch_track(url)
            return ([track], "track") if track else (None, None)
        elif self.playlist_pattern.match(url):
            tracks = await self.fetch_playlist(url)
            return (tracks, "playlist") if tracks else (None, None)
        elif self.album_pattern.match(url):
            tracks = await self.fetch_album(url)
            return (tracks, "album") if tracks else (None, None)
        elif self.artist_pattern.match(url):
            # For now, we'll ignore artist URLs as they don't have a single track list
            return (None, None)
        return (None, None)