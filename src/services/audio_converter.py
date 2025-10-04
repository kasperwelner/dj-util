"""
Audio conversion service using ffmpeg.

Supports converting audio files to different formats while preserving metadata.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of audio conversion operation."""

    success: bool
    output_path: Optional[Path]
    error_message: Optional[str] = None
    original_path: Optional[Path] = None


class AudioConverter:
    """Service for converting audio files using ffmpeg."""

    # Common audio format configurations
    FORMAT_CONFIGS = {
        "wav": {
            "codec": "pcm_s16le",
            "container": "wav",
            "description": "WAV (PCM 16-bit)",
        },
        "aiff": {
            "codec": "pcm_s16be",
            "container": "aiff",
            "description": "AIFF (PCM 16-bit)",
        },
        "flac": {
            "codec": "flac",
            "container": "flac",
            "description": "FLAC (lossless)",
            "compression": "8",  # Max compression
        },
        "mp3": {
            "codec": "libmp3lame",
            "container": "mp3",
            "description": "MP3 (320kbps)",
            "bitrate": "320k",
        },
        "aac": {
            "codec": "aac",
            "container": "m4a",
            "description": "AAC (256kbps)",
            "bitrate": "256k",
        },
        "alac": {
            "codec": "alac",
            "container": "m4a",
            "description": "Apple Lossless (ALAC)",
        },
    }

    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        Initialize the audio converter.

        Args:
            ffmpeg_path: Optional path to ffmpeg binary. If None, searches PATH.

        Raises:
            RuntimeError: If ffmpeg is not found or not executable.
        """
        self.ffmpeg_path = self._find_ffmpeg(ffmpeg_path)

    def _find_ffmpeg(self, custom_path: Optional[str]) -> str:
        """Find ffmpeg binary."""
        if custom_path:
            if not Path(custom_path).is_file():
                raise RuntimeError(f"ffmpeg not found at: {custom_path}")
            return custom_path

        # Search in PATH
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(
                "ffmpeg not found. Install it with: brew install ffmpeg (macOS) "
                "or see https://ffmpeg.org/download.html"
            )

        return ffmpeg

    def is_conversion_needed(
        self, source_path: Path, target_format: Optional[str]
    ) -> bool:
        """
        Check if conversion is needed.

        Args:
            source_path: Source audio file path
            target_format: Desired format (e.g., 'wav', 'flac')

        Returns:
            True if conversion is needed, False otherwise
        """
        if not target_format:
            return False

        source_ext = source_path.suffix.lstrip(".").lower()
        target_format = target_format.lower()

        # Normalize m4a/aac
        if source_ext in ("m4a", "aac"):
            source_ext = "aac"
        if target_format in ("m4a", "aac"):
            target_format = "aac"

        # Normalize alac
        if source_ext == "alac" or target_format == "alac":
            # ALAC files have .m4a extension
            if source_ext == "m4a" and target_format == "alac":
                # Need to probe codec to be sure
                return True
            if source_ext == "alac" and target_format != "alac":
                return True

        return source_ext != target_format

    def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Optional[Path] = None,
        preserve_original: bool = True,
        overwrite: bool = False,
    ) -> ConversionResult:
        """
        Convert audio file to target format.

        Args:
            source_path: Source audio file
            target_format: Target format (wav, flac, mp3, aac, alac)
            output_dir: Output directory (defaults to source directory)
            preserve_original: Keep original file (default: True)
            overwrite: Overwrite existing output file (default: False)

        Returns:
            ConversionResult with success status and output path
        """
        # Validate inputs
        if not source_path.is_file():
            return ConversionResult(
                success=False,
                output_path=None,
                error_message=f"Source file not found: {source_path}",
                original_path=source_path,
            )

        target_format = target_format.lower()
        if target_format not in self.FORMAT_CONFIGS:
            return ConversionResult(
                success=False,
                output_path=None,
                error_message=f"Unsupported format: {target_format}. "
                f"Supported: {', '.join(self.FORMAT_CONFIGS.keys())}",
                original_path=source_path,
            )

        # Build output path
        config = self.FORMAT_CONFIGS[target_format]
        output_dir = output_dir or source_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        output_ext = config["container"]
        output_path = output_dir / f"{source_path.stem}.{output_ext}"

        # Check if output already exists
        if output_path.exists() and not overwrite:
            return ConversionResult(
                success=False,
                output_path=None,
                error_message=f"Output file already exists: {output_path}",
                original_path=source_path,
            )

        # Build ffmpeg command
        cmd = self._build_ffmpeg_command(source_path, output_path, config)

        # Execute conversion
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=300
            )

            if result.returncode != 0:
                return ConversionResult(
                    success=False,
                    output_path=None,
                    error_message=f"ffmpeg error: {result.stderr[:500]}",
                    original_path=source_path,
                )

            # Verify output was created
            if not output_path.is_file():
                return ConversionResult(
                    success=False,
                    output_path=None,
                    error_message="Conversion completed but output file not found",
                    original_path=source_path,
                )

            # Delete original if requested
            if not preserve_original:
                source_path.unlink()

            return ConversionResult(
                success=True, output_path=output_path, original_path=source_path
            )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                output_path=None,
                error_message="Conversion timed out (>5 minutes)",
                original_path=source_path,
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                error_message=f"Unexpected error: {str(e)}",
                original_path=source_path,
            )

    def _build_ffmpeg_command(
        self, source_path: Path, output_path: Path, config: Dict[str, str]
    ) -> List[str]:
        """Build ffmpeg command with proper arguments."""
        cmd = [
            self.ffmpeg_path,
            "-i",
            str(source_path),
            "-y",  # Overwrite output
            "-codec:a",
            config["codec"],
        ]

        # Add format-specific options
        if "bitrate" in config:
            cmd.extend(["-b:a", config["bitrate"]])

        if "compression" in config:
            cmd.extend(["-compression_level", config["compression"]])

        # Copy metadata
        cmd.extend(["-map_metadata", "0"])

        # Output file
        cmd.append(str(output_path))

        return cmd

    def get_supported_formats(self) -> Dict[str, str]:
        """
        Get dictionary of supported formats and descriptions.

        Returns:
            Dictionary mapping format codes to descriptions
        """
        return {fmt: cfg["description"] for fmt, cfg in self.FORMAT_CONFIGS.items()}

    def probe_format(self, file_path: Path) -> Optional[str]:
        """
        Probe audio file to detect actual format/codec.

        Args:
            file_path: Path to audio file

        Returns:
            Format string or None if detection fails
        """
        try:
            # Use ffprobe if available
            ffprobe = shutil.which("ffprobe")
            if not ffprobe:
                # Fallback to extension
                return file_path.suffix.lstrip(".").lower()

            cmd = [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                codec = result.stdout.strip()
                # Map codecs to our format names
                codec_map = {
                    "pcm_s16le": "wav",
                    "flac": "flac",
                    "mp3": "mp3",
                    "aac": "aac",
                    "alac": "alac",
                }
                return codec_map.get(codec, codec)

            return file_path.suffix.lstrip(".").lower()

        except Exception:
            return file_path.suffix.lstrip(".").lower()
