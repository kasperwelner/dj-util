"""Progress feedback for long-running operations."""
import sys
import time
from typing import Optional


class ProgressIndicator:
    """Simple progress indicator for terminal output."""
    
    def __init__(self, message: str = "Processing"):
        """Initialize progress indicator.
        
        Args:
            message: Base message to display
        """
        self.message = message
        self.active = False
        self.start_time = None
        self.last_update = None
    
    def start(self, suffix: str = "") -> None:
        """Start showing progress.
        
        Args:
            suffix: Additional text to append to message
        """
        self.active = True
        self.start_time = time.time()
        self.last_update = self.start_time
        
        full_message = f"{self.message} {suffix}".strip()
        if sys.stdout.isatty():
            print(f"\r{full_message}...", end="", flush=True)
        else:
            print(f"{full_message}...")
    
    def update(self, suffix: str = "") -> None:
        """Update progress message.
        
        Args:
            suffix: New suffix text
        """
        if not self.active:
            return
        
        now = time.time()
        if now - self.last_update < 0.1:  # Throttle updates
            return
        
        self.last_update = now
        elapsed = int(now - self.start_time)
        
        full_message = f"{self.message} {suffix}".strip()
        if sys.stdout.isatty():
            # Add spinner animation
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            spin_char = spinner[elapsed % len(spinner)]
            print(f"\r{spin_char} {full_message}... ({elapsed}s)", end="", flush=True)
        # Non-TTY updates are skipped to avoid spam
    
    def stop(self, success: bool = True, message: Optional[str] = None) -> None:
        """Stop showing progress.
        
        Args:
            success: Whether operation succeeded
            message: Final message to display
        """
        if not self.active:
            return
        
        self.active = False
        elapsed = time.time() - self.start_time
        
        if message:
            final_msg = message
        elif success:
            final_msg = f"{self.message} completed"
        else:
            final_msg = f"{self.message} failed"
        
        if sys.stdout.isatty():
            # Clear line and show final message
            print(f"\r{final_msg} ({elapsed:.1f}s)          ")
        else:
            print(f"{final_msg} ({elapsed:.1f}s)")


class ProgressBar:
    """Progress bar for operations with known item count."""
    
    def __init__(self, total: int, message: str = "Progress"):
        """Initialize progress bar.
        
        Args:
            total: Total number of items
            message: Message to display
        """
        self.total = total
        self.message = message
        self.current = 0
        self.start_time = None
        self.width = 40  # Bar width in characters
    
    def start(self) -> None:
        """Start the progress bar."""
        self.start_time = time.time()
        self.current = 0
        self._draw()
    
    def update(self, current: Optional[int] = None) -> None:
        """Update progress.
        
        Args:
            current: Current item number, or None to increment
        """
        if current is not None:
            self.current = min(current, self.total)
        else:
            self.current = min(self.current + 1, self.total)
        
        self._draw()
    
    def finish(self) -> None:
        """Complete the progress bar."""
        self.current = self.total
        self._draw()
        if sys.stdout.isatty():
            print()  # New line after progress bar
    
    def _draw(self) -> None:
        """Draw the progress bar."""
        if not sys.stdout.isatty():
            # Only show milestones in non-TTY
            milestones = [25, 50, 75, 100]
            percent = int(100 * self.current / self.total) if self.total > 0 else 0
            if percent in milestones and self.current > 0:
                print(f"{self.message}: {percent}%")
            return
        
        # Calculate progress
        percent = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * percent)
        
        # Create bar
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Calculate ETA
        eta_str = ""
        if self.start_time and self.current > 0:
            elapsed = time.time() - self.start_time
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            if remaining > 0:
                eta_str = f" ETA: {int(remaining)}s"
        
        # Draw
        print(f"\r{self.message}: [{bar}] {self.current}/{self.total}{eta_str}", 
              end="", flush=True)


def show_spinner(message: str, duration: float = 2.0) -> None:
    """Show a simple spinner for a fixed duration.
    
    Args:
        message: Message to display
        duration: How long to show spinner
    """
    if not sys.stdout.isatty():
        print(f"{message}...")
        time.sleep(duration)
        return
    
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration
    i = 0
    
    while time.time() < end_time:
        print(f"\r{spinner[i % len(spinner)]} {message}...", end="", flush=True)
        time.sleep(0.1)
        i += 1
    
    print(f"\r✓ {message}       ")


def format_track_count(count: int) -> str:
    """Format track count for display.
    
    Args:
        count: Number of tracks
        
    Returns:
        Formatted string
    """
    if count == 0:
        return "No tracks"
    elif count == 1:
        return "1 track"
    else:
        return f"{count:,} tracks"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"