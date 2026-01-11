"""ID3 tag management for MP3 files."""

from pathlib import Path
from typing import Any

from mutagen.id3 import APIC, COMM, TALB, TIT2, TPE1, TRCK, ID3
from mutagen.mp3 import MP3


class ID3Tagger:
    """Manages ID3 tags for MP3 files."""

    @staticmethod
    def update_tags(file_path: Path, metadata: dict[str, Any]) -> None:
        """
        Update ID3 tags for an MP3 file.

        Args:
            file_path: Path to the MP3 file
            metadata: Dictionary containing:
                - title: Track title
                - artist: Artist/uploader name
                - album: Album/playlist name
                - track_number: Track number (1-indexed)
                - total_tracks: Total number of tracks
                - url: Optional YouTube URL to store in comment field
                - thumbnail_path: Optional path to thumbnail image for album art
        """
        try:
            # Load the MP3 file
            audio = MP3(file_path, ID3=ID3)

            # Add ID3 tag if it doesn't exist
            if audio.tags is None:
                audio.add_tags()

            # Set title
            audio.tags.add(TIT2(encoding=3, text=metadata["title"]))

            # Set artist
            audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))

            # Set album
            audio.tags.add(TALB(encoding=3, text=metadata["album"]))

            # Set track number in format "track/total"
            track_str = f"{metadata['track_number']}/{metadata['total_tracks']}"
            audio.tags.add(TRCK(encoding=3, text=track_str))

            # Add YouTube URL as a comment if provided
            if "url" in metadata and metadata["url"]:
                audio.tags.add(
                    COMM(encoding=3, lang="eng", desc="YouTube URL", text=metadata["url"])
                )

            # Add album art if thumbnail path is provided
            if "thumbnail_path" in metadata and metadata["thumbnail_path"]:
                thumbnail_path = Path(metadata["thumbnail_path"])
                if thumbnail_path.exists():
                    ID3Tagger._add_album_art(audio, thumbnail_path)

            # Save the tags
            audio.save()

        except Exception as e:
            print(f"Error updating ID3 tags for {file_path}: {e}")

    @staticmethod
    def _add_album_art(audio: MP3, thumbnail_path: Path) -> None:
        """
        Add album art to the MP3 file.

        Args:
            audio: MP3 file object
            thumbnail_path: Path to the thumbnail image
        """
        # Determine MIME type based on file extension
        ext = thumbnail_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime = mime_types.get(ext, "image/jpeg")

        # Read the image data
        with open(thumbnail_path, "rb") as img_file:
            img_data = img_file.read()

        # Add as front cover
        audio.tags.add(
            APIC(
                encoding=3,  # UTF-8
                mime=mime,
                type=3,  # Cover (front)
                desc="Cover",
                data=img_data,
            )
        )

    @staticmethod
    def verify_tags(file_path: Path) -> dict[str, Any]:
        """
        Verify and return the ID3 tags from an MP3 file.

        Args:
            file_path: Path to the MP3 file

        Returns:
            Dictionary with tag information
        """
        try:
            audio = MP3(file_path, ID3=ID3)

            if audio.tags is None:
                return {"error": "No ID3 tags found"}

            # Extract comment/URL if present
            comment = ""
            if "COMM:YouTube URL:eng" in audio.tags:
                comment = str(audio.tags["COMM:YouTube URL:eng"])

            tags = {
                "title": str(audio.tags.get("TIT2", "")),
                "artist": str(audio.tags.get("TPE1", "")),
                "album": str(audio.tags.get("TALB", "")),
                "track": str(audio.tags.get("TRCK", "")),
                "url": comment,
                "has_artwork": "APIC:" in audio.tags,
            }

            return tags

        except Exception as e:
            return {"error": str(e)}
