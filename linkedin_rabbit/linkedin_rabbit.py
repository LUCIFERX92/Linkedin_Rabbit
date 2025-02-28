#!/usr/bin/env python3
"""
LinkedIn Rabbit - LinkedIn Post Scraper

This module provides functions to extract posts from LinkedIn profiles.
It includes features to avoid detection, handle rate limiting, and ensure reliable scraping.

Made by Tensor Boy
"""

import os
import time
import re
import random
import hashlib
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# Constants
MIN_SCROLL_DELAY = 2.5
MAX_SCROLL_DELAY = 5.0
MIN_ACTION_DELAY = 0.5
MAX_ACTION_DELAY = 1.5

def random_delay(min_seconds=MIN_ACTION_DELAY, max_seconds=MAX_ACTION_DELAY):
    """Add a random delay to avoid detection."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

def setup_driver(headless=False):
    """Initialize and configure the Chrome WebDriver with anti-detection measures."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Basic options
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    
    # Anti-detection measures
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Add a user agent to appear more like a real browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Updated ChromeDriverManager setup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional anti-detection measures
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def login_to_linkedin(driver, username, password):
    """Log in to LinkedIn with the provided credentials."""
    print("Logging in to LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    
    # Add a random delay before login
    random_delay(2.0, 4.0)
    
    try:
        # Wait for the login page to load and enter credentials
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        # Type username with random delays between keystrokes
        username_field = driver.find_element(By.ID, "username")
        for char in username:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        random_delay(0.5, 1.5)
        
        # Type password with random delays between keystrokes
        password_field = driver.find_element(By.ID, "password")
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        random_delay(0.5, 1.5)
        
        # Click the login button
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for login to complete
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "global-nav"))
        )
        
        print("Successfully logged in to LinkedIn")
        
        # Add a longer delay after login to avoid suspicion
        random_delay(3.0, 5.0)
        
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def get_posts_url(profile_url):
    """Convert a profile URL to the posts/activity URL."""
    # Clean up the URL
    if profile_url.endswith('/'):
        profile_url = profile_url[:-1]
    
    # Check if it's a company page or personal profile
    if '/company/' in profile_url:
        return f"{profile_url}/posts"
    else:
        # Extract username from URL
        username = profile_url.split('/')[-1]
        return f"https://www.linkedin.com/in/{username}/recent-activity/all/"

def expand_see_more_buttons(driver):
    """Find and click all 'see more' buttons in the page."""
    try:
        see_more_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'see more')]")
        for button in see_more_buttons:
            try:
                # Scroll to the button
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                random_delay(0.3, 0.7)
                
                # Click the button
                driver.execute_script("arguments[0].click();", button)
                random_delay(0.5, 1.0)
            except:
                pass
        return True
    except Exception as e:
        print(f"Error expanding 'see more' buttons: {e}")
        return False

