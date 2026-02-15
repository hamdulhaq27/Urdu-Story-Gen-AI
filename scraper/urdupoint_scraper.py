# UrduPoint Kids Moral Stories Scraper - Selenium Version

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import json
from pathlib import Path
import random
import re


class UrduPointSeleniumScraper:
    def __init__(self, output_dir="raw_stories"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stories = []
        self.scraped_urls = set()
        self.base_url = "https://www.urdupoint.com"
        self.driver = None
        self.last_page = 1
        
        # Load existing stories if any
        self.load_existing_stories()
        self.load_progress()
    
    def load_existing_stories(self):
        #Load previously scraped stories from CSV to continue from where we left off
        csv_file = self.output_dir / "urdupoint_stories.csv"
        
        if not csv_file.exists():
            print("No existing stories found. Starting fresh.")
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.stories.append({
                        'story_id': row['story_id'],
                        'story_title': row['story_title'],
                        'story_text': row['story_text'],
                        'url': row.get('url', '')  
                    })
                    # Track URL to avoid re-scraping
                    if row.get('url'):
                        self.scraped_urls.add(row['url'])
            
            print(f"  Loaded {len(self.stories)} existing stories")
            print(f"  Will continue from story #{len(self.stories) + 1}")
            
        except Exception as e:
            print(f" Error loading existing stories: {e}")
            print("  Starting fresh...")
    
    def load_progress(self):
        # Load the last page number from progress file
        progress_file = self.output_dir / "scraping_progress.json"
        
        if not progress_file.exists():
            return
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                self.last_page = progress.get('last_page', 1)
                print(f" Will resume from page {self.last_page}")
        except Exception as e:
            print(f"Error loading progress: {e}")
    
    def save_progress(self, page_num):
        # Save current page number to progress file
        progress_file = self.output_dir / "scraping_progress.json"
        
        try:
            progress = {
                'last_page': page_num,
                'total_stories': len(self.stories),
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f" Error saving progress: {e}")
    
    def setup_driver(self, headless=False):
        # Setup Chrome driver with options
        print("Setting up Chrome driver...")
        
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        # Make it look like a real browser
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print(" Chrome driver ready")
            return True
        except Exception as e:
            print(f" Failed to setup Chrome driver: {e}")
            print("\nMake sure you have:")
            print("1. Chrome browser installed")
            print("2. ChromeDriver installed (pip install selenium)")
            print("3. ChromeDriver in PATH or same folder")
            return False
    
    def test_connection(self):
        # Test if we can access the website
        print("\nTesting connection to UrduPoint...")
        
        try:
            self.driver.get(f"{self.base_url}/kids/")
            time.sleep(3)
            
            # Check if page loaded
            if "urdupoint" in self.driver.current_url.lower():
                print(" Successfully loaded UrduPoint")
                return True
            else:
                print(" Failed to load UrduPoint")
                return False
                
        except Exception as e:
            print(f" Connection failed: {e}")
            return False
    
    def get_story_links_from_listing(self, page_num=1):
        # Get story links from listing page - URDU VERSION
        
        if page_num == 1:
            url = f"{self.base_url}/kids/category/moral-stories.html?lang=ur"
        else:
            url = f"{self.base_url}/kids/category/moral-stories-page{page_num}.html?lang=ur"
        
        print(f"\nFetching listing page {page_num} (Urdu)...")
        
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find all story links
            story_links = []
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and '/kids/detail/moral-stories/' in href and href.endswith('.html'):
                        # Ensure Urdu language parameter
                        if '?lang=ur' not in href:
                            href += '?lang=ur'
                        if href not in self.scraped_urls:
                            story_links.append(href)
                except:
                    continue
            
            # Remove duplicates
            story_links = list(dict.fromkeys(story_links))
            print(f"   Found {len(story_links)} story links")
            
            return story_links
            
        except Exception as e:
            print(f"   Error: {e}")
            return []
    
    def extract_story_title(self):
        # Extract story title from page
        
        try:
            # Try multiple selectors for title
            title_selectors = [
                (By.TAG_NAME, "h1"),
                (By.CLASS_NAME, "title"),
                (By.CLASS_NAME, "story-title"),
                (By.CLASS_NAME, "heading"),
            ]
            
            for by, value in title_selectors:
                try:
                    element = self.driver.find_element(by, value)
                    title = element.text.strip()
                    if title and len(title) > 3:
                        # Remove date and author info from title
                        title = re.sub(r'تحریر نمبر.*', '', title)
                        title = re.sub(r'\d{1,2}\s+[^\s]+\s+\d{4}', '', title)
                        title = title.strip()
                        if title:
                            return title
                except NoSuchElementException:
                    continue
            
            return "Untitled"
            
        except Exception as e:
            return "Untitled"
    

    
    def extract_story_content(self):
        # Extract complete story - gets page source and extracts all clear_mt divs
        try:
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get the entire page source
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup for better HTML handling
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all divs with class containing 'clear' and 'mt'
            story_divs = []
            for div in soup.find_all('div'):
                div_class = div.get('class', [])
                div_class_str = ' '.join(div_class) if isinstance(div_class, list) else str(div_class)
                
                # Check if it's a story content div
                if 'clear' in div_class_str and 'mt' in div_class_str:
                    story_divs.append(div)
            
            if story_divs:
                # Extract text from all story divs
                story_parts = []
                for div in story_divs:
                    # Get text with line breaks preserved
                    text = div.get_text(separator='\n', strip=False)
                    
                    # Check if it has Urdu content
                    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
                    if urdu_chars > 20:  # Has some Urdu content
                        story_parts.append(text.strip())
                
                if story_parts:
                    # Join all parts
                    full_text = '\n'.join(story_parts)
                    
                    # Minimal cleaning - only remove excessive whitespace
                    lines = []
                    for line in full_text.split('\n'):
                        line = line.strip()
                        if line:  # Keep all non-empty lines
                            lines.append(line)
                    
                    full_text = '\n'.join(lines)
                    
                    # Verify Urdu content
                    urdu_chars = sum(1 for c in full_text if '\u0600' <= c <= '\u06FF')
                    if urdu_chars > 200:
                        return full_text
            
            # Fallback: Try to find main content area
            content_divs = soup.find_all('div', class_=lambda x: x and ('content' in str(x).lower() or 'story' in str(x).lower() or 'detail' in str(x).lower()))
            
            for div in content_divs:
                text = div.get_text(separator='\n', strip=False)
                urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
                
                if urdu_chars > 300 and 1000 < len(text) < 20000:
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    return '\n'.join(lines)
            
            return None
            
        except Exception as e:
            print(f"    Error extracting content: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_story(self, url, story_id):
        """Scrape a single story with title - URDU ONLY"""
        if url in self.scraped_urls:
            return False
        
        print(f"  [{story_id}] Scraping story...")
        
        try:
            # Add language parameter if not present
            if '?lang=ur' not in url:
                url += '?lang=ur'
            
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            # Scroll to ensure content loads
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            # Extract title
            story_title = self.extract_story_title()
            
            # Extract content
            story_text = self.extract_story_content()
            
            if story_text and len(story_text) > 100:
                # Clean the text (no author removal)
                story_text = self.clean_text(story_text)
                
                # Validate it's Urdu content
                urdu_chars = sum(1 for c in story_text if '\u0600' <= c <= '\u06FF')
                total_chars = len(story_text)
                urdu_percentage = (urdu_chars / total_chars * 100) if total_chars > 0 else 0
                
                # Must be at least 60% Urdu characters
                if urdu_chars > 100 and urdu_percentage > 60:
                    self.stories.append({
                        'story_id': story_id,
                        'story_title': story_title,
                        'story_text': story_text,
                        'url': url
                    })
                    self.scraped_urls.add(url)
                    print(f"    ✓ '{story_title[:30]}...' ({len(story_text)} chars)")
                    return True
                else:
                    print(f"    ✗ Not enough Urdu content ({urdu_percentage:.1f}% Urdu)")
                    return False
            else:
                print(f"    ✗ No content found")
                return False
                
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")
            return False
    
    def clean_text(self, text):
        """Clean extracted text - Remove ads and navigation while preserving story"""
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove common English ad/navigation text
        junk_patterns = [
            r'error occurred.*?later',
            r'Please.*?again.*?later',
            r'Advertisement',
            r'Learn more',
            r'unmute',
            r'mute',
            r'Click here',
            r'Read more',
            r'Share',
            r'Facebook',
            r'Twitter',
            r'WhatsApp',
            r'Subscribe',
            r'Follow us',
            r'Sign up',
            r'Login',
            r'Register',
        ]
        
        for pattern in junk_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove Urdu continuation markers and metadata
        urdu_junk_patterns = [
            r'جاری ہے',  # "to be continued"
            r'تحریر نمبر\s*\d+',  # Story number
            r'\d{1,2}\s+(جنوری|فروری|مارچ|اپریل|مئی|جون|جولائی|اگست|ستمبر|اکتوبر|نومبر|دسمبر)\s+\d{4}',  # Dates
            r'جمعرات|پیر|منگل|بدھ|جمعہ|ہفتہ|اتوار',  # Days of week
        ]
        
        for pattern in urdu_junk_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove standalone English words (1-20 chars) but keep Urdu
        # This removes words like "error", "later", etc.
        text = re.sub(r'\b[a-zA-Z]{1,20}\b', '', text)
        
        # Clean up excessive whitespace
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n\n\n+', '\n\n', text)  # Max 2 newlines
        
        # Remove very short lines (likely navigation/ads)
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # Keep lines that have substantial content (more than 10 chars)
            # OR lines that are entirely in Urdu (even if short, like dialogue)
            urdu_chars = sum(1 for c in line if '\u0600' <= c <= '\u06FF')
            if len(line) > 10 or (urdu_chars > 3 and urdu_chars == len(line.replace(' ', '').replace('۔', '').replace('؟', '').replace('!', '').replace('"', '').replace('،', ''))):
                lines.append(line)
        
        text = '\n'.join(lines)
        
        # Remove common duplicate phrases (sometimes pages repeat content)
        # Split by double newline and remove duplicates while preserving order
        paragraphs = text.split('\n\n')
        seen = set()
        unique_paragraphs = []
        for para in paragraphs:
            # Use first 50 chars as key to detect duplicates
            key = para[:50] if len(para) > 50 else para
            if key not in seen:
                seen.add(key)
                unique_paragraphs.append(para)
        
        text = '\n\n'.join(unique_paragraphs)
        
        return text.strip()
    
    def validate_urdu_text(self, text):
        """Validate that text is primarily Urdu"""
        if not text or len(text) < 100:
            return False
        
        urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return False
        
        urdu_percentage = (urdu_chars / total_chars) * 100
        return urdu_percentage > 60  # At least 60% Urdu
    
    def save_to_csv(self, filename="urdupoint_stories.csv"):
        """Save stories to CSV with story_id, story_title, story_text, and url columns"""
        if not self.stories:
            print("\n✗ No stories to save!")
            return
        
        filepath = self.output_dir / filename
        print(f"\nSaving {len(self.stories)} stories to {filepath}...")
        
        # Save CSV with UTF-8 BOM for better Excel compatibility
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['story_id', 'story_title', 'story_text', 'url'])
            writer.writeheader()
            
            for story in self.stories:
                writer.writerow({
                    'story_id': story['story_id'],
                    'story_title': story['story_title'],
                    'story_text': story['story_text'],
                    'url': story.get('url', '')
                })
        
        print(f"✓ CSV saved with UTF-8 encoding (4 columns: story_id, story_title, story_text, url)")
        
        # JSON backup (UTF-8)
        json_file = filepath.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.stories, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON backup saved")
        
        # Also save a plain text file for verification
        txt_file = self.output_dir / "urdupoint_stories.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for story in self.stories:
                f.write(f"{'='*60}\n")
                f.write(f"Story ID: {story['story_id']}\n")
                f.write(f"Title: {story['story_title']}\n")
                f.write(f"{'='*60}\n")
                f.write(f"{story['story_text']}\n\n")
        print(f"✓ Text file saved for verification")
    
    def print_statistics(self):
        """Print statistics with Urdu content analysis"""
        if not self.stories:
            return
        
        total_chars = sum(len(s['story_text']) for s in self.stories)
        avg_length = total_chars // len(self.stories)
        
        # Calculate Urdu content statistics
        total_urdu_chars = sum(
            sum(1 for c in s['story_text'] if '\u0600' <= c <= '\u06FF')
            for s in self.stories
        )
        avg_urdu_percentage = (total_urdu_chars / total_chars * 100) if total_chars > 0 else 0
        
        print("\n" + "="*60)
        print("SCRAPING STATISTICS")
        print("="*60)
        print(f"Total stories scraped: {len(self.stories)}")
        print(f"Total characters: {total_chars:,}")
        print(f"Average story length: {avg_length} characters")
        print(f"Total Urdu characters: {total_urdu_chars:,}")
        print(f"Average Urdu content: {avg_urdu_percentage:.1f}%")
        print("="*60)
    
    def run(self, max_stories=250, headless=False):
        """Main scraping method"""
        print("\n" + "="*60)
        print("URDUPOINT SELENIUM SCRAPER")
        print("="*60)
        print(f"Target: {max_stories} stories")
        print(f"Already scraped: {len(self.stories)} stories")
        print(f"Remaining: {max(0, max_stories - len(self.stories))} stories")
        print(f"Starting from page: {self.last_page}")
        print(f"Mode: {'Headless' if headless else 'Browser visible'}")
        print(f"Auto-save: Every 20 stories")
        print("="*60)
        
        # If we already have enough stories, don't scrape
        if len(self.stories) >= max_stories:
            print(f"\n Already have {len(self.stories)} stories (target: {max_stories})")
            print("No additional scraping needed.")
            self.print_statistics()
            return len(self.stories)
        
        # Setup driver
        if not self.setup_driver(headless=headless):
            return 0
        
        try:
            # Test connection
            if not self.test_connection():
                print("\n Cannot connect to UrduPoint")
                return 0
            
            # Start from where we left off
            story_counter = len(self.stories)
            page_num = self.last_page
            max_pages = 30
            
            while story_counter < max_stories and page_num <= max_pages:
                print(f"\n--- Page {page_num} ---")
                
                story_links = self.get_story_links_from_listing(page_num)
                
                if not story_links:
                    print(f"  No more stories on page {page_num}")
                    break
                
                for link in story_links:
                    if story_counter >= max_stories:
                        break
                    
                    story_id = f"UP_{story_counter + 1:04d}"
                    success = self.scrape_story(link, story_id)
                    
                    if success:
                        story_counter += 1
                        if story_counter % 10 == 0:
                            print(f"\n  Progress: {story_counter}/{max_stories}")
                        
                        # Save after every 20 stories
                        if story_counter % 20 == 0:
                            print(f"\n  💾 Auto-saving at {story_counter} stories...")
                            self.save_to_csv()
                            self.save_progress(page_num)
                
                # Save progress after completing each page
                self.save_progress(page_num + 1)
                
                page_num += 1
                
                if story_counter < max_stories:
                    time.sleep(random.uniform(3, 5))
            
            print("\n" + "="*60)
            print("COMPLETE")
            print("="*60)
            
            if len(self.stories) == 0:
                print("\n Could not scrape any stories")
                return 0
            
            self.save_to_csv()
            self.save_progress(page_num)
            self.print_statistics()
            
            return len(self.stories)
            
        finally:
            
            if self.driver:
                print("\nClosing browser...")
                self.driver.quit()


if(__name__ == "__main__"):
    scraper = UrduPointSeleniumScraper()
    
    count = scraper.run(max_stories=250, headless=True)
    
    if(count > 0):
        print(f"\n Successfully scraped {count} stories!")
    
    else:
        print("\n Scraping failed.")