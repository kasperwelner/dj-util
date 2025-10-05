"""Bandcamp Wishlist Automator Service.

Automatically adds tracks from a CSV to your Bandcamp wishlist.
"""

import csv
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

@dataclass
class BandcampSearchResult:
    """Represents a search result from Bandcamp."""
    artist: str
    title: str
    url: str
    confidence: float = 0.0


LOGIN_URL = "https://bandcamp.com/login"


class BandcampWishlistAutomator:
    """Automates adding tracks to Bandcamp wishlist."""

    def __init__(
        self, username: str, password: str, delay_between_tracks: float = 2.0, progress_csv: str = "bandcamp_wishlist_progress.csv"
    ):
        """Initialize the automator.

        Args:
            username: Bandcamp username or email
            password: Bandcamp password
            delay_between_tracks: Seconds to wait between track processing
            progress_csv: Path to progress tracking CSV file
        """
        self.username = username
        self.password = password
        self.delay_between_tracks = delay_between_tracks
        self.progress_csv = progress_csv
        self.driver = None
        self.wait = None
        self.processed_ids = set()
        # Matching threshold for search results
        self.match_threshold = 0.6

    def is_owned(self) -> bool:
        """Return True if the visible page shows that the user owns the track."""
        if not self.driver:
            return False
        owned_xpaths = [
            "//h3[normalize-space(text())='You own this']",
            "//a[normalize-space(text())='You own this']",
        ]
        for xp in owned_xpaths:
            try:
                elems = self.driver.find_elements(By.XPATH, xp)
                for el in elems:
                    if el.is_displayed():
                        return True
            except Exception:
                continue
        return False

    def is_in_wishlist(self) -> bool:
        """Return True if the visible page shows 'In Wishlist' in the share panel area."""
        if not self.driver:
            return False
        try:
            el = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'share-panel-wrapper-desktop')]//*[normalize-space(text())='In Wishlist']",
            )
            return el.is_displayed()
        except NoSuchElementException:
            return False

    def setup_driver(self):
        """Initialize Chrome driver with webdriver-manager."""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # Comment out the next line if you want to see the browser
        # options.add_argument('--headless')

        # Use webdriver-manager to automatically download the correct ChromeDriver version
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)

        # Navigate to bandcamp first and dismiss cookies BEFORE login
        print("Initializing session and dismissing cookie dialog...")
        self.driver.get("https://bandcamp.com")
        time.sleep(2)
        self.dismiss_cookies()

    def dismiss_cookies(self):
        """Dismiss cookie consent banner if present."""
        try:
            # Wait a bit for dialog to appear
            time.sleep(1)

            # Try to find the "Accept all" button by exact text match
            try:
                cookie_button = self.driver.find_element(By.XPATH, "//button[text()='Accept all']")
                if cookie_button.is_displayed():
                    print("Dismissing cookie banner...")
                    # Scroll into view first
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cookie_button)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", cookie_button)
                    time.sleep(1)
                    print("✓ Cookie banner dismissed")
                    return
            except (NoSuchElementException, Exception):
                pass

            # Try partial text match
            try:
                cookie_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept all')]")
                if cookie_button.is_displayed():
                    print("Dismissing cookie banner...")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cookie_button)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", cookie_button)
                    time.sleep(1)
                    print("✓ Cookie banner dismissed")
                    return
            except (NoSuchElementException, Exception):
                pass

            # Try alternative selectors
            cookie_selectors = [
                "button[aria-label*='accept' i]",
                "button[aria-label*='consent' i]",
                "button[aria-label*='cookie' i]",
                ".gdpr-notice button",
                "#onetrust-accept-btn-handler",
                "button[id*='accept' i]",
                "button[class*='accept' i]",
            ]

            for selector in cookie_selectors:
                try:
                    cookie_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if cookie_button.is_displayed():
                        print("Dismissing cookie banner...")
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cookie_button)
                        time.sleep(0.3)
                        self.driver.execute_script("arguments[0].click();", cookie_button)
                        time.sleep(1)
                        print("✓ Cookie banner dismissed")
                        return
                except NoSuchElementException:
                    continue
                except:
                    continue
        except:
            pass  # No cookie banner found, continue
    
    def _clean_text(self, text: str) -> str:
        """Clean text for matching (same logic as file_path_matcher).
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned lowercase text
        """
        if not text:
            return ""
        
        # Remove content in parentheses and brackets
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        
        # Remove special characters (keep spaces for word matching)
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings.
        
        Uses same approach as file_path_matcher:
        70% sequential similarity + 30% word overlap similarity.
        
        Args:
            text1: First text to compare
            text2: Second text to compare
            
        Returns:
            Similarity score (0.0-1.0)
        """
        clean1 = self._clean_text(text1)
        clean2 = self._clean_text(text2)
        
        if not clean1 or not clean2:
            return 0.0
        
        # Sequential similarity (70% weight)
        sequence_sim = SequenceMatcher(None, clean1, clean2).ratio()
        
        # Word overlap similarity (30% weight)
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        if words1 and words2:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            word_sim = intersection / union if union > 0 else 0.0
        else:
            word_sim = 0.0
        
        # Combined score
        return (sequence_sim * 0.7) + (word_sim * 0.3)
    
    def _calculate_track_similarity(
        self, 
        target_artist: str, 
        target_title: str,
        result_artist: str, 
        result_title: str
    ) -> float:
        """Calculate overall similarity between target track and search result.
        
        Requires minimum title similarity (like file_path_matcher) and 
        weights artist/title matching separately.
        
        Args:
            target_artist: Artist we're looking for
            target_title: Title we're looking for  
            result_artist: Artist from search result
            result_title: Title from search result
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Title similarity (required minimum like file_path_matcher)
        title_sim = self._calculate_text_similarity(target_title, result_title)
        if title_sim < 0.3:  # Minimum title similarity threshold
            return 0.0  # No match if title doesn't have partial similarity
        
        # Artist similarity
        artist_sim = self._calculate_text_similarity(target_artist, result_artist)
        
        # Combined score: 60% title + 40% artist (title is more distinctive)
        return (title_sim * 0.6) + (artist_sim * 0.4)
    
    def _extract_search_results(self) -> List[BandcampSearchResult]:
        """Extract all search results from the current Bandcamp search page.
        
        Returns:
            List of BandcampSearchResult objects
        """
        results = []
        
        try:
            # Find all search result elements
            search_results = self.driver.find_elements(By.CSS_SELECTOR, ".searchresult")
            
            for result_elem in search_results:
                try:
                    # Get the track link
                    track_link = result_elem.find_element(By.CSS_SELECTOR, "a.artcont")
                    track_url = track_link.get_attribute("href")
                    
                    if not track_url:
                        continue
                    
                    # Extract artist and title from the search result
                    # Bandcamp typically shows: "Artist Name - Song Title"
                    artist = ""
                    title = ""
                    
                    try:
                        # Try to get artist from dedicated element
                        artist_elem = result_elem.find_element(By.CSS_SELECTOR, ".subhead")
                        artist = artist_elem.text.strip()
                        
                        # Remove "by " prefix if present
                        if artist.lower().startswith("by "):
                            artist = artist[3:].strip()
                    except NoSuchElementException:
                        pass
                    
                    try:
                        # Try to get title from main heading
                        title_elem = result_elem.find_element(By.CSS_SELECTOR, ".heading")
                        title = title_elem.text.strip()
                    except NoSuchElementException:
                        pass
                    
                    # Fallback: parse from combined text if we didn't get both
                    if not artist or not title:
                        try:
                            # Get combined text and try to split
                            combined_text = result_elem.find_element(By.CSS_SELECTOR, ".heading").text.strip()
                            if " - " in combined_text:
                                parts = combined_text.split(" - ", 1)
                                if len(parts) == 2:
                                    if not artist:
                                        artist = parts[0].strip()
                                    if not title:
                                        title = parts[1].strip()
                            elif not title:
                                title = combined_text
                        except NoSuchElementException:
                            pass
                    
                    # Only add if we have at least a title
                    if title:
                        results.append(BandcampSearchResult(
                            artist=artist,
                            title=title,
                            url=track_url
                        ))
                        
                except Exception as e:
                    # Skip problematic results
                    continue
                    
        except Exception as e:
            print(f"  ⚠ Error extracting search results: {e}")
            
        return results

    def login(self) -> bool:
        """Login to Bandcamp."""
        print(f"Logging in as {self.username}...")
        self.driver.get(LOGIN_URL)
        time.sleep(2)

        # Find and fill username
        username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username-field")))
        username_field.send_keys(self.username)

        # Find and fill password
        password_field = self.driver.find_element(By.ID, "password-field")
        password_field.send_keys(self.password)

        # Click login button - scroll into view first to avoid footer overlap
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        time.sleep(0.5)

        # Try regular click, fallback to JavaScript click if intercepted
        try:
            login_button.click()
        except:
            self.driver.execute_script("arguments[0].click();", login_button)

        # Wait for login to complete - give it more time in case of slow network or captcha
        print("Waiting for login to complete...")
        time.sleep(5)

        # Verify login by checking for multiple indicators
        # Try multiple methods since Bandcamp's layout can vary
        login_success = False

        try:
            # Method 1: Look for Feed link
            self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Feed")))
            login_success = True
        except TimeoutException:
            try:
                # Method 2: Look for Collection link
                self.driver.find_element(By.LINK_TEXT, "Collection")
                login_success = True
            except NoSuchElementException:
                try:
                    # Method 3: Check if we're no longer on the login page
                    current_url = self.driver.current_url
                    if "login" not in current_url.lower():
                        # Method 4: Look for account menu items
                        try:
                            self.driver.find_element(By.CSS_SELECTOR, "[aria-label*='account' i], [aria-label*='menu' i]")
                            login_success = True
                        except:
                            pass
                except:
                    pass

        if login_success:
            print("✓ Login successful!")
            return True
        else:
            print("✗ Login detection failed")
            print("\nBut you may already be logged in!")
            print("Current URL:", self.driver.current_url)
            print("\nIf you can see you're logged in the browser, press Enter to continue...")
            print("Otherwise, log in manually and then press Enter.")

            # Give user a chance to verify or manually log in
            input()

            # Assume they're logged in now and continue
            print("✓ Proceeding...")
            return True

    def load_progress(self):
        """Load previously processed tracks from progress file."""
        if os.path.exists(self.progress_csv):
            with open(self.progress_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["status"] in ["added", "owned", "already_wishlisted"]:
                        self.processed_ids.add(row["id"])
            print(f"Loaded {len(self.processed_ids)} previously processed tracks")

    def save_progress(self, track_id: str, artist: str, title: str, status: str, url: str = "", notes: str = ""):
        """Append progress to CSV."""
        file_exists = os.path.exists(self.progress_csv)

        with open(self.progress_csv, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["id", "artist", "title", "status", "bandcamp_url", "notes", "timestamp"])

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([track_id, artist, title, status, url, notes, timestamp])

    def search_and_wishlist_track(self, track_id: str, artist: str, title: str):
        """Search for a track and add it to wishlist using intelligent matching."""
        # Skip if already processed
        if track_id in self.processed_ids:
            print(f"⊘ Skipping {artist} - {title} (already processed)")
            return

        print(f"→ Processing: {artist} - {title}")

        # Construct search URL
        query = f"{artist} {title}"
        search_url = f"https://bandcamp.com/search?q={quote_plus(query)}"

        try:
            # Navigate to search
            self.driver.get(search_url)
            time.sleep(1)

            # Dismiss cookie banner if it appears
            self.dismiss_cookies()

            # Extract all search results
            try:
                # Wait for search results to load
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".searchresult"))
                )
                time.sleep(0.5)  # Let results fully load
                
                # Get all search results
                search_results = self._extract_search_results()
                
                if not search_results:
                    print("  ✗ No search results found")
                    self.save_progress(track_id, artist, title, "not_found", "", "No search results")
                    return
                
                print(f"  • Found {len(search_results)} search result(s)")
                
                # Calculate similarity scores and find best match
                best_match = None
                best_similarity = 0.0
                
                for result in search_results:
                    similarity = self._calculate_track_similarity(
                        artist, title,
                        result.artist, result.title
                    )
                    result.confidence = similarity
                    
                    if similarity > best_similarity and similarity >= self.match_threshold:
                        best_similarity = similarity
                        best_match = result
                
                if not best_match:
                    print(f"  ⊘ No good matches found (threshold: {self.match_threshold})")
                    # Show some results for debugging
                    for i, result in enumerate(search_results[:3]):
                        print(f"    [{i+1}] {result.artist} - {result.title} (confidence: {result.confidence:.3f})")
                    self.save_progress(track_id, artist, title, "no_match", "", f"No matches above threshold {self.match_threshold}")
                    return
                
                # Show match info
                print(f"  ✓ Best match: {best_match.artist} - {best_match.title} (confidence: {best_similarity:.3f})")
                
                # Navigate to the best match
                self.driver.get(best_match.url)
                time.sleep(1.5)

                # Ensure the wishlist control is present if available (non-fatal)
                try:
                    self.wait.until(EC.presence_of_element_located((By.ID, "wishlist-msg")))
                except TimeoutException:
                    pass

                # 1) Check if owned (visible UI only)
                if self.is_owned():
                    print("  • Status: OWNED")
                    self.save_progress(track_id, artist, title, "owned", best_match.url, 
                                     f"Already purchased (confidence: {best_similarity:.3f})")
                    self.processed_ids.add(track_id)
                    return

                # 2) Check if already in wishlist
                if self.is_in_wishlist():
                    print("  • Status: Already in wishlist")
                    self.save_progress(track_id, artist, title, "already_wishlisted", best_match.url,
                                     f"Already in wishlist (confidence: {best_similarity:.3f})")
                    self.processed_ids.add(track_id)
                    return

                # 3) Add to wishlist
                try:
                    wishlist_button = self.driver.find_element(By.ID, "wishlist-msg")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wishlist_button)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", wishlist_button)
                    time.sleep(1)

                    # Verify it was added by waiting for 'In Wishlist' to appear in the share panel
                    try:
                        self.wait.until(
                            EC.visibility_of_element_located(
                                (By.XPATH, "//div[contains(@class,'share-panel-wrapper-desktop')]//*[normalize-space(text())='In Wishlist']")
                            )
                        )
                        print("  • Status: Added to wishlist")
                        self.save_progress(track_id, artist, title, "added", best_match.url,
                                         f"Added to wishlist (confidence: {best_similarity:.3f})")
                        self.processed_ids.add(track_id)
                    except TimeoutException:
                        print("  ? Could not verify wishlist addition")
                        self.save_progress(track_id, artist, title, "uncertain", best_match.url, 
                                         f"Click registered but not verified (confidence: {best_similarity:.3f})")

                except NoSuchElementException:
                    print("  ✗ Could not find wishlist button")
                    self.save_progress(track_id, artist, title, "no_wishlist_button", best_match.url, 
                                     f"Wishlist button not found (confidence: {best_similarity:.3f})")

            except TimeoutException:
                print("  ✗ No search results found")
                self.save_progress(track_id, artist, title, "not_found", "", "No search results")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            self.save_progress(track_id, artist, title, "error", "", str(e))

        # Delay between tracks
        time.sleep(self.delay_between_tracks)

    def process_csv(self, input_csv: str):
        """Process all tracks from CSV.

        Args:
            input_csv: Path to the input CSV file with track data
        """
        print(f"\nReading tracks from {input_csv}...")

        tracks = []
        empty_lines_skipped = 0
        with open(input_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty lines (rows where all required fields are empty)
                track_id = (row.get("id") or "").strip()
                artist = (row.get("artist") or "").strip()
                title = (row.get("title") or "").strip()
                
                if not track_id and not artist and not title:
                    empty_lines_skipped += 1
                    continue
                
                # Skip rows with missing required fields
                if not track_id or not artist or not title:
                    print(f"  ⚠ Skipping incomplete row: id={track_id!r}, artist={artist!r}, title={title!r}")
                    continue
                
                tracks.append({"id": track_id, "artist": artist, "title": title})

        if empty_lines_skipped > 0:
            print(f"Skipped {empty_lines_skipped} empty line(s)")
        
        print(f"Found {len(tracks)} tracks to process")
        print(f"Already processed: {len(self.processed_ids)}")
        remaining = len(tracks) - len(self.processed_ids)
        print(f"Remaining: {remaining}\n")

        if remaining == 0:
            print("All tracks already processed!")
            return

        print("=" * 60)

        for i, track in enumerate(tracks, 1):
            if track["id"] in self.processed_ids:
                continue

            print(f"\n[{i}/{len(tracks)}] ", end="")
            self.search_and_wishlist_track(track["id"], track["artist"], track["title"])

        print("\n" + "=" * 60)
        print("✓ Processing complete!")
        print(f"Results saved to: {self.progress_csv}")

    def cleanup(self):
        """Close browser."""
        if self.driver:
            self.driver.quit()
