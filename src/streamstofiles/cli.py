"""Command-line interface for streamstofiles."""

import re
from datetime import date
from pathlib import Path
from typing import Any

import click
from mutagen.mp3 import MP3

from .downloader import PlaylistDownloader
from .converter import ID3Tagger
from .playlist import PlaylistGenerator
from .metadata import MetadataGenerator
from .concatenator import AudioConcatenator

# Default playlist URL
DEFAULT_PLAYLIST = "https://www.youtube.com/watch?v=LZmtl3l1R9A&list=PLW7vZQVayoR0wLs2ahN7h774_XsD-dp-2"


@click.command()
@click.argument("playlist_url", default=DEFAULT_PLAYLIST, required=False)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default="files",
    help="Output directory for downloaded files (default: files/)",
)
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["128", "192", "320"]),
    default="192",
    help="MP3 quality in kbps (default: 192)",
)
@click.option(
    "--update-tags/--no-update-tags",
    default=True,
    help="Update ID3 tags after download (default: enabled)",
)
@click.option(
    "--concatenate/--no-concatenate",
    default=True,
    help="Create a single concatenated file from all tracks (default: enabled)",
)
def main(
    playlist_url: str,
    output_dir: Path,
    quality: str,
    update_tags: bool,
    concatenate: bool,
) -> None:
    """
    Download a YouTube playlist and convert to MP3 files with ID3 tags and m3u playlist.

    PLAYLIST_URL: YouTube playlist URL (defaults to example playlist if not provided)

    Examples:

        # Use default playlist
        $ streamstofiles

        # Download a specific playlist
        $ streamstofiles "https://youtube.com/playlist?list=..."

        # Change quality and output directory
        $ streamstofiles --quality 320 --output-dir ~/music
    """
    click.echo(f"StreamsToFiles - YouTube Playlist to MP3 Converter")
    click.echo(f"=" * 60)
    click.echo(f"Playlist URL: {playlist_url}")
    click.echo(f"Output directory: {output_dir}")
    click.echo(f"Quality: {quality} kbps")
    click.echo(f"Concatenate: {'Yes' if concatenate else 'No'}")
    click.echo(f"=" * 60)
    click.echo()

    try:
        # Initialize downloader
        downloader = PlaylistDownloader(output_dir, quality)

        # Download playlist
        click.echo("Downloading playlist...")
        result = downloader.download_playlist(playlist_url)

        click.echo(f"\n\nDownload complete!")
        click.echo(f"Playlist: {result['playlist_title']}")
        downloaded = len(result['files'])
        total = result['total_tracks']
        failed = total - downloaded
        pct = (downloaded / total * 100) if total > 0 else 0
        click.echo(f"Downloaded: {downloaded}/{total} tracks ({pct:.0f}%)")
        if failed > 0:
            click.echo(f"Failed: {failed} tracks")
        click.echo(f"Output directory: {result['playlist_dir']}")
        click.echo()

        # Update ID3 tags if requested
        if update_tags and result["files"]:
            click.echo("Updating ID3 tags...")
            for file_info in result["files"]:
                ID3Tagger.update_tags(file_info["path"], file_info)
                click.echo(f"  ✓ Updated tags for: {file_info['path'].name}")
            click.echo()

        # Generate m3u playlist
        if result["files"]:
            click.echo("Generating m3u playlist...")
            playlist_path = result["playlist_dir"] / "playlist.m3u"
            PlaylistGenerator.generate_m3u(playlist_path, result["files"])
            click.echo(f"  ✓ Created playlist: {playlist_path}")
            click.echo()

        # Concatenate files if requested
        concat_info = None
        randomized_concat_info = None
        if concatenate and result["files"]:
            click.echo("Concatenating audio files...")
            concat_filename = f"{result['playlist_dir'].name}_complete.mp3"
            concat_path = result["playlist_dir"] / concat_filename
            concat_info = AudioConcatenator.concatenate_files(
                result["files"],
                concat_path,
                quality
            )
            click.echo(f"  ✓ Created concatenated file: {concat_path.name}")
            click.echo(f"  ✓ Total duration: {AudioConcatenator._format_timestamp(concat_info['total_duration'])}")
            click.echo()

            # Create randomized concatenation
            click.echo("Creating randomized concatenation...")
            today = date.today().isoformat()
            randomized_filename = f"{result['playlist_dir'].name}_randomized_{today}.mp3"
            randomized_path = result["playlist_dir"] / randomized_filename
            randomized_concat_info = AudioConcatenator.concatenate_files_randomized(
                result["files"],
                randomized_path,
                quality
            )
            click.echo(f"  ✓ Created randomized file: {randomized_path.name}")

            # Generate track listing for randomized version
            tracklist_filename = f"randomized_tracklist_{today}.txt"
            tracklist_path = result["playlist_dir"] / tracklist_filename
            AudioConcatenator.generate_track_listing(
                tracklist_path,
                randomized_concat_info,
                result["playlist_title"]
            )
            click.echo(f"  ✓ Created track listing: {tracklist_path.name}")
            click.echo()

        # Generate metadata info file
        if result["files"]:
            click.echo("Generating metadata file...")
            info_path = result["playlist_dir"] / "playlist_info.txt"
            MetadataGenerator.generate_info_file(info_path, playlist_url, result, concat_info)
            click.echo(f"  ✓ Created metadata file: {info_path}")
            click.echo()

        # Summary
        click.echo("=" * 60)
        click.echo(f"✓ Successfully processed {downloaded}/{total} tracks ({pct:.0f}%)")
        click.echo(f"✓ Files saved to: {result['playlist_dir']}")
        click.echo(f"✓ Playlist file: {result['playlist_dir']}/playlist.m3u")
        if concat_info:
            click.echo(f"✓ Concatenated file: {concat_info['path'].name}")
        if randomized_concat_info:
            click.echo(f"✓ Randomized file: {randomized_concat_info['path'].name}")
            click.echo(f"✓ Track listing: {result['playlist_dir']}/randomized_tracklist.txt")
        click.echo(f"✓ Metadata file: {result['playlist_dir']}/playlist_info.txt")
        click.echo("=" * 60)

    except KeyboardInterrupt:
        click.echo("\n\nDownload interrupted by user.")
        raise click.Abort()
    except Exception as e:
        click.echo(f"\n\nError: {e}", err=True)
        raise click.Abort()


