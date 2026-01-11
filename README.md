# StreamsToFiles

A Python CLI tool that downloads YouTube playlists and converts them to MP3 files with proper ID3 tags, embedded album art, and generates an m3u playlist file.

## Features

- Download entire YouTube playlists as MP3 files
- Convert audio at 192 kbps quality (configurable: 128, 192, or 320 kbps)
- Add comprehensive ID3 tags to each MP3:
  - Title (video title)
  - Artist (channel/uploader name)
  - Album (playlist title)
  - Track number and total tracks
  - Comment (original YouTube URL)
  - Embedded album art (video thumbnail)
- Files are numbered sequentially (01-xxx.mp3, 02-xxx.mp3) for proper ordering
- Generate m3u playlist file with extended metadata
- Create playlist metadata file with track listing and YouTube URLs
- Organized output: `files/{sanitized-playlist-title}/`

## Requirements

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver
- ffmpeg - Required by yt-dlp for audio conversion

### Installing ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use:
```bash
winget install ffmpeg
```

## Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tools-streamstofiles
   ```

3. **Set up the environment:**
   ```bash
   make setup
   ```

4. **Install the package:**
   ```bash
   make install
   ```

## Usage

### Basic Usage

Use the default example playlist:
```bash
streamstofiles
```

Or run via uv without installation:
```bash
uv run streamstofiles
```

Or use the Makefile:
```bash
make run
```

### Custom Playlist

Download a specific YouTube playlist:
```bash
streamstofiles "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

### Advanced Options

**Change audio quality:**
```bash
streamstofiles --quality 320
```

**Specify output directory:**
```bash
streamstofiles --output-dir ~/music
```

**Skip ID3 tag updates:**
```bash
streamstofiles --no-update-tags
```

**Combine options:**
```bash
streamstofiles "https://youtube.com/playlist?list=..." --quality 320 --output-dir ~/downloads
```

### View All Options

```bash
streamstofiles --help
```

## Output Structure

Files are organized as follows:

```
files/
└── Sanitized_Playlist_Title/
    ├── 01-First_Video_Title.mp3
    ├── 02-Second_Video_Title.mp3
    ├── 03-Third_Video_Title.mp3
    ├── playlist.m3u
    └── playlist_info.txt
```

**Each MP3 file contains:**
- High-quality audio (192 kbps by default)
- Complete ID3 tags (title, artist, album, track number, original YouTube URL)
- Embedded album art (video thumbnail)

**The `playlist.m3u` file** can be opened in any media player that supports m3u playlists (VLC, iTunes, etc.).

**The `playlist_info.txt` file** contains:
- Playlist title and original YouTube URL
- Download date and output directory
- Complete track listing with metadata (title, artist, duration, YouTube URL)
- Easy reference to find original sources

## How It Works

1. **Playlist Extraction**: Uses yt-dlp to fetch playlist metadata and video information
2. **Audio Download**: Downloads best available audio for each video
3. **MP3 Conversion**: Converts audio to MP3 format using ffmpeg at specified quality
4. **ID3 Tagging**: Adds comprehensive metadata tags (including YouTube URL) using mutagen library
5. **Album Art**: Embeds video thumbnail as album art in each MP3
6. **M3U Generation**: Creates an extended m3u playlist with all tracks
7. **Metadata File**: Generates a text file with complete playlist and track information

## Development

### Project Structure

```
.
├── src/
│   └── streamstofiles/
│       ├── __init__.py       # Package initialization
│       ├── cli.py            # Click-based CLI
│       ├── downloader.py     # yt-dlp integration
│       ├── converter.py      # ID3 tag management
│       ├── playlist.py       # M3U generation
│       ├── metadata.py       # Playlist metadata file generation
│       └── utils.py          # Utility functions
├── pyproject.toml            # Project metadata and dependencies
├── Makefile                  # Common development tasks
└── README.md                 # This file
```

### Makefile Commands

- `make help` - Show all available commands
- `make setup` - Initialize uv environment and install dependencies
- `make install` - Install package in development mode
- `make run` - Run with default example playlist
- `make clean` - Remove output files and build artifacts

### Dependencies

- **yt-dlp**: YouTube video/playlist downloading
- **click**: Command-line interface framework
- **mutagen**: ID3 tag manipulation for MP3 files
- **ffmpeg**: (System dependency) Required for audio conversion

### Development Setup

1. Fork and clone the repository
2. Run `make setup` to install dependencies
3. Make your changes
4. Test with `uv run streamstofiles`
5. Submit a pull request

## Examples

### Use Case: PocketCasts File Upload

The numbered filename prefix (01-xxx, 02-xxx) ensures proper ordering when uploading files to podcast apps like PocketCasts:

```bash
# Download a playlist for PocketCasts
streamstofiles "https://youtube.com/playlist?list=YOUR_EDUCATIONAL_PLAYLIST"

# Files will be created as:
# 01-Introduction.mp3
# 02-Chapter_One.mp3
# 03-Chapter_Two.mp3
# etc.
```

Simply upload the entire directory to PocketCasts Files feature for sequential playback.

### Downloading Multiple Playlists

```bash
# Educational playlist
streamstofiles "https://youtube.com/playlist?list=EDUCATION_ID" --quality 128

# Music playlist with high quality
streamstofiles "https://youtube.com/playlist?list=MUSIC_ID" --quality 320

# Podcast playlist to custom directory
streamstofiles "https://youtube.com/playlist?list=PODCAST_ID" --output-dir ~/podcasts
```

## Troubleshooting

### ffmpeg not found
```
Error: ffmpeg not found
```
Install ffmpeg using your system package manager (see Requirements section).

### Permission denied
```
Error: Permission denied writing to files/
```
Ensure you have write permissions in the current directory or specify a different `--output-dir`.

### Video unavailable
```
Error: Video unavailable
```
Some videos in playlists may be private, deleted, or region-restricted. The tool will skip these and continue with available videos.

## License

[Add your license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