def scroll_to_load_posts(driver, num_posts, start_from=0, max_attempts=40):
    """Scroll down the page to load the specified number of posts."""
    print(f"Scrolling to load at least {num_posts} posts (starting after post #{start_from})...")
    
    posts = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    no_change_count = 0
    max_no_change = 5  # Stop after 5 scrolls with no new content
    attempts = 0
    
    # We load more posts than needed to account for filtering and duplicates
    target_posts = num_posts * 4
    
    # Create a progress bar
    pbar = tqdm(total=target_posts, desc="Loading posts")
    
    # If we're starting from a non-zero position, we need to scroll down to load previous posts first
    if start_from > 0:
        print(f"Scrolling to load the first {start_from} posts (to skip them)...")
        initial_scroll_count = min(start_from // 5, 20)  # Estimate how many scrolls needed
        
        # Initial rapid scrolling to get past the already processed posts
        for _ in range(initial_scroll_count):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_delay(1.0, 2.0)
            
            # Expand any "see more" buttons to ensure all content is loaded
            expand_see_more_buttons(driver)
            
            # Get current posts to check progress
            if '/company/' in driver.current_url:
                current_posts = driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")
            else:
                current_posts = driver.find_elements(By.CSS_SELECTOR, "div.occludable-update, div.feed-shared-update-v2")
            
            # If we've loaded enough posts to skip, break early
            if len(current_posts) >= start_from * 1.5:  # Load extra to account for filtering
                print(f"Loaded {len(current_posts)} posts during initial scrolling")
                break
    
    while len(posts) < target_posts and no_change_count < max_no_change and attempts < max_attempts:
        # Scroll down with a smooth, human-like behavior
        driver.execute_script("""
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        """)
        
        # Random delay between scrolls to mimic human behavior
        scroll_delay = random_delay(MIN_SCROLL_DELAY, MAX_SCROLL_DELAY)
        
        # Expand any "see more" buttons
        expand_see_more_buttons(driver)
        
        # Get new scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Find all posts
        if '/company/' in driver.current_url:
            # Company page posts
            posts = driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")
        else:
            # Personal profile posts - try different selectors
            posts = driver.find_elements(By.CSS_SELECTOR, "div.occludable-update, div.feed-shared-update-v2")
        
        # Update progress bar
        pbar.n = min(len(posts), target_posts)
        pbar.refresh()
        
        # Check if the page height has changed
        if new_height == last_height:
            no_change_count += 1
            
            # If we're stuck, try a different scroll approach
            if no_change_count >= 3:
                # Try a random scroll position to trigger more content loading
                random_scroll = random.uniform(0.5, 0.9) * last_height
                driver.execute_script(f"window.scrollTo(0, {random_scroll});")
                random_delay(1.0, 2.0)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                random_delay(1.0, 2.0)
        else:
            no_change_count = 0
            
        last_height = new_height
        attempts += 1
        
        # Add some randomness to the scrolling behavior
        if random.random() < 0.2:  # 20% chance
            # Scroll up a bit and then back down to mimic human behavior
            up_scroll = random.uniform(0.7, 0.9) * last_height
            driver.execute_script(f"window.scrollTo(0, {up_scroll});")
            random_delay(1.0, 2.0)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_delay(1.0, 2.0)
    
    pbar.close()
    
    # If we're starting from a non-zero position, we need to skip the first 'start_from' posts
    if start_from > 0 and len(posts) > start_from:
        print(f"Skipping the first {start_from} posts that were already processed")
        posts = posts[start_from:]
    
    print(f"Found {len(posts)} posts after scrolling (after skipping {start_from} posts)")
    
    return posts

def is_reposted_content(post):
    """Check if the post is reposted content."""
    try:
        repost_indicators = post.find_elements(By.CSS_SELECTOR, "li-icon[type='repost-filled']")
        if repost_indicators:
            return True
            
        repost_text = post.find_elements(By.XPATH, ".//*[contains(text(), 'reposted') or contains(text(), 'shared')]")
        if repost_text:
            return True
            
        return False
    except:
        return False

def extract_post_content(post):
    """Extract the text content from a post element."""
    try:
        # Check if this is a reposted content
        if is_reposted_content(post):
            return "[Reposted content - skipped]"
        
        # Try different selectors for post content
        selectors = [
            ".feed-shared-update-v2__description-wrapper",
            ".feed-shared-text",
            ".feed-shared-text__text-view",
            ".break-words",
            ".update-components-text",
            ".feed-shared-update-v2__description",
            ".feed-shared-inline-show-more-text",
            ".feed-shared-text-view"
        ]
        
        for selector in selectors:
            elements = post.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].text.strip():
                return elements[0].text.strip()
        
        # If no specific content found, get all text from the post
        all_text = post.text.strip()
        if all_text:
            # Try to clean up the text by removing common headers
            lines = all_text.split('\n')
            cleaned_lines = []
            skip_next = False
            
            for i, line in enumerate(lines):
                if skip_next:
                    skip_next = False
                    continue
                    
                # Skip lines that are likely headers or metadata
                if any(x in line.lower() for x in ["likes", "comments", "repost", "shared", "following"]):
                    continue
                    
                # Skip date lines (often short and contain time indicators)
                if len(line) < 30 and any(x in line.lower() for x in ["min", "hour", "day", "week", "month", "year"]):
                    continue
                    
                cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
        
        return "[No text content found]"
    except Exception as e:
        print(f"Error extracting post content: {e}")
        return "[Error extracting post content]"

def extract_post_date(post):
    """Extract the date from a post element."""
    try:
        date_selectors = [
            ".feed-shared-actor__sub-description",
            ".feed-shared-actor__sub-description span",
            ".ml4.mt2.text-body-xsmall.t-black--light",
            ".visually-hidden"
        ]
        
        for selector in date_selectors:
            elements = post.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].text.strip():
                date_text = elements[0].text.strip()
                # Clean up the date text (remove any "• Edited" or similar)
                if "•" in date_text:
                    date_text = date_text.split("•")[0].strip()
                return date_text
        
        return "Unknown date"
    except Exception as e:
        print(f"Error extracting post date: {e}")
        return "Unknown date"

