"""Tests for audio converter service."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.services.audio_converter import AudioConverter, ConversionResult


class TestAudioConverter:
    """Test suite for AudioConverter."""

    def test_init_finds_ffmpeg_in_path(self):
        """Test that AudioConverter finds ffmpeg in PATH."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            assert converter.ffmpeg_path == "/usr/bin/ffmpeg"

    def test_init_raises_when_ffmpeg_not_found(self):
        """Test that AudioConverter raises error when ffmpeg not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="ffmpeg not found"):
                AudioConverter()

    def test_init_accepts_custom_ffmpeg_path(self, tmp_path):
        """Test that AudioConverter accepts custom ffmpeg path."""
        ffmpeg_path = tmp_path / "ffmpeg"
        ffmpeg_path.touch()
        
        converter = AudioConverter(ffmpeg_path=str(ffmpeg_path))
        assert converter.ffmpeg_path == str(ffmpeg_path)

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            formats = converter.get_supported_formats()
            
            assert "wav" in formats
            assert "flac" in formats
            assert "mp3" in formats
            assert "aac" in formats
            assert "alac" in formats
            assert "WAV" in formats["wav"]

    def test_is_conversion_needed_same_format(self):
        """Test that conversion is not needed for same format."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = Path("/test/file.flac")
            assert not converter.is_conversion_needed(source, "flac")
            assert not converter.is_conversion_needed(source, "FLAC")

    def test_is_conversion_needed_different_format(self):
        """Test that conversion is needed for different format."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = Path("/test/file.mp3")
            assert converter.is_conversion_needed(source, "wav")
            assert converter.is_conversion_needed(source, "flac")

    def test_is_conversion_needed_none_format(self):
        """Test that no conversion needed when format is None."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = Path("/test/file.mp3")
            assert not converter.is_conversion_needed(source, None)

    def test_is_conversion_needed_aac_m4a_normalization(self):
        """Test AAC/M4A format normalization."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            # .m4a and 'aac' should be considered the same
            source = Path("/test/file.m4a")
            assert not converter.is_conversion_needed(source, "aac")
            
            # .aac and 'm4a' should be considered the same
            source = Path("/test/file.aac")
            assert not converter.is_conversion_needed(source, "m4a")

    def test_convert_source_not_found(self):
        """Test conversion fails when source file not found."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = Path("/nonexistent/file.mp3")
            result = converter.convert(source, "wav")
            
            assert not result.success
            assert "not found" in result.error_message.lower()
            assert result.original_path == source

    def test_convert_unsupported_format(self, tmp_path):
        """Test conversion fails for unsupported format."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.touch()
            
            result = converter.convert(source, "ogg")
            
            assert not result.success
            assert "Unsupported format" in result.error_message

    def test_convert_output_already_exists(self, tmp_path):
        """Test conversion fails when output exists and overwrite=False."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.touch()
            
            output = tmp_path / "test.wav"
            output.touch()
            
            result = converter.convert(source, "wav", overwrite=False)
            
            assert not result.success
            assert "already exists" in result.error_message.lower()

    def test_convert_success(self, tmp_path):
        """Test successful conversion."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.write_text("fake mp3 data")
            
            output = tmp_path / "test.wav"
            
            # Mock subprocess.run to simulate successful conversion
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            def create_output_file(*args, **kwargs):
                # Simulate ffmpeg creating the output file
                output.touch()
                return mock_result
            
            with patch("subprocess.run", side_effect=create_output_file):
                result = converter.convert(source, "wav")
            
            assert result.success
            assert result.output_path == output
            assert result.original_path == source

    def test_convert_preserves_original_by_default(self, tmp_path):
        """Test that original file is preserved by default."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.write_text("fake mp3 data")
            output = tmp_path / "test.wav"
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            def create_output_file(*args, **kwargs):
                output.touch()
                return mock_result
            
            with patch("subprocess.run", side_effect=create_output_file):
                result = converter.convert(source, "wav", preserve_original=True)
            
            # Original should still exist
            assert source.exists()
            assert result.success

    def test_convert_deletes_original_when_requested(self, tmp_path):
        """Test that original file is deleted when preserve_original=False."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.write_text("fake mp3 data")
            output = tmp_path / "test.wav"
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            def create_output_file(*args, **kwargs):
                output.touch()
                return mock_result
            
            with patch("subprocess.run", side_effect=create_output_file):
                result = converter.convert(source, "wav", preserve_original=False)
            
            # Original should be deleted
            assert not source.exists()
            assert result.success

    def test_convert_ffmpeg_error(self, tmp_path):
        """Test conversion handles ffmpeg errors."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.write_text("fake mp3 data")
            
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "ffmpeg error: invalid codec"
            
            with patch("subprocess.run", return_value=mock_result):
                result = converter.convert(source, "wav")
            
            assert not result.success
            assert "ffmpeg error" in result.error_message

    def test_convert_timeout(self, tmp_path):
        """Test conversion handles timeouts."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.write_text("fake mp3 data")
            
            with patch("subprocess.run", side_effect=TimeoutError("Timeout")):
                result = converter.convert(source, "wav")
            
            assert not result.success

    def test_build_ffmpeg_command_wav(self):
        """Test building ffmpeg command for WAV."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = Path("/test/input.mp3")
            output = Path("/test/output.wav")
            config = converter.FORMAT_CONFIGS["wav"]
            
            cmd = converter._build_ffmpeg_command(source, output, config)
            
            assert "/usr/bin/ffmpeg" in cmd
            assert "-i" in cmd
            assert str(source) in cmd
            assert "-codec:a" in cmd
            assert "pcm_s16le" in cmd
            assert str(output) in cmd

    def test_build_ffmpeg_command_mp3_with_bitrate(self):
        """Test building ffmpeg command for MP3 with bitrate."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = Path("/test/input.wav")
            output = Path("/test/output.mp3")
            config = converter.FORMAT_CONFIGS["mp3"]
            
            cmd = converter._build_ffmpeg_command(source, output, config)
            
            assert "-b:a" in cmd
            assert "320k" in cmd
            assert "libmp3lame" in cmd

    def test_build_ffmpeg_command_flac_with_compression(self):
        """Test building ffmpeg command for FLAC with compression."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = Path("/test/input.wav")
            output = Path("/test/output.flac")
            config = converter.FORMAT_CONFIGS["flac"]
            
            cmd = converter._build_ffmpeg_command(source, output, config)
            
            assert "-compression_level" in cmd
            assert "8" in cmd
            assert "flac" in cmd

    def test_probe_format(self, tmp_path):
        """Test probing audio format."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            converter = AudioConverter()
            
            source = tmp_path / "test.mp3"
            source.touch()
            
            # Test fallback to extension when ffprobe not available
            with patch("shutil.which", return_value=None):
                format_str = converter.probe_format(source)
                assert format_str == "mp3"

    def test_probe_format_with_ffprobe(self, tmp_path):
        """Test probing format with ffprobe."""
        with patch("shutil.which", side_effect=lambda x: "/usr/bin/" + x):
            converter = AudioConverter()
            
            source = tmp_path / "test.m4a"
            source.touch()
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "alac\n"
            
            with patch("subprocess.run", return_value=mock_result):
                format_str = converter.probe_format(source)
                assert format_str == "alac"
