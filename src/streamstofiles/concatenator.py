"""Audio file concatenation for creating single long-form files."""

import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


class AudioConcatenator:
    """Concatenates multiple audio files into a single long file."""

    @staticmethod
    def concatenate_files(
        file_list: list[dict[str, Any]],
        output_path: Path,
        quality: str = "192",
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

        # Calculate timestamps for each track in the concatenated file
        timestamps = AudioConcatenator._calculate_timestamps(file_list)

        # Create a temporary file list for ffmpeg concat demuxer
        concat_list_path = output_path.parent / "concat_list.txt"
        AudioConcatenator._create_concat_list(file_list, concat_list_path)

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

        # Create a shuffled copy of the file list
        shuffled_list = file_list.copy()
        random.shuffle(shuffled_list)

        # Use the regular concatenation with the shuffled list
        result = AudioConcatenator.concatenate_files(shuffled_list, output_path, quality)

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
