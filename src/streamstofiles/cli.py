"""Command-line interface for streamstofiles."""

from pathlib import Path

import click

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
        click.echo(f"Total tracks: {result['total_tracks']}")
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

        # Generate metadata info file
        if result["files"]:
            click.echo("Generating metadata file...")
            info_path = result["playlist_dir"] / "playlist_info.txt"
            MetadataGenerator.generate_info_file(info_path, playlist_url, result, concat_info)
            click.echo(f"  ✓ Created metadata file: {info_path}")
            click.echo()

        # Summary
        click.echo("=" * 60)
        click.echo(f"✓ Successfully processed {len(result['files'])} tracks")
        click.echo(f"✓ Files saved to: {result['playlist_dir']}")
        click.echo(f"✓ Playlist file: {result['playlist_dir']}/playlist.m3u")
        if concat_info:
            click.echo(f"✓ Concatenated file: {concat_info['path'].name}")
        click.echo(f"✓ Metadata file: {result['playlist_dir']}/playlist_info.txt")
        click.echo("=" * 60)

    except KeyboardInterrupt:
        click.echo("\n\nDownload interrupted by user.")
        raise click.Abort()
    except Exception as e:
        click.echo(f"\n\nError: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
