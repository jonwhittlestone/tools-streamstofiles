"""YouTube playlist downloading using yt-dlp."""

import shutil
import time
from pathlib import Path
from typing import Any

import yt_dlp

from .utils import ensure_directory, format_track_number, sanitize_filename


def _detect_node_path() -> str | None:
    """Detect Node.js path for yt-dlp JS runtime."""
    node_path = shutil.which("node")
    if node_path:
        return node_path
    return None


def _detect_cookies_file() -> Path | None:
    """Detect cookies.txt in the project root."""
    # Try common locations for the cookies file
    possible_paths = [
        Path("cookies.txt"),  # Current directory
        Path(__file__).parent.parent.parent.parent / "cookies.txt",  # Project root
    ]
    for path in possible_paths:
        if path.exists():
            return path.resolve()
    return None


class PlaylistDownloader:
    """Downloads YouTube playlists and converts to MP3."""

    def __init__(self, output_dir: Path, quality: str = "192"):
        """
        Initialize the downloader.

        Args:
            output_dir: Base directory for output files
            quality: MP3 quality in kbps (default: 192)
        """
        self.output_dir = Path(output_dir)
        self.quality = quality

    def download_playlist(self, playlist_url: str) -> dict[str, Any]:
        """
        Download a YouTube playlist and convert to MP3 files.

        Args:
            playlist_url: URL of the YouTube playlist

        Returns:
            Dictionary containing playlist info and downloaded file paths
        """
        # Log configuration status
        cookies_path = _detect_cookies_file()
        node_path = _detect_node_path()
        if cookies_path:
            print(f"Using cookies: {cookies_path}", flush=True)
        else:
            print("No cookies.txt found (rate limiting may occur)", flush=True)
        if node_path:
            print(f"Using Node.js: {node_path}", flush=True)

        # First, get playlist info to determine track count and playlist title
        info = self._get_playlist_info(playlist_url)
        playlist_title = info.get("title", "Unknown")

        # Handle both playlists (has 'entries') and single videos (no 'entries')
        if "entries" in info:
            entries = info["entries"]
        else:
            # Single video - wrap it in a list
            entries = [info]
            playlist_title = info.get("uploader", "Single_Video")

        total_tracks = len(entries)

        # Create sanitized directory name
        sanitized_title = sanitize_filename(playlist_title)
        playlist_dir = ensure_directory(self.output_dir / sanitized_title)

        # Download each video with proper numbering
        downloaded_files = []
        for idx, entry in enumerate(entries, start=1):
            if entry is None:
                continue

            # Add delay between downloads to avoid rate limiting (skip first)
            if idx > 1:
                print("Waiting 3 seconds before next download...")
                time.sleep(3)

            # Get video URL - prefer webpage_url, fallback to constructing from id
            video_url = entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={entry['id']}"

            track_num = format_track_number(idx, total_tracks)
            file_info = self._download_video(
                video_url,
                playlist_dir,
                track_num,
                entry,
                playlist_title,
                idx,
                total_tracks,
            )
            if file_info:
                downloaded_files.append(file_info)

        return {
            "playlist_title": playlist_title,
            "playlist_dir": playlist_dir,
            "total_tracks": total_tracks,
            "files": downloaded_files,
        }

    def _get_playlist_info(self, playlist_url: str) -> dict[str, Any]:
        """Get playlist information without downloading."""
        ydl_opts = {
            "quiet": True,
            "extract_flat": False,
            "no_warnings": False,
            # Enable remote JS challenge solver from GitHub
            "remote_components": ["ejs:github"],
        }

        # Add cookies file if present
        cookies_path = _detect_cookies_file()
        if cookies_path:
            ydl_opts["cookiefile"] = str(cookies_path)

        # Add JS runtime if Node.js is available
        node_path = _detect_node_path()
        if node_path:
            ydl_opts["js_runtimes"] = {"node": {"path": node_path}}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

        return info

    def _download_video(
        self,
        video_url: str,
        output_dir: Path,
        track_num: str,
        entry: dict[str, Any],
        playlist_title: str,
        track_index: int,
        total_tracks: int,
    ) -> dict[str, Any] | None:
        """
        Download a single video and convert to MP3.

        Args:
            video_url: URL of the video
            output_dir: Directory to save the file
            track_num: Formatted track number (e.g., "01", "02")
            entry: Video entry info from playlist
            playlist_title: Title of the playlist
            track_index: Track number (1-indexed)
            total_tracks: Total number of tracks

        Returns:
            Dictionary with file info or None if download failed
        """
        video_title = entry.get("title", "Unknown")
        uploader = entry.get("uploader", entry.get("channel", "Unknown"))
        duration = entry.get("duration", 0)
        sanitized_title = sanitize_filename(video_title, max_length=80)

        # Output template with track number prefix
        output_template = str(output_dir / f"{track_num}-{sanitized_title}.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": self.quality,
                },
                {
                    "key": "FFmpegMetadata",
                },
                {
                    "key": "EmbedThumbnail",
                },
            ],
            # Enable remote JS challenge solver from GitHub
            "remote_components": ["ejs:github"],
            "writethumbnail": True,
            "outtmpl": output_template,
            "quiet": False,
            "no_warnings": False,
            "progress_hooks": [self._progress_hook],
        }

        # Add cookies file if present
        cookies_path = _detect_cookies_file()
        if cookies_path:
            ydl_opts["cookiefile"] = str(cookies_path)

        # Add JS runtime if Node.js is available (required for some YouTube videos)
        node_path = _detect_node_path()
        if node_path:
            ydl_opts["js_runtimes"] = {"node": {"path": node_path}}

        max_retries = 3
        retry_delays = [10, 20, 30]  # Increasing delays for each retry

        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)

                mp3_path = output_dir / f"{track_num}-{sanitized_title}.mp3"

                # Verify the MP3 file was actually created
                if not mp3_path.exists():
                    print(f"Warning: Audio extraction failed for '{video_title}' - MP3 file not created")
                    return None

                return {
                    "path": mp3_path,
                    "title": video_title,
                    "artist": uploader,
                    "album": playlist_title,
                    "track_number": track_index,
                    "total_tracks": total_tracks,
                    "duration": duration,
                    "url": video_url,
                }

            except Exception as e:
                error_str = str(e)
                is_rate_limit = "403" in error_str or "Forbidden" in error_str

                if is_rate_limit and attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    print(f"Rate limited on '{video_title}', retrying in {delay}s (attempt {attempt + 2}/{max_retries})...")
                    time.sleep(delay)
                else:
                    print(f"Error downloading {video_title}: {e}")
                    return None

    def _progress_hook(self, d: dict[str, Any]) -> None:
        """Hook for download progress updates."""
        if d["status"] == "downloading":
            # Extract filename from path
            filename = Path(d.get("filename", "")).name
            percent = d.get("_percent_str", "N/A")
            speed = d.get("_speed_str", "N/A")
            print(f"\rDownloading {filename}: {percent} at {speed}", end="", flush=True)
        elif d["status"] == "finished":
            print("\nProcessing audio...")
