"""Audio file concatenation for creating single long-form files."""

import random
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

_NUM_WORDS = {
    1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
    6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
    11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen",
    16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty",
    21: "Twenty-one", 22: "Twenty-two", 23: "Twenty-three", 24: "Twenty-four",
    25: "Twenty-five", 26: "Twenty-six", 27: "Twenty-seven", 28: "Twenty-eight",
    29: "Twenty-nine", 30: "Thirty", 40: "Forty", 50: "Fifty",
    60: "Sixty", 70: "Seventy", 80: "Eighty", 90: "Ninety",
}


def _num_to_words(n: int) -> str:
    if n in _NUM_WORDS:
        return _NUM_WORDS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return f"{_NUM_WORDS[tens * 10]}-{_NUM_WORDS[ones].lower()}"
    return str(n)


class AudioConcatenator:
    """Concatenates multiple audio files into a single long file."""

    @staticmethod
    def _say_available() -> bool:
        return shutil.which("say") is not None

    @staticmethod
    def _generate_track_announcement(
        track_number: int,
        title: str,
        output_path: Path,
        quality: str,
        voice: str = "Daniel",
        rate: int = 145,
    ) -> bool:
        """
        Generate a spoken track announcement using macOS say, saved as MP3.

        Returns True on success, False if say is unavailable or fails.
        """
        if not AudioConcatenator._say_available():
            return False

        text = f"Track {_num_to_words(track_number)}. {title}."

        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
            aiff_path = Path(tmp.name)

        try:
            subprocess.run(
                ["say", "-v", voice, "-r", str(rate), "-o", str(aiff_path), text],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", str(aiff_path),
                    "-c:a", "libmp3lame",
                    "-b:a", f"{quality}k",
                    "-y",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
        finally:
            aiff_path.unlink(missing_ok=True)

    @staticmethod
    def _generate_silence(duration: float, output_path: Path, quality: str) -> None:
        """Generate a silent MP3 clip of the given duration in seconds."""
        subprocess.run(
            [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-c:a", "libmp3lame",
                "-b:a", f"{quality}k",
                "-y",
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )

    @staticmethod
    def concatenate_files(
        file_list: list[dict[str, Any]],
        output_path: Path,
        quality: str = "192",
        announce_tracks: bool = True,
    ) -> dict[str, Any]:
        """
        Concatenate multiple audio files into a single MP3 file.

        Args:
            file_list: List of file info dictionaries with 'path' and 'duration'
            output_path: Path for the output concatenated file
            quality: MP3 quality in kbps

        Returns:
            Dictionary with concatenation info including timestamps
        """
        if not file_list:
            raise ValueError("No files to concatenate")

        # Generate announcement clips and build expanded file list
        temp_dir = output_path.parent / "_announcements"
        announcement_files: list[Path] = []
        expanded_list = []

        if announce_tracks and AudioConcatenator._say_available():
            temp_dir.mkdir(exist_ok=True)
            for file_info in file_list:
                track_num = file_info.get("track_number", file_info.get("_idx", 1))
                title = file_info.get("title", "")
                announcement_path = temp_dir / f"announce_{track_num:03d}.mp3"
                silence_path = temp_dir / f"silence_{track_num:03d}.mp3"

                ok = AudioConcatenator._generate_track_announcement(
                    track_num, title, announcement_path, quality
                )
                if ok:
                    AudioConcatenator._generate_silence(0.6, silence_path, quality)
                    announcement_files.extend([announcement_path, silence_path])
                    expanded_list.append({"path": announcement_path, "duration": 0, "title": "", "_skip_timestamp": True})
                    expanded_list.append({"path": silence_path, "duration": 0, "title": "", "_skip_timestamp": True})

                expanded_list.append(file_info)
        else:
            expanded_list = file_list

        # Calculate timestamps for each track in the concatenated file (skip announcement clips)
        timestamps = AudioConcatenator._calculate_timestamps(file_list)

        # Create a temporary file list for ffmpeg concat demuxer
        concat_list_path = output_path.parent / "concat_list.txt"
        AudioConcatenator._create_concat_list(expanded_list, concat_list_path)

        try:
            # Concatenate using ffmpeg concat demuxer and convert to MP3
            # This approach is efficient as it doesn't re-encode unnecessarily
            temp_output = output_path.parent / f"{output_path.stem}_temp.mp3"

            subprocess.run(
                [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_list_path),
                    "-c:a", "libmp3lame",
                    "-b:a", f"{quality}k",
                    "-y",  # Overwrite output file
                    str(temp_output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Move to final location
            temp_output.rename(output_path)

        finally:
            # Clean up temporary concat list file
            if concat_list_path.exists():
                concat_list_path.unlink()
            # Clean up announcement clips
            for f in announcement_files:
                f.unlink(missing_ok=True)
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

        return {
            "path": output_path,
            "timestamps": timestamps,
            "total_duration": timestamps[-1]["end"] if timestamps else 0,
        }

    @staticmethod
    def _calculate_timestamps(file_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Calculate start and end timestamps for each track in the concatenated file.

        Args:
            file_list: List of file info dictionaries with 'duration'

        Returns:
            List of timestamp dictionaries with start, end, and formatted times
        """
        timestamps = []
        current_time = 0

        for idx, file_info in enumerate(file_list, start=1):
            duration = file_info.get("duration", 0)
            start_time = current_time
            end_time = current_time + duration

            timestamps.append({
                "track_number": idx,
                "title": file_info.get("title", "Unknown"),
                "start": start_time,
                "end": end_time,
                "start_formatted": AudioConcatenator._format_timestamp(start_time),
                "end_formatted": AudioConcatenator._format_timestamp(end_time),
                "duration": duration,
            })

            current_time = end_time

        return timestamps

    @staticmethod
    def _format_timestamp(seconds: int) -> str:
        """
        Format seconds into HH:MM:SS timestamp.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def _create_concat_list(file_list: list[dict[str, Any]], output_path: Path) -> None:
        """
        Create a concat list file for ffmpeg.

        Args:
            file_list: List of file info dictionaries with 'path'
            output_path: Path where the concat list file should be created
        """
        lines = []
        for file_info in file_list:
            file_path = file_info["path"]
            # Use absolute path and escape single quotes
            abs_path = str(file_path.absolute()).replace("'", "'\\''")
            lines.append(f"file '{abs_path}'")

        output_path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def concatenate_files_randomized(
        file_list: list[dict[str, Any]],
        output_path: Path,
        quality: str = "192",
        announce_tracks: bool = True,
    ) -> dict[str, Any]:
        """
        Concatenate multiple audio files into a single MP3 file in randomized order.

        Args:
            file_list: List of file info dictionaries with 'path' and 'duration'
            output_path: Path for the output concatenated file
            quality: MP3 quality in kbps

        Returns:
            Dictionary with concatenation info including timestamps and shuffled order
        """
        if not file_list:
            raise ValueError("No files to concatenate")

        # Create a shuffled copy of the file list, re-number for announcements
        shuffled_list = file_list.copy()
        random.shuffle(shuffled_list)
        for idx, item in enumerate(shuffled_list, start=1):
            item["_idx"] = idx

        # Use the regular concatenation with the shuffled list
        result = AudioConcatenator.concatenate_files(shuffled_list, output_path, quality, announce_tracks=announce_tracks)

        # Add the shuffled order to the result
        result["shuffled_order"] = shuffled_list

        return result

    @staticmethod
    def generate_track_listing(
        output_path: Path,
        concat_info: dict[str, Any],
        playlist_title: str,
    ) -> Path:
        """
        Generate a track listing text file for a randomized concatenation.

        Args:
            output_path: Path where the track listing file should be saved
            concat_info: Dictionary with concatenation info including timestamps
            playlist_title: Title of the playlist

        Returns:
            Path to the created track listing file
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("RANDOMIZED TRACK LISTING")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Playlist: {playlist_title}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Duration: {AudioConcatenator._format_timestamp(concat_info['total_duration'])}")
        lines.append("")
        lines.append("=" * 80)
        lines.append("TRACK ORDER")
        lines.append("=" * 80)
        lines.append("")

        for ts in concat_info["timestamps"]:
            lines.append(f"{ts['track_number']:3d}. {ts['title']}")
            lines.append(f"     [{ts['start_formatted']} - {ts['end_formatted']}]")
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("Generated by StreamsToFiles")
        lines.append("=" * 80)

        output_path.write_text("\n".join(lines), encoding="utf-8")

        return output_path