def scan_existing_tracks(directory: Path) -> list[dict[str, Any]]:
    """
    Scan a directory for existing numbered MP3 track files.

    Args:
        directory: Path to the playlist directory

    Returns:
        List of file info dictionaries sorted by track number
    """
    files = []
    # Match files like "01-Title.mp3", "02-Title.mp3", etc.
    # Exclude concatenated files (*_complete.mp3, *_randomized.mp3)
    pattern = re.compile(r"^(\d+)-(.+)\.mp3$")

    for mp3_file in directory.glob("*.mp3"):
        # Skip concatenated files
        if mp3_file.name.endswith("_complete.mp3") or mp3_file.name.endswith("_randomized.mp3"):
            continue

        match = pattern.match(mp3_file.name)
        if match:
            track_num = int(match.group(1))
            try:
                # Get duration from the MP3 file
                audio = MP3(mp3_file)
                duration = int(audio.info.length)

                # Get title from ID3 tags or filename
                title = match.group(2).replace("_", " ")
                if audio.tags and "TIT2" in audio.tags:
                    title = str(audio.tags["TIT2"])

                files.append({
                    "path": mp3_file,
                    "title": title,
                    "duration": duration,
                    "track_number": track_num,
                })
            except Exception as e:
                click.echo(f"  Warning: Could not read {mp3_file.name}: {e}", err=True)

    # Sort by track number
    files.sort(key=lambda x: x["track_number"])
    return files


@click.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["128", "192", "320"]),
    default="192",
    help="MP3 quality in kbps (default: 192)",
)
def rerandomize(directory: Path, quality: str) -> None:
    """
    Re-randomize existing tracks into a new concatenated file.

    DIRECTORY: Path to a playlist directory containing numbered MP3 files

    This command scans an existing playlist directory for numbered track files
    (e.g., 01-Title.mp3, 02-Title.mp3), validates they exist, and creates a new
    randomized concatenation with a fresh track listing.

    Examples:

        # Re-randomize tracks in a playlist directory
        $ rerandomize files/My_Playlist/

        # Re-randomize with higher quality encoding
        $ rerandomize files/My_Playlist/ --quality 320
    """
    click.echo("StreamsToFiles - Re-randomize Existing Tracks")
    click.echo("=" * 60)
    click.echo(f"Directory: {directory}")
    click.echo(f"Quality: {quality} kbps")
    click.echo("=" * 60)
    click.echo()

    try:
        # Scan for existing track files
        click.echo("Scanning for existing tracks...")
        files = scan_existing_tracks(directory)

        if not files:
            click.echo("Error: No numbered MP3 track files found in directory.", err=True)
            click.echo("Expected files like: 01-Title.mp3, 02-Title.mp3, etc.", err=True)
            raise click.Abort()

        click.echo(f"  Found {len(files)} tracks:")
        for f in files:
            click.echo(f"    {f['track_number']:02d}. {f['title']} ({AudioConcatenator._format_timestamp(f['duration'])})")
        click.echo()

        # Validate all files exist and are readable
        click.echo("Validating files...")
        missing_files = [f for f in files if not f["path"].exists()]
        if missing_files:
            click.echo("Error: The following files are missing:", err=True)
            for f in missing_files:
                click.echo(f"  - {f['path']}", err=True)
            raise click.Abort()
        click.echo("  ✓ All files validated")
        click.echo()

        # Get playlist title from directory name
        playlist_title = directory.name.replace("_", " ")

        # Create randomized concatenation with date in filename
        click.echo("Creating randomized concatenation...")
        today = date.today().isoformat()
        randomized_filename = f"{directory.name}_randomized_{today}.mp3"
        randomized_path = directory / randomized_filename
        randomized_concat_info = AudioConcatenator.concatenate_files_randomized(
            files,
            randomized_path,
            quality
        )
        click.echo(f"  ✓ Created randomized file: {randomized_path.name}")
        click.echo(f"  ✓ Total duration: {AudioConcatenator._format_timestamp(randomized_concat_info['total_duration'])}")
        click.echo()

        # Generate track listing
        click.echo("Generating track listing...")
        tracklist_filename = f"randomized_tracklist_{today}.txt"
        tracklist_path = directory / tracklist_filename
        AudioConcatenator.generate_track_listing(
            tracklist_path,
            randomized_concat_info,
            playlist_title
        )
        click.echo(f"  ✓ Created track listing: {tracklist_path.name}")
        click.echo()

        # Summary
        click.echo("=" * 60)
        click.echo(f"✓ Successfully re-randomized {len(files)} tracks")
        click.echo(f"✓ Randomized file: {randomized_path.name}")
        click.echo(f"✓ Track listing: {tracklist_path.name}")
        click.echo("=" * 60)

    except click.Abort:
        raise
    except KeyboardInterrupt:
        click.echo("\n\nOperation interrupted by user.")
        raise click.Abort()
    except Exception as e:
        click.echo(f"\n\nError: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
