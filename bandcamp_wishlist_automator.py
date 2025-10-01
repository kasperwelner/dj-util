#!/usr/bin/env python3
"""
Bandcamp Wishlist Automator
Automatically adds tracks from a CSV to your Bandcamp wishlist
"""

import csv
import time
import sys
import os
import getpass
from urllib.parse import quote_plus
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
INPUT_CSV = "Hard Groove.csv"
PROGRESS_CSV = "bandcamp_wishlist_progress.csv"
DELAY_BETWEEN_TRACKS = 2  # seconds between searches
LOGIN_URL = "https://bandcamp.com/login"

class BandcampWishlistAutomator:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.processed_ids = set()
        
    def is_owned(self):
        """Return True if the visible page shows that the user owns the track"""
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
        
    def is_in_wishlist(self):
        """Return True if the visible page shows 'In Wishlist' in the share panel area"""
        if not self.driver:
            return False
        try:
            el = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'share-panel-wrapper-desktop')]//*[normalize-space(text())='In Wishlist']"
            )
            return el.is_displayed()
        except NoSuchElementException:
            return False
        
    def setup_driver(self):
        """Initialize Chrome driver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
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
        """Dismiss cookie consent banner if present"""
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
                "button[class*='accept' i]"
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
    
    def login(self):
        """Login to Bandcamp"""
        print(f"Logging in as {self.username}...")
        self.driver.get(LOGIN_URL)
        time.sleep(2)
        
        # Find and fill username
        username_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "username-field"))
        )
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
            self.wait.until(
                EC.presence_of_element_located((By.LINK_TEXT, "Feed"))
            )
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
        """Load previously processed tracks from progress file"""
        if os.path.exists(PROGRESS_CSV):
            with open(PROGRESS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] in ['added', 'owned', 'already_wishlisted']:
                        self.processed_ids.add(row['id'])
            print(f"Loaded {len(self.processed_ids)} previously processed tracks")
    
    def save_progress(self, track_id, artist, title, status, url="", notes=""):
        """Append progress to CSV"""
        file_exists = os.path.exists(PROGRESS_CSV)
        
        with open(PROGRESS_CSV, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['id', 'artist', 'title', 'status', 'bandcamp_url', 'notes', 'timestamp'])
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([track_id, artist, title, status, url, notes, timestamp])
    
    def search_and_wishlist_track(self, track_id, artist, title):
        """Search for a track and add it to wishlist"""
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
            
            # Look for track results
            try:
                # Find the first TRACK result - look for track link specifically
                track_link = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".searchresult[data-search] a.artcont, .searchresult a.artcont"))
                )
                track_url = track_link.get_attribute('href')
                
                # Scroll into view to avoid menu bar overlap
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", track_link)
                time.sleep(0.5)
                
                # Click to go to track page - try regular click, fallback to JavaScript click
                try:
                    track_link.click()
                except:
                    self.driver.execute_script("arguments[0].click();", track_link)
                time.sleep(1.5)
                
                # Ensure the wishlist control is present if available (non-fatal)
                try:
                    self.wait.until(EC.presence_of_element_located((By.ID, "wishlist-msg")))
                except TimeoutException:
                    pass
                
                # 1) Check if owned (visible UI only)
                if self.is_owned():
                    print("  • Status: OWNED")
                    self.save_progress(track_id, artist, title, 'owned', track_url, 'Already purchased')
                    self.processed_ids.add(track_id)
                    return
                
                # 2) Check if already in wishlist
                if self.is_in_wishlist():
                    print("  • Status: Already in wishlist")
                    self.save_progress(track_id, artist, title, 'already_wishlisted', track_url)
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
                        self.save_progress(track_id, artist, title, 'added', track_url)
                        self.processed_ids.add(track_id)
                    except TimeoutException:
                        print("  ? Could not verify wishlist addition")
                        self.save_progress(track_id, artist, title, 'uncertain', track_url, 'Click registered but not verified')
                        
                except NoSuchElementException:
                    print("  ✗ Could not find wishlist button")
                    self.save_progress(track_id, artist, title, 'no_wishlist_button', track_url, 'Wishlist button not found')
                    
            except TimeoutException:
                print(f"  ✗ No search results found")
                self.save_progress(track_id, artist, title, 'not_found', '', 'No search results')
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            self.save_progress(track_id, artist, title, 'error', '', str(e))
        
        # Delay between tracks
        time.sleep(DELAY_BETWEEN_TRACKS)
    
    def process_csv(self):
        """Process all tracks from CSV"""
        print(f"\nReading tracks from {INPUT_CSV}...")
        
        tracks = []
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracks.append({
                    'id': row['id'],
                    'artist': row['artist'],
                    'title': row['title']
                })
        
        print(f"Found {len(tracks)} tracks to process")
        print(f"Already processed: {len(self.processed_ids)}")
        remaining = len(tracks) - len(self.processed_ids)
        print(f"Remaining: {remaining}\n")
        
        if remaining == 0:
            print("All tracks already processed!")
            return
        
        print("=" * 60)
        
        for i, track in enumerate(tracks, 1):
            if track['id'] in self.processed_ids:
                continue
                
            print(f"\n[{i}/{len(tracks)}] ", end="")
            self.search_and_wishlist_track(track['id'], track['artist'], track['title'])
        
        print("\n" + "=" * 60)
        print(f"✓ Processing complete!")
        print(f"Results saved to: {PROGRESS_CSV}")
    
    def cleanup(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

def main():
    """Main execution"""
    print("=" * 60)
    print("Bandcamp Wishlist Automator")
    print("=" * 60)
    
    # Get credentials
    username = input("Bandcamp username or email: ").strip()
    password = getpass.getpass("Bandcamp password: ").strip()
    
    if not username or not password:
        print("Error: Username and password required")
        sys.exit(1)
    
    # Initialize automator
    automator = BandcampWishlistAutomator(username, password)
    
    try:
        # Load previous progress
        automator.load_progress()
        
        # Setup browser
        print("\nInitializing browser...")
        automator.setup_driver()
        
        # Login
        if not automator.login():
            print("Failed to login. Please check your credentials.")
            sys.exit(1)
        
        # Process tracks
        automator.process_csv()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        print(f"Progress has been saved to {PROGRESS_CSV}")
        print("Run the script again to resume from where you left off.")
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        automator.cleanup()
        print("\nBrowser closed.")

if __name__ == "__main__":
    main()
