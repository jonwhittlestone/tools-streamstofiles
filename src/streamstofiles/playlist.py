"""M3U playlist generation."""

from pathlib import Path
from typing import Any


class PlaylistGenerator:
    """Generates m3u playlist files."""

    @staticmethod
    def generate_m3u(
        output_path: Path,
        files: list[dict[str, Any]],
    ) -> Path:
        """
        Generate an m3u playlist file.

        Args:
            output_path: Path where the m3u file should be saved
            files: List of file dictionaries containing:
                - path: Path to the MP3 file
                - title: Track title
                - artist: Artist name
                - duration: Duration in seconds

        Returns:
            Path to the created m3u file
        """
        playlist_lines = ["#EXTM3U\n"]

        for file_info in files:
            path = Path(file_info["path"])
            title = file_info.get("title", "Unknown")
            artist = file_info.get("artist", "Unknown")
            duration = file_info.get("duration", -1)

            # Add EXTINF line with duration and display info
            display_name = f"{artist} - {title}"
            playlist_lines.append(f"#EXTINF:{duration},{display_name}\n")

            # Add file path (relative to playlist location)
            # Use just the filename since playlist is in the same directory
            playlist_lines.append(f"{path.name}\n")

        # Write the playlist file
        output_path.write_text("".join(playlist_lines), encoding="utf-8")

        return output_path

    @staticmethod
    def verify_playlist(playlist_path: Path) -> dict[str, Any]:
        """
        Verify a playlist file and return information about it.

        Args:
            playlist_path: Path to the m3u playlist file

        Returns:
            Dictionary with playlist information
        """
        if not playlist_path.exists():
            return {"error": "Playlist file not found"}

        try:
            content = playlist_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")

            if not lines or not lines[0].startswith("#EXTM3U"):
                return {"error": "Invalid m3u format"}

            # Count tracks
            track_count = sum(1 for line in lines if line and not line.startswith("#"))

            return {
                "valid": True,
                "track_count": track_count,
                "path": str(playlist_path),
            }

        except Exception as e:
            return {"error": str(e)}
