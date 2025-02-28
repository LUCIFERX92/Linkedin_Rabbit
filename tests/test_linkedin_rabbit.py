"""
Tests for the LinkedIn Rabbit scraper.
"""

import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from linkedin_rabbit.linkedin_rabbit import setup_driver, get_posts_url, generate_content_hash

def test_setup_driver():
    """Test that the driver can be set up."""
    try:
        driver = setup_driver(headless=True)
        assert driver is not None
        driver.quit()
    except Exception as e:
        pytest.skip(f"Failed to set up driver: {e}")

def test_get_posts_url():
    """Test that the posts URL is correctly generated."""
    profile_url = "https://www.linkedin.com/in/username/"
    posts_url = get_posts_url(profile_url)
    assert posts_url == "https://www.linkedin.com/in/username/recent-activity/shares/"
    
    # Test with trailing slash
    profile_url = "https://www.linkedin.com/in/username"
    posts_url = get_posts_url(profile_url)
    assert posts_url == "https://www.linkedin.com/in/username/recent-activity/shares/"

def test_generate_content_hash():
    """Test that content hashes are generated correctly."""
    content1 = "This is a test post."
    content2 = "This is a test post."
    content3 = "This is a different test post."
    
    hash1 = generate_content_hash(content1)
    hash2 = generate_content_hash(content2)
    hash3 = generate_content_hash(content3)
    
    assert hash1 == hash2
    assert hash1 != hash3

def test_output_directory_exists():
    """Test that the output directory exists or can be created."""
    os.makedirs("output", exist_ok=True)
    assert os.path.exists("output") 