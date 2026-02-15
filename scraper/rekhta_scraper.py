# Rekhta Children's Stories Scraper - Selenium Version


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


class RekhtaSeleniumScraper:
    def __init__(self, output_dir="rekhta_stories"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.stories = []
        self.scraped_urls = set()
        self.base_url = "https://www.rekhta.org"
        self.driver = None
        self.last_page = 1  # Track last scraped page
        
        # Load existing stories if any
        self.load_existing_stories()
        self.load_progress()
    
    def load_existing_stories(self):
        """Load previously scraped stories from CSV to continue from where we left off"""
        csv_file = self.output_dir / "rekhta_stories.csv"
        
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
            
            print(f"✓ Loaded {len(self.stories)} existing stories")
            print(f"  Will continue from story #{len(self.stories) + 1}")
            
        except Exception as e:
            print(f"⚠ Error loading existing stories: {e}")
            print("  Starting fresh...")
    
    def load_progress(self):
        """Load the last page number from progress file"""
        progress_file = self.output_dir / "scraping_progress.json"
        
        if not progress_file.exists():
            return
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                self.last_page = progress.get('last_page', 1)
                print(f"✓ Will resume from page {self.last_page}")
        except Exception as e:
            print(f"⚠ Error loading progress: {e}")
    
    def save_progress(self, page_num):
        """Save current page number to progress file"""
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
            print(f"⚠ Error saving progress: {e}")
    
    def setup_driver(self, headless=False):
        """Setup Chrome driver with options"""
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
            print("✓ Chrome driver ready")
            return True
        except Exception as e:
            print(f"✗ Failed to setup Chrome driver: {e}")
            print("\nMake sure you have:")
            print("1. Chrome browser installed")
            print("2. ChromeDriver installed (pip install selenium)")
            print("3. ChromeDriver in PATH or same folder")
            return False
    
    def test_connection(self):
        """Test if we can access the website"""
        print("\nTesting connection to Rekhta...")
        
        try:
            self.driver.get(f"{self.base_url}/children-s-stories?lang=ur")
            time.sleep(3)
            
            # Check if page loaded
            if "rekhta" in self.driver.current_url.lower():
                print("✓ Successfully loaded Rekhta")
                return True
            else:
                print("✗ Failed to load Rekhta")
                return False
                
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def get_author_links_from_listing(self, page_num=1):
        """Get author links from listing page"""
        alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                   'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        
        if page_num <= len(alphabet):
            letter = alphabet[page_num - 1]
            url = f"https://www.rekhta.org/children-s-stories?startswith={letter}&lang=ur"
        else:
            url = f"https://www.rekhta.org/children-s-stories/{page_num - len(alphabet)}?lang=ur"
        
        print(f"\nFetching author listing page {page_num} (letter: {alphabet[page_num-1] if page_num <= 26 else 'N/A'})...")
        
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            author_links = []
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link['href']
                # Author pages: /authors/name/children-s-stories or /poets/name/children-s-stories
                if ('/authors/' in href or '/poets/' in href) and '/children-s-stories' in href:
                    full_url = href if href.startswith('http') else self.base_url + href
                    if '?lang=ur' not in full_url:
                        full_url += '?lang=ur' if '?' not in full_url else '&lang=ur'
                    author_links.append(full_url)
            
            author_links = list(dict.fromkeys(author_links))
            print(f"  ✓ Found {len(author_links)} author pages")
            return author_links
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return []
    
    def get_story_links_from_author_page(self, author_url):
        """Get individual story links from an author's page"""
        try:
            # Extract author name from URL
            # URL format: /authors/aagha-ashraf/children-s-stories
            author_slug = author_url.split('/')[-2]  # Get the author slug
            author_name = author_slug.replace('-', ' ').title()
            
            self.driver.get(author_url)
            time.sleep(random.uniform(2, 4))
            
            # Scroll to load all stories
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            story_links = []
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link['href']
                # Individual story URLs contain the story slug and end with -children-s-stories
                if 'children-s-stories' in href and href.count('-') >= 3:
                    # Must not be an author/poet page
                    if '/authors/' not in href and '/poets/' not in href:
                        # Must not be a filter page
                        if 'startswith=' not in href:
                            full_url = href if href.startswith('http') else self.base_url + href
                            if '?lang=ur' not in full_url:
                                full_url += '?lang=ur' if '?' not in full_url else '&lang=ur'
                            
                            if full_url not in self.scraped_urls:
                                # Store as tuple: (url, author_name)
                                story_links.append((full_url, author_name))
            
            # Remove duplicates while keeping author name
            seen = set()
            unique_links = []
            for url, author in story_links:
                if url not in seen:
                    seen.add(url)
                    unique_links.append((url, author))
            
            return unique_links
            
        except Exception as e:
            print(f"    Error getting stories from author: {e}")
            return []
    
    def extract_story_title(self, url="", author_name=""):
        """Extract story title from URL (English) and remove author name"""
        try:
            # Extract title from URL slug
            # URL format: /story-name-author-name-children-s-stories
            # Example: /tinku-aagha-ashraf-children-s-stories
            
            if url:
                # Get the last part of URL (the slug)
                slug = url.split('/')[-1].split('?')[0]  # Remove query params
                
                # Remove the -children-s-stories suffix
                if slug.endswith('-children-s-stories'):
                    slug = slug[:-len('-children-s-stories')]
                
                # Convert dashes to spaces and title case
                title = slug.replace('-', ' ').title()
                
                # Remove author name from title if provided
                if author_name and author_name in title:
                    # Remove the author name and clean up extra spaces
                    title = title.replace(author_name, '').strip()
                    # Remove trailing/leading spaces and dashes
                    title = re.sub(r'\s+', ' ', title).strip()
                
                if title and len(title) > 3:
                    return title
            
            # Fallback: try to get from page if URL method fails
            time.sleep(1)
            
            title_selectors = [
                (By.CSS_SELECTOR, "h1.hdg"),
                (By.CSS_SELECTOR, ".contentHeading h1"),
                (By.TAG_NAME, "h1"),
            ]
            
            for by, value in title_selectors:
                try:
                    element = self.driver.find_element(by, value)
                    title = element.text.strip()
                    if title and len(title) > 3:
                        return title
                except NoSuchElementException:
                    continue
            
            return "Untitled"
            
        except Exception as e:
            return "Untitled"
    
    def extract_story_content(self):
        """Extract complete story content from page"""
        try:
            # Wait for page to load completely
            time.sleep(2)
            
            # Scroll to load all lazy-loaded content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get the entire page source
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            story_text = []
            
            # Find the main content container: div.pMC
            pmc_div = soup.find('div', class_=lambda x: x and 'pMC' in str(x))
            
            if pmc_div:
                print(f"    Found pMC div (main content)")
                
                # Find all paragraph containers: div.w with data-p attribute
                paragraph_divs = pmc_div.find_all('div', class_='w', attrs={'data-p': True})
                print(f"    Found {len(paragraph_divs)} paragraph divs (data-p)")
                
                for para_div in paragraph_divs:
                    # Get paragraph number
                    para_num = para_div.get('data-p', '')
                    
                    # Find the content div: div.c
                    content_div = para_div.find('div', class_='c')
                    
                    if content_div:
                        # Find all line paragraphs: p with data-l attribute
                        lines = content_div.find_all('p', attrs={'data-l': True})
                        
                        for line in lines:
                            # Extract all span text
                            spans = line.find_all('span')
                            line_text = []
                            
                            for span in spans:
                                # Get the visible text (not the data-m attribute)
                                text = span.get_text(strip=True)
                                if text:
                                    # Check if it's Urdu
                                    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
                                    if urdu_chars > 0:  # Has Urdu content
                                        line_text.append(text)
                            
                            if line_text:
                                # Join spans in this line with space
                                full_line = ' '.join(line_text)
                                story_text.append(full_line)
                
                if story_text:
                    # Join all lines with newlines
                    full_text = '\n'.join(story_text)
                    
                    # Clean up multiple spaces
                    full_text = re.sub(r' +', ' ', full_text)
                    
                    # Verify Urdu content
                    urdu_chars = sum(1 for c in full_text if '\u0600' <= c <= '\u06FF')
                    total_chars = len(full_text)
                    
                    print(f"    Extracted: {len(full_text)} chars, {urdu_chars} Urdu chars ({len(story_text)} lines)")
                    
                    if urdu_chars > 200:
                        return full_text
                    else:
                        print(f"    Not enough Urdu content")
            else:
                print(f"    No pMC div found")
            
            # Fallback: try to find any content with Urdu
            print(f"    Trying fallback extraction...")
            all_spans = soup.find_all('span')
            fallback_text = []
            
            for span in all_spans:
                text = span.get_text(strip=True)
                if text and len(text) > 3:
                    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
                    if urdu_chars > 3:
                        fallback_text.append(text)
            
            if fallback_text and len(fallback_text) > 10:
                full_text = ' '.join(fallback_text)
                urdu_chars = sum(1 for c in full_text if '\u0600' <= c <= '\u06FF')
                
                if urdu_chars > 200:
                    print(f"    Fallback succeeded: {len(full_text)} chars, {urdu_chars} Urdu chars")
                    return full_text
            
            print(f"    No valid content found")
            return None
            
        except Exception as e:
            print(f"    Error extracting content: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_story(self, url, story_id, author_name=""):
        """Scrape a single story - URDU ONLY"""
        if url in self.scraped_urls:
            return False
        
        print(f"  [{story_id}] Scraping story...")
        
        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            # Scroll to ensure content loads
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            # Extract title from URL (English) and remove author name
            story_title = self.extract_story_title(url, author_name)
            
            # Extract content
            story_text = self.extract_story_content()
            
            if story_text and len(story_text) > 100:
                # Clean the text
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
                    print(f"    ✓ '{story_title[:40]}...' ({len(story_text)} chars)")
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
            r'More Stories',
            r'Related Stories',
            r'Recommended',
        ]
        
        for pattern in junk_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove Rekhta-specific navigation elements
        rekhta_junk = [
            r'Rekhta Dictionary',
            r'Audio/Video',
            r'Play Audio',
            r'Download',
            r'Meaning in English',
        ]
        
        for pattern in rekhta_junk:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove standalone English words (1-20 chars) but keep Urdu
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
        
        # Remove common duplicate phrases
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
    
    def save_to_csv(self, filename="rekhta_stories.csv"):
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
        txt_file = self.output_dir / "rekhta_stories.txt"
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
        print("REKHTA SELENIUM SCRAPER")
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
            print(f"\n✓ Already have {len(self.stories)} stories (target: {max_stories})")
            print("No additional scraping needed.")
            self.print_statistics()
            return len(self.stories)
        
        # Setup driver
        if not self.setup_driver(headless=headless):
            return 0
        
        try:
            # Test connection
            if not self.test_connection():
                print("\n✗ Cannot connect to Rekhta")
                return 0
            
            # Start from where we left off
            story_counter = len(self.stories)
            page_num = self.last_page
            max_pages = 26  # 26 letters of alphabet
            
            while story_counter < max_stories and page_num <= max_pages:
                print(f"\n--- Page {page_num} ---")
                
                # Step 1: Get author links from this alphabet page
                author_links = self.get_author_links_from_listing(page_num)
                
                if not author_links:
                    print(f"  No authors found on page {page_num}")
                    page_num += 1
                    continue
                
                # Step 2: Visit each author and get their stories
                for author_url in author_links:
                    if story_counter >= max_stories:
                        break
                    
                    print(f"\n  Checking author: {author_url.split('/')[-2]}")
                    story_links = self.get_story_links_from_author_page(author_url)
                    print(f"    Found {len(story_links)} stories by this author")
                    
                    # Step 3: Scrape each story
                    for link_tuple in story_links:
                        if story_counter >= max_stories:
                            break
                        
                        # Unpack tuple: (url, author_name)
                        link, author_name = link_tuple
                        
                        story_id = f"RK_{story_counter + 1:04d}"
                        success = self.scrape_story(link, story_id, author_name)
                        
                        if success:
                            story_counter += 1
                            if story_counter % 10 == 0:
                                print(f"\n  Progress: {story_counter}/{max_stories}")
                            
                            # Save after every 20 stories
                            if story_counter % 20 == 0:
                                print(f"\n  💾 Auto-saving at {story_counter} stories...")
                                self.save_to_csv()
                                self.save_progress(page_num)
                    
                    time.sleep(random.uniform(1, 2))  # Small delay between authors
                
                # Save progress after completing each page
                self.save_progress(page_num + 1)
                
                page_num += 1
                
                if story_counter < max_stories:
                    time.sleep(random.uniform(2, 4))
            
            print("\n" + "="*60)
            print("COMPLETE")
            print("="*60)
            
            if len(self.stories) == 0:
                print("\n✗ Could not scrape any stories")
                return 0
            
            self.save_to_csv()
            self.save_progress(page_num)
            self.print_statistics()
            
            return len(self.stories)
            
        finally:
            # Always close the driver
            if self.driver:
                print("\nClosing browser...")
                self.driver.quit()


if __name__ == "__main__":
    scraper = RekhtaSeleniumScraper()
    
    count = scraper.run(max_stories=250, headless=True)
    
    if count > 0:
        print(f"\nSuccessfully scraped {count} stories!")
    
    else:
        print("\nScraping failed.")