def extract_engagement_stats(post):
    """Extract engagement statistics (likes, comments, shares) from a post."""
    try:
        stats = {"likes": "0", "comments": "0", "shares": "0"}
        
        # Try to find likes
        like_selectors = [
            ".social-details-social-counts__reactions-count",
            ".social-details-social-counts__count-value"
        ]
        for selector in like_selectors:
            elements = post.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].text.strip():
                stats["likes"] = elements[0].text.strip()
                break
                
        # Try to find comments
        comment_selectors = [
            ".social-details-social-counts__comments-count",
            ".social-details-social-counts__comments span"
        ]
        for selector in comment_selectors:
            elements = post.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].text.strip():
                stats["comments"] = elements[0].text.strip()
                break
                
        # Try to find shares
        share_selectors = [
            ".social-details-social-counts__shares-count"
        ]
        for selector in share_selectors:
            elements = post.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].text.strip():
                stats["shares"] = elements[0].text.strip()
                break
        
        # Alternative approach - look for the social activity section
        if stats["likes"] == "0" and stats["comments"] == "0" and stats["shares"] == "0":
            social_text = post.text.lower()
            
            # Parse the text for numbers
            if "like" in social_text:
                likes_match = re.search(r'(\d+)\s+like', social_text)
                if likes_match:
                    stats["likes"] = likes_match.group(1)
            
            if "comment" in social_text:
                comments_match = re.search(r'(\d+)\s+comment', social_text)
                if comments_match:
                    stats["comments"] = comments_match.group(1)
            
            if "share" in social_text:
                shares_match = re.search(r'(\d+)\s+share', social_text)
                if shares_match:
                    stats["shares"] = shares_match.group(1)
        
        return stats
    except Exception as e:
        print(f"Error extracting engagement stats: {e}")
        return {"likes": "0", "comments": "0", "shares": "0"}

def get_profile_name(driver, profile_url):
    """Extract the profile name from the page."""
    try:
        if '/company/' in profile_url:
            # For company pages
            try:
                name_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.org-top-card-summary__title"))
                )
                return name_element.text.strip()
            except:
                # Extract from URL if element not found
                company_name = profile_url.split('/')[-1]
                return company_name.replace('-', ' ').title()
        else:
            # For personal profiles
            try:
                # Try multiple selectors for the name
                selectors = [
                    "h1.text-heading-xlarge",
                    "h1.inline.t-24.t-black.t-normal.break-words",
                    "h1.top-card-layout__title",
                    ".feed-identity-module__actor-meta a"
                ]
                
                for selector in selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].text.strip():
                        return elements[0].text.strip()
                
                # If still not found, try to get from URL
                username = profile_url.split('/')[-1]
                if username:
                    return username.replace('-', ' ').title()
                else:
                    # Fallback to a default name
                    return "LinkedIn_User"
            except Exception as e:
                print(f"Error getting profile name: {e}")
                # Extract from URL if element not found
                username = profile_url.split('/')[-1]
                return username.replace('-', ' ').title() if username else "LinkedIn_User"
    except Exception as e:
        print(f"Error in get_profile_name: {e}")
        # Final fallback
        return "LinkedIn_User"

def save_posts_to_file(posts_data, profile_name):
    """Save the extracted posts to a text file."""
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure we have a valid profile name
    if not profile_name or profile_name.strip() == "":
        profile_name = "LinkedIn_User"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{profile_name}_linkedin_posts_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(f"LinkedIn Posts for: {profile_name}\n")
            f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Number of posts: {len(posts_data)}\n")
            f.write("=" * 80 + "\n\n")
            
            for idx, post in enumerate(posts_data, 1):
                f.write(f"Post #{idx}\n")
                f.write(f"Date: {post['date']}\n")
                
                # Format engagement data
                engagement = post['engagement']
                engagement_str = f"{engagement.get('likes', '0')} likes, {engagement.get('comments', '0')} comments, {engagement.get('shares', '0')} shares"
                f.write(f"Engagement: {engagement_str}\n\n")
                
                # Write content - handle any potential encoding issues
                content = post['content']
                # Replace any problematic characters
                content = ''.join(char if ord(char) < 65536 else '?' for char in content)
                f.write(content + "\n")
                f.write("\n" + "-" * 80 + "\n\n")
        
        print(f"Posts saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving posts to file: {e}")
        # Try with a more basic encoding as fallback
        try:
            with open(filepath, 'w', encoding='ascii', errors='replace') as f:
                f.write(f"LinkedIn Posts for: {profile_name}\n")
                f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Number of posts: {len(posts_data)}\n")
                f.write("=" * 80 + "\n\n")
                
                for idx, post in enumerate(posts_data, 1):
                    f.write(f"Post #{idx}\n")
                    f.write(f"Date: {post['date']}\n")
                    
                    # Format engagement data
                    engagement = post['engagement']
                    engagement_str = f"{engagement.get('likes', '0')} likes, {engagement.get('comments', '0')} comments, {engagement.get('shares', '0')} shares"
                    f.write(f"Engagement: {engagement_str}\n\n")
                    
                    # Write content with replacement for non-ASCII characters
                    f.write(post['content'] + "\n")
                    f.write("\n" + "-" * 80 + "\n\n")
            
            print(f"Posts saved to {filepath} with fallback encoding")
            return filepath
        except Exception as e2:
            print(f"Error saving posts with fallback encoding: {e2}")
            return None

def generate_content_hash(content):
    """Generate a hash of the content to identify duplicates."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def expand_post_see_more(driver, post):
    """Expand 'see more' buttons in a specific post."""
    try:
        # Find all "see more" buttons in this post
        see_more_buttons = post.find_elements(By.CSS_SELECTOR, "button.feed-shared-inline-show-more-text__button")
        for button in see_more_buttons:
            try:
                if "see more" in button.text.lower():
                    # Scroll to the button
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                    random_delay(0.3, 0.7)
                    
                    # Click the button
                    driver.execute_script("arguments[0].click();", button)
                    random_delay(0.5, 1.0)
            except (StaleElementReferenceException, Exception) as e:
                print(f"Error clicking 'see more' button: {e}")
                continue
        return True
    except Exception as e:
        print(f"Error expanding post 'see more' buttons: {e}")
        return False

def scrape_linkedin_posts(profile_url, num_posts, username, password, headless=False, start_from=0, batch_size=30):
    """Main function to scrape LinkedIn posts."""
    driver = None
    try:
        # Set up the driver
        driver = setup_driver(headless)
        
        # Login to LinkedIn
        if not login_to_linkedin(driver, username, password):
            return None
        
        # Navigate to the posts page
        posts_url = get_posts_url(profile_url)
        driver.get(posts_url)
        print(f"Navigating to {posts_url}")
        
        # Add a random delay after navigation
        random_delay(3.0, 5.0)
        
        # Get the profile name
        profile_name = get_profile_name(driver, profile_url)
        print(f"Scraping posts for: {profile_name}")
        
        # Determine how many posts to scrape in this batch
        posts_to_scrape = min(batch_size, num_posts - start_from)
        
        # Load posts by scrolling - load more than needed to account for filtering
        all_posts = scroll_to_load_posts(driver, posts_to_scrape, start_from=start_from)
        
        if not all_posts:
            print("No posts found. Check the profile URL and try again.")
            return None
            
        # Extract data from each post
        posts_data = []
        valid_posts_count = 0
        content_hashes = set()  # To track duplicate content
        
        print(f"Processing {len(all_posts)} posts to find {posts_to_scrape} valid ones...")
        
        # Create a progress bar for processing posts
        with tqdm(total=posts_to_scrape, desc="Processing posts") as pbar:
            for post in all_posts:
                try:
                    # Try to expand "see more" buttons in this specific post
                    expand_post_see_more(driver, post)
                    
                    # Extract content
                    content = extract_post_content(post)
                    
                    # Skip reposted content
                    if content == "[Reposted content - skipped]":
                        print("Skipping reposted content")
                        continue
                        
                    # Skip posts with no content
                    if not content or content == "[No text content found]" or content == "[Error extracting post content]":
                        print("Skipping post with no valid content")
                        continue
                        
                    # Check for duplicates
                    content_hash = generate_content_hash(content)
                    if content_hash in content_hashes:
                        print("Skipping duplicate post")
                        continue
                        
                    # Add hash to set to track duplicates
                    content_hashes.add(content_hash)
                    
                    # Extract date and engagement stats
                    date = extract_post_date(post)
                    engagement = extract_engagement_stats(post)
                    
                    # Add post data
                    posts_data.append({
                        'content': content,
                        'date': date,
                        'engagement': engagement
                    })
                    valid_posts_count += 1
                    pbar.update(1)
                    print(f"Found valid post #{valid_posts_count + start_from}")
                    
                    # Add a random delay between processing posts
                    random_delay(0.5, 1.5)
                    
                    # Break if we have enough valid posts for this batch
                    if valid_posts_count >= posts_to_scrape:
                        break
                        
                except StaleElementReferenceException:
                    print("Encountered a stale element. Skipping this post.")
                    continue
                except Exception as e:
                    print(f"Error processing post: {e}")
                    continue
        
        # Save posts to a file
        if posts_data:
            if len(posts_data) < posts_to_scrape:
                print(f"Warning: Only found {len(posts_data)} valid posts out of {posts_to_scrape} requested")
                
            filename = save_posts_to_file(posts_data, profile_name)
            
            # Check if we need to continue scraping
            posts_remaining = num_posts - (start_from + valid_posts_count)
            if posts_remaining > 0:
                print(f"Scraped {valid_posts_count} posts. {posts_remaining} posts remaining.")
                print(f"Continuing to scrape more posts...")
                
                # Return a dictionary with the current results and a flag to continue
                return {
                    'filename': filename,
                    'continue_scraping': True,
                    'posts_scraped': start_from + valid_posts_count,
                    'posts_remaining': posts_remaining
                }
            else:
                # Return just the filename when we're done
                return filename
        else:
            print("No valid posts found after filtering.")
            return None
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        if driver:
            # Add a final delay before quitting to avoid suspicion
            random_delay(2.0, 4.0)
            driver.quit()

def read_input_file(filename="linkedin_input.txt"):
    """Read inputs from a file."""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            
        if len(lines) < 5:
            print("Input file must contain at least 5 lines: profile URL, number of posts, username, password, headless mode (y/n)")
            return None
            
        profile_url = lines[0].strip()
        num_posts = int(lines[1].strip())
        username = lines[2].strip()
        password = lines[3].strip()
        headless = lines[4].strip().lower() == 'y'
        
        return {
            'profile_url': profile_url,
            'num_posts': num_posts,
            'username': username,
            'password': password,
            'headless': headless
        }
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None

def main():
    """Read inputs from file and run the scraper."""
    print("=" * 50)
    print("LinkedIn Rabbit - LinkedIn Post Scraper")
    print("=" * 50)
    print("Reading inputs from linkedin_input.txt...")
    
    # Read inputs from file
    inputs = read_input_file()
    if not inputs:
        print("Failed to read inputs from file. Please check the file format.")
        return
    
    print(f"Profile URL: {inputs['profile_url']}")
    print(f"Number of posts: {inputs['num_posts']}")
    print(f"Username: {inputs['username']}")
    print(f"Headless mode: {'Yes' if inputs['headless'] else 'No'}")
    
    print("\nStarting the scraper...")
    
    # Initialize variables for batch processing
    posts_scraped = 0
    total_posts = inputs['num_posts']
    batch_size = 30  # Process in batches of 30
    all_filenames = []
    
    while posts_scraped < total_posts:
        print(f"\nScraping batch: {posts_scraped+1}-{min(posts_scraped+batch_size, total_posts)} of {total_posts}")
        
        # Call the scraper function with the current progress
        result = scrape_linkedin_posts(
            inputs['profile_url'],
            total_posts,
            inputs['username'],
            inputs['password'],
            inputs['headless'],
            start_from=posts_scraped,
            batch_size=batch_size
        )
        
        # Handle the result
        if isinstance(result, dict) and result.get('continue_scraping'):
            # Save the batch result
            all_filenames.append(result['filename'])
            posts_scraped = result['posts_scraped']
            
            print(f"\nBatch complete! Scraped {posts_scraped} posts so far.")
            print(f"Batch results saved to: {result['filename']}")
            print(f"{result['posts_remaining']} posts remaining.")
            
            # Provide a brief pause between batches
            print("\nContinuing to next batch in 5 seconds...")
            time.sleep(5)
            
        elif result:
            # Final batch - scraping complete
            all_filenames.append(result)
            posts_scraped = total_posts
            
            print(f"\nSuccess! All {posts_scraped} posts have been extracted from {inputs['profile_url']}")
            print(f"Final results saved to: {result}")
            break
            
        else:
            print("\nFailed to extract posts. Please check your inputs and try again.")
            break
    
    if all_filenames:
        print("\nAll batches completed successfully!")
        print("Files saved:")
        for idx, filename in enumerate(all_filenames, 1):
            print(f"  Batch {idx}: {filename}")
    else:
        print("\nNo posts were extracted. Please check your inputs and try again.")

if __name__ == "__main__":
    main() 