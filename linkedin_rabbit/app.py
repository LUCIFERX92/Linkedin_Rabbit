import streamlit as st
import os
import time
import base64
import pandas as pd
import re
from datetime import datetime
from fpdf import FPDF
from pathlib import Path

import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
from linkedin_rabbit import scrape_linkedin_posts, read_input_file


# Set page configuration
st.set_page_config(
    page_title="LinkedIn Rabbit - Post Scraper",
    page_icon="🐰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0077B5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0077B5;
        margin-bottom: 1rem;
    }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        margin-top: 3rem;
    }
    .stProgress > div > div > div > div {
        background-color: #0077B5;
    }
    .info-box {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #0077B5;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #f0fff0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #00B57A;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fffaf0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #FFA500;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #fff0f0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.5rem solid #FF0000;
        margin-bottom: 1rem;
    }
    .terminal-box {
        background-color: #1E1E1E;
        color: #FFFFFF;
        font-family: 'Courier New', monospace;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        white-space: pre-wrap;
    }
    .terminal-command {
        color: #63C5DA;
    }
    .terminal-output {
        color: #CCCCCC;
    }
    .terminal-success {
        color: #00B57A;
    }
    .terminal-error {
        color: #FF6B6B;
    }
    .terminal-warning {
        color: #FFA500;
    }
    .terminal-info {
        color: #63C5DA;
    }
    .terminal-progress {
        color: #CCCCCC;
        margin-left: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def create_pdf(posts_data, profile_name):
    """Create a PDF file from the posts data"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Arial", "B", 16)
        
        # Extract username if it's in the profile_name
        username = ""
        if "_" in profile_name:
            parts = profile_name.split("_")
            if len(parts) > 1:
                username = parts[-1]
                # Format username for display
                username = username.replace("_", " ")
        
        # Title
        pdf.cell(0, 10, f"LinkedIn Posts for: {profile_name.split('_')[0]}", 0, 1, "C")
        
        # Add username if available
        if username:
            pdf.set_font("Arial", "I", 14)
            pdf.cell(0, 10, f"LinkedIn Username: {username}", 0, 1, "C")
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")
        pdf.cell(0, 10, f"Number of posts: {len(posts_data)}", 0, 1, "C")
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Add posts
        for idx, post in enumerate(posts_data, 1):
            try:
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, f"Post #{idx}", 0, 1)
                
                pdf.set_font("Arial", "I", 12)
                pdf.cell(0, 10, f"Date: {post['date']}", 0, 1)
                
                # Format engagement data
                engagement = post['engagement']
                engagement_str = f"{engagement.get('likes', '0')} likes, {engagement.get('comments', '0')} comments, {engagement.get('shares', '0')} shares"
                pdf.cell(0, 10, f"Engagement: {engagement_str}", 0, 1)
                
                pdf.ln(5)
                pdf.set_font("Arial", "", 12)
                
                # Handle multi-line content with proper encoding
                try:
                    content = post['content']
                    # Replace any problematic characters
                    content = ''.join(char if ord(char) < 65536 else '?' for char in content)
                    
                    # Handle multi-line content
                    content_lines = content.split('\n')
                    for line in content_lines:
                        # Skip empty lines
                        if not line.strip():
                            pdf.ln(5)
                            continue
                            
                        # Clean the line to ensure it's PDF-compatible
                        # Replace any characters outside the valid range
                        clean_line = ''
                        for char in line:
                            if 32 <= ord(char) <= 255:  # Basic Latin and Latin-1 Supplement
                                clean_line += char
                            else:
                                clean_line += '?'
                        
                        # Split long lines
                        while len(clean_line) > 80:
                            pdf.multi_cell(0, 10, clean_line[:80])
                            clean_line = clean_line[80:]
                        pdf.multi_cell(0, 10, clean_line)
                except Exception as e:
                    print(f"Error adding content to PDF: {e}")
                    pdf.multi_cell(0, 10, "[Error displaying content]")
                
                pdf.ln(5)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
                
                # Add a new page if needed
                if idx < len(posts_data) and pdf.get_y() > 250:
                    pdf.add_page()
            except Exception as e:
                print(f"Error processing post #{idx} for PDF: {e}")
                pdf.multi_cell(0, 10, f"[Error processing post #{idx}]")
                pdf.ln(5)
                continue
        
        # Footer
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, "Generated by LinkedIn Rabbit | @tensor._.boy", 0, 0, "C")
        
        # Save PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("output", exist_ok=True)
        pdf_filename = f"output/{profile_name}_{timestamp}.pdf"
        
        try:
            pdf.output(pdf_filename)
            print(f"PDF saved successfully: {pdf_filename}")
            return pdf_filename
        except Exception as e:
            print(f"Error saving PDF: {e}")
            # Try with a more basic approach
            try:
                # Create a simpler PDF with minimal content
                simple_pdf = FPDF()
                simple_pdf.add_page()
                simple_pdf.set_font("Arial", "B", 16)
                simple_pdf.cell(0, 10, f"LinkedIn Posts for: {profile_name.split('_')[0]}", 0, 1, "C")
                
                # Add username if available
                if username:
                    simple_pdf.set_font("Arial", "I", 14)
                    simple_pdf.cell(0, 10, f"LinkedIn Username: {username}", 0, 1, "C")
                
                simple_pdf.set_font("Arial", "", 12)
                simple_pdf.cell(0, 10, f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")
                simple_pdf.cell(0, 10, f"Number of posts: {len(posts_data)}", 0, 1, "C")
                simple_pdf.cell(0, 10, "Error creating detailed PDF. Please check the text file for complete content.", 0, 1)
                
                pdf_filename = f"output/{profile_name}_simple_{timestamp}.pdf"
                simple_pdf.output(pdf_filename)
                print(f"Simple PDF saved as fallback: {pdf_filename}")
                return pdf_filename
            except Exception as e2:
                print(f"Error saving simple PDF: {e2}")
                return None
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generate a download link for a file"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

def main():
    # Header
    st.markdown('<h1 class="main-header">LinkedIn Rabbit 🐰</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Extract posts from any LinkedIn profile with ease</p>', unsafe_allow_html=True)
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Sidebar
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png", width=50)
    st.sidebar.markdown("## LinkedIn Rabbit")
    st.sidebar.markdown("Extract posts from any LinkedIn profile")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### How it works")
    st.sidebar.markdown("""
    1. Enter LinkedIn profile URL
    2. Specify number of posts to extract
    3. Enter your LinkedIn credentials
    4. Click 'Start Scraping'
    5. Download the results
    """)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Batch Processing")
    st.sidebar.markdown("""
    For requests over 30 posts:
    - Posts are processed in batches of 30
    - The scraper will automatically continue until all posts are collected
    - Final combined results will be available for download
    """)
    st.sidebar.markdown("---")
    st.sidebar.markdown("Made with ❤️ by Tensor Boy")
    st.sidebar.markdown("[GitHub Repository](https://github.com/tensorboy/linkedin-rabbit)")
    st.sidebar.markdown("[Instagram](https://www.instagram.com/tensor._.boy/)")
    
    # Initialize session state for tracking scraping progress
    if 'scraping_in_progress' not in st.session_state:
        st.session_state.scraping_in_progress = False
    if 'posts_scraped' not in st.session_state:
        st.session_state.posts_scraped = 0
    if 'total_posts' not in st.session_state:
        st.session_state.total_posts = 0
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    if 'continue_scraping' not in st.session_state:
        st.session_state.continue_scraping = False
    if 'scraping_complete' not in st.session_state:
        st.session_state.scraping_complete = False
    if 'all_posts_data' not in st.session_state:
        st.session_state.all_posts_data = []
    if 'profile_name' not in st.session_state:
        st.session_state.profile_name = ""
    if 'username_from_url' not in st.session_state:
        st.session_state.username_from_url = ""
    
    # Main form
    with st.form("scraper_form"):
        st.markdown('<h2 class="sub-header">Enter Scraping Details</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            profile_url = st.text_input("LinkedIn Profile URL", placeholder="https://www.linkedin.com/in/username/")
            num_posts = st.number_input("Number of posts to extract", min_value=1, max_value=100, value=10)
        
        with col2:
            linkedin_username = st.text_input("LinkedIn Email/Username", placeholder="your.email@example.com")
            linkedin_password = st.text_input("LinkedIn Password", type="password")
        
        headless = st.checkbox("Run in headless mode (recommended)", value=True)
        
        st.markdown('<div class="info-box">⚠️ Your credentials are used only for logging into LinkedIn and are not stored anywhere.</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Start Scraping")
    
    # Handle form submission
    if submitted:
        if not profile_url or not linkedin_username or not linkedin_password:
            st.error("Please fill in all the required fields.")
        else:
            # Extract username from URL for file naming
            if '/in/' in profile_url:
                username = profile_url.split('/in/')[-1].split('/')[0]
            elif '/company/' in profile_url:
                username = profile_url.split('/company/')[-1].split('/')[0]
            else:
                username = "linkedin_user"
            
            # Clean up username
            username = username.replace('-', '_').replace('.', '_')
            
            # Reset session state
            st.session_state.scraping_in_progress = True
            st.session_state.posts_scraped = 0
            st.session_state.total_posts = num_posts
            st.session_state.batch_results = []
            st.session_state.continue_scraping = True
            st.session_state.scraping_complete = False
            st.session_state.all_posts_data = []
            st.session_state.profile_name = ""
            st.session_state.username_from_url = username
            
            # Create a temporary input file
            with open("temp_input.txt", "w") as f:
                f.write(f"{profile_url}\n")
                f.write(f"{num_posts}\n")
                f.write(f"{linkedin_username}\n")
                f.write(f"{linkedin_password}\n")
                f.write(f"{'y' if headless else 'n'}\n")
    
    # Display scraping progress
    if st.session_state.scraping_in_progress:
        st.markdown('<h2 class="sub-header">Scraping in Progress</h2>', unsafe_allow_html=True)
        
        # Create multiple progress bars for different phases
        login_progress = st.progress(0)
        scroll_progress = st.progress(0)
        extraction_progress = st.progress(0)
        overall_progress = st.progress(0)
        
        # Create containers for status updates
        status_text = st.empty()
        phase_text = st.empty()
        terminal_output = st.empty()
        
        # Terminal-style output container
        terminal_content = ""
        
        # Add initial terminal content
        terminal_content += '<div class="terminal-box">'
        terminal_content += '<span class="terminal-command">$ linkedin-rabbit</span>\n'
        terminal_content += '<span class="terminal-info">Initializing LinkedIn Rabbit scraper...</span>\n'
        terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
        
        try:
            # Run the scraper
            status_text.markdown("<h3>Running the scraper...</h3>", unsafe_allow_html=True)
            
            # Start or continue scraping
            if st.session_state.continue_scraping:
                batch_size = 30  # Process in batches of 30
                
                # Create a container for real-time updates
                update_container = st.container()
                
                # Auto-continue until all posts are scraped
                while st.session_state.continue_scraping and st.session_state.posts_scraped < st.session_state.total_posts:
                    # Update terminal output
                    batch_num = len(st.session_state.batch_results) + 1
                    terminal_content += f'<span class="terminal-info">Starting batch {batch_num} ({st.session_state.posts_scraped}/{st.session_state.total_posts} posts scraped so far)</span>\n'
                    terminal_content += f'<span class="terminal-command">$ scrape_linkedin_posts --start={st.session_state.posts_scraped} --batch-size={batch_size}</span>\n'
                    terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
                    
                    # Update overall progress
                    overall_percentage = st.session_state.posts_scraped / st.session_state.total_posts
                    overall_progress.progress(overall_percentage)
                    
                    # Show detailed progress updates
                    with update_container:
                        st.markdown(f"""
                        <div class="info-box">
                            <h4>Scraping Progress</h4>
                            <p>Posts scraped: <b>{st.session_state.posts_scraped}</b> of <b>{st.session_state.total_posts}</b></p>
                            <p>Current batch: <b>{batch_num}</b></p>
                            <p>Remaining posts: <b>{st.session_state.total_posts - st.session_state.posts_scraped}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Simulate login phase
                    phase_text.markdown("<h4>Phase 1: Logging into LinkedIn...</h4>", unsafe_allow_html=True)
                    for i in range(101):
                        login_progress.progress(i/100)
                        if i < 30:
                            status_text.markdown(f"<p>Opening browser...</p>", unsafe_allow_html=True)
                        elif i < 60:
                            status_text.markdown(f"<p>Navigating to LinkedIn...</p>", unsafe_allow_html=True)
                        elif i < 90:
                            status_text.markdown(f"<p>Entering credentials...</p>", unsafe_allow_html=True)
                        else:
                            status_text.markdown(f"<p>Completing login...</p>", unsafe_allow_html=True)
                        time.sleep(0.01)  # Quick animation
                    
                    # Simulate scrolling phase
                    phase_text.markdown("<h4>Phase 2: Loading posts...</h4>", unsafe_allow_html=True)
                    for i in range(101):
                        scroll_progress.progress(i/100)
                        status_text.markdown(f"<p>Scrolling to load posts ({i}%)...</p>", unsafe_allow_html=True)
                        time.sleep(0.02)  # Slightly slower animation
                    
                    # Simulate extraction phase
                    phase_text.markdown("<h4>Phase 3: Extracting post content...</h4>", unsafe_allow_html=True)
                    
                    # Call the scraper function with the current progress
                    result = scrape_linkedin_posts(
                        profile_url,
                        num_posts,
                        linkedin_username,
                        linkedin_password,
                        headless,
                        start_from=st.session_state.posts_scraped,
                        batch_size=batch_size
                    )
                    
                    # Simulate extraction progress while scraping happens
                    for i in range(101):
                        extraction_progress.progress(i/100)
                        status_text.markdown(f"<p>Extracting post content ({i}%)...</p>", unsafe_allow_html=True)
                        time.sleep(0.02)  # Slightly slower animation
                    
                    # Handle the result
                    if isinstance(result, dict) and result.get('continue_scraping'):
                        # Save the batch result
                        st.session_state.batch_results.append(result['filename'])
                        st.session_state.posts_scraped = result['posts_scraped']
                        
                        # Get profile name if not already set
                        if not st.session_state.profile_name:
                            st.session_state.profile_name = os.path.basename(result['filename']).split('_linkedin_posts_')[0]
                        
                        # Update overall progress
                        overall_percentage = st.session_state.posts_scraped / st.session_state.total_posts
                        overall_progress.progress(overall_percentage)
                        
                        # Parse the batch and add to all posts data
                        batch_posts_data = parse_text_file(result['filename'])
                        st.session_state.all_posts_data.extend(batch_posts_data)
                        
                        # Update terminal output
                        terminal_content += f'<span class="terminal-success">✓ Batch {batch_num} complete! Found {len(batch_posts_data)} posts.</span>\n'
                        terminal_content += f'<span class="terminal-output">Total posts scraped: {st.session_state.posts_scraped}/{st.session_state.total_posts}</span>\n'
                        terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
                        
                        # Display batch information in the UI
                        with update_container:
                            st.markdown(f"""
                            <div class="success-box">
                                <h4>✅ Batch {batch_num} Complete!</h4>
                                <p>Successfully scraped <b>{len(batch_posts_data)}</b> posts in this batch.</p>
                                <p>Total posts scraped: <b>{st.session_state.posts_scraped}</b> of <b>{st.session_state.total_posts}</b></p>
                                <p>Remaining: <b>{result['posts_remaining']}</b> posts</p>
                                <p>Progress: <b>{int(overall_percentage * 100)}%</b> complete</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add individual batch download options
                            st.markdown(f"### Batch {batch_num} Results")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"#### Batch {batch_num} Text File")
                                st.markdown(get_binary_file_downloader_html(result['filename'], f'Download Batch {batch_num} Text File'), unsafe_allow_html=True)
                            with col2:
                                # Create PDF for this batch
                                batch_pdf = create_pdf(batch_posts_data, f"{st.session_state.profile_name}_batch{batch_num}")
                                if batch_pdf:
                                    st.markdown(f"#### Batch {batch_num} PDF File")
                                    st.markdown(get_binary_file_downloader_html(batch_pdf, f'Download Batch {batch_num} PDF File'), unsafe_allow_html=True)
                        
                        # Continue to next batch automatically if needed
                        if st.session_state.posts_scraped < st.session_state.total_posts:
                            terminal_content += '<span class="terminal-info">Continuing to next batch in 3 seconds...</span>\n'
                            terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
                            
                            # Add countdown timer
                            countdown_text = st.empty()
                            for i in range(3, 0, -1):
                                countdown_text.markdown(f"<h3>Continuing to next batch in {i} seconds...</h3>", unsafe_allow_html=True)
                                time.sleep(1)
                            countdown_text.empty()
                        else:
                            st.session_state.continue_scraping = False
                            st.session_state.scraping_complete = True
                    
                    elif result:
                        # Final batch - scraping complete
                        st.session_state.batch_results.append(result)
                        st.session_state.posts_scraped = num_posts
                        st.session_state.continue_scraping = False
                        st.session_state.scraping_complete = True
                        
                        # Update progress to 100%
                        overall_progress.progress(1.0)
                        
                        # Parse the text file to create a PDF
                        final_batch_posts = parse_text_file(result)
                        st.session_state.all_posts_data.extend(final_batch_posts)
                        
                        # Get profile name if not already set
                        if not st.session_state.profile_name:
                            st.session_state.profile_name = os.path.basename(result).split('_linkedin_posts_')[0]
                        
                        # Update terminal output
                        terminal_content += f'<span class="terminal-success">✓ Final batch complete! Found {len(final_batch_posts)} posts.</span>\n'
                        terminal_content += f'<span class="terminal-success">✓ All {st.session_state.posts_scraped} posts scraped successfully!</span>\n'
                        terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
                    
                    else:
                        # Error occurred
                        terminal_content += '<span class="terminal-error">✗ Error: Failed to extract posts. Please check your inputs and try again.</span>\n'
                        terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
                        st.error("Failed to extract posts. Please check your inputs and try again.")
                        st.session_state.scraping_in_progress = False
                        st.session_state.continue_scraping = False
                        break
                
                # All batches completed - create combined files
                if st.session_state.scraping_complete:
                    profile_name = st.session_state.profile_name
                    username = st.session_state.username_from_url
                    
                    # Update terminal output
                    terminal_content += '<span class="terminal-info">Creating combined output files...</span>\n'
                    terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
                    
                    # Show file creation progress
                    file_creation_progress = st.progress(0)
                    file_status = st.empty()
                    
                    # Create combined text file with progress updates
                    file_status.markdown("<p>Creating combined text file...</p>", unsafe_allow_html=True)
                    for i in range(50):
                        file_creation_progress.progress(i/100)
                        time.sleep(0.05)
                    combined_text_file = combine_text_files(st.session_state.batch_results, f"{profile_name}_{username}")
                    
                    # Create combined PDF file with progress updates
                    file_status.markdown("<p>Creating combined PDF file...</p>", unsafe_allow_html=True)
                    for i in range(50, 101):
                        file_creation_progress.progress(i/100)
                        time.sleep(0.05)
                    combined_pdf_file = create_pdf(st.session_state.all_posts_data, f"{profile_name}_{username}")
                    
                    # Update terminal output
                    terminal_content += f'<span class="terminal-success">✓ Combined text file created: {os.path.basename(combined_text_file)}</span>\n'
                    terminal_content += f'<span class="terminal-success">✓ Combined PDF file created: {os.path.basename(combined_pdf_file)}</span>\n'
                    terminal_content += '<span class="terminal-success">✓ Scraping process completed successfully!</span>\n'
                    terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
                    
                    # Success message with confetti effect
                    st.balloons()  # Add balloons for a celebratory effect
                    st.markdown('<div class="success-box">✅ Scraping completed successfully!</div>', unsafe_allow_html=True)
                    
                    # Display results
                    st.markdown('<h2 class="sub-header">Results</h2>', unsafe_allow_html=True)
                    
                    # Read the combined text file
                    with open(combined_text_file, 'r', encoding='utf-8', errors='ignore') as f:
                        combined_content = f.read()
                    
                    # Display content in a text area
                    st.text_area("All Posts", combined_content, height=400)
                    
                    # Provide download links for combined files only
                    st.markdown("### Download Files")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Combined Text File")
                        st.markdown(get_binary_file_downloader_html(combined_text_file, 'Download Text File'), unsafe_allow_html=True)
                    with col2:
                        st.markdown("#### Combined PDF File")
                        st.markdown(get_binary_file_downloader_html(combined_pdf_file, 'Download PDF File'), unsafe_allow_html=True)
            
        except Exception as e:
            # Update terminal output with error
            terminal_content += f'<span class="terminal-error">✗ Error: {str(e)}</span>\n'
            terminal_content += '<span class="terminal-error">Please check your LinkedIn credentials and try again.</span>\n'
            terminal_output.markdown(terminal_content + '</div>', unsafe_allow_html=True)
            
            st.error(f"An error occurred: {str(e)}")
            st.info("Please check your LinkedIn credentials and try again.")
            st.session_state.scraping_in_progress = False
        
        finally:
            # Clean up temporary input file
            if os.path.exists("temp_input.txt"):
                os.remove("temp_input.txt")
    
    # Footer
    st.markdown('<div class="footer">LinkedIn Rabbit © 2023 | Made by Tensor Boy (@tensor._.boy) | Open Source Project</div>', unsafe_allow_html=True)

def parse_text_file(file_path):
    """Parse the text file to extract post data."""
    posts_data = []
    current_post = None
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        for line in content.split('\n'):
            if line.startswith('Post #'):
                if current_post:
                    posts_data.append(current_post)
                current_post = {'content': ''}
            elif current_post:
                if line.startswith('Date:'):
                    current_post['date'] = line[5:].strip()
                elif line.startswith('Engagement:'):
                    engagement_text = line[11:].strip()
                    likes = comments = shares = '0'
                    
                    likes_match = re.search(r'(\d+) likes', engagement_text)
                    if likes_match:
                        likes = likes_match.group(1)
                    
                    comments_match = re.search(r'(\d+) comments', engagement_text)
                    if comments_match:
                        comments = comments_match.group(1)
                    
                    shares_match = re.search(r'(\d+) shares', engagement_text)
                    if shares_match:
                        shares = shares_match.group(1)
                    
                    current_post['engagement'] = {
                        'likes': likes,
                        'comments': comments,
                        'shares': shares
                    }
                elif not line.startswith('=') and not line.startswith('-') and not line.startswith('LinkedIn Posts for:') and not line.startswith('Extracted on:') and not line.startswith('Number of posts:'):
                    current_post['content'] += line + '\n'
        
        # Add the last post
        if current_post:
            posts_data.append(current_post)
        
        return posts_data
    except Exception as e:
        print(f"Error parsing text file: {e}")
        return []

def combine_text_files(batch_files, profile_name):
    """Combine text files from a list of batch files into a single file."""
    # Extract header from the first file
    with open(batch_files[0], 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        header_lines = []
        for i, line in enumerate(lines):
            if line.startswith('='):
                header_lines = lines[:i+1]
                break
    
    # Create a new header with updated information
    total_posts = 0
    all_posts_content = []
    
    for batch_file in batch_files:
        with open(batch_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Extract number of posts
            num_posts_match = re.search(r'Number of posts: (\d+)', content)
            if num_posts_match:
                total_posts += int(num_posts_match.group(1))
            
            # Extract post content (skip header)
            post_sections = content.split('=' * 80)[1].strip()
            all_posts_content.append(post_sections)
    
    # Extract username if it's in the profile_name
    username = ""
    display_name = profile_name
    if "_" in profile_name:
        parts = profile_name.split("_")
        if len(parts) > 1:
            display_name = parts[0]
            username = parts[-1]
            # Format username for display
            username = username.replace("_", " ")
    
    # Create the combined file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("output", exist_ok=True)
    combined_file = f"output/{profile_name}_all_batches_{timestamp}.txt"
    
    with open(combined_file, 'w', encoding='utf-8', errors='ignore') as f:
        # Write updated header
        f.write(f"LinkedIn Posts for: {display_name}\n")
        if username:
            f.write(f"LinkedIn Username: {username}\n")
        f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Number of posts: {total_posts}\n")
        f.write("=" * 80 + "\n\n")
        
        # Write all posts with renumbered indices
        post_index = 1
        for content in all_posts_content:
            # Split into individual posts
            posts = content.split('-' * 80)
            for post in posts:
                if post.strip():
                    # Replace the post number
                    post_with_new_index = re.sub(r'Post #\d+', f'Post #{post_index}', post, 1)
                    f.write(post_with_new_index.strip() + "\n\n" + "-" * 80 + "\n\n")
                    post_index += 1
    
    return combined_file

if __name__ == "__main__":
    main() 