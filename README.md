# LinkedIn Rabbit 🐰

A powerful and stealthy LinkedIn post scraper that allows you to extract posts from any LinkedIn profile.

![LinkedIn Rabbit Logo](https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png)

## Features

- 🚀 Extract posts from any LinkedIn profile
- 📊 Get engagement metrics (likes, comments, shares)
- 📅 Extract post dates
- 📄 Save posts to text and PDF files
- 🌐 Interactive Streamlit web interface
- 💻 Command-line interface for automation
- 🔒 Secure handling of credentials (not stored)
- 🕒 Delay between actions to avoid detection
- 🤖 Headless mode for background operation

## Installation

### Option 1: Install from PyPI

```bash
pip install linkedin-rabbit
```

### Option 2: Install from source

```bash
git clone https://github.com/tensorboy/linkedin-rabbit.git
cd linkedin-rabbit
pip install -e .
```

## Usage

### Web Interface

Run the Streamlit web interface:

```bash
linkedin-rabbit-app
```

Then open your browser at http://localhost:8501

### Command Line Interface

Run the CLI version:

```bash
linkedin-rabbit-cli --url "https://www.linkedin.com/in/username/" --posts 10 --username "your-email@example.com" --password "your-password" --headless --pdf
```

Or use an input file:

```bash
linkedin-rabbit-cli --file linkedin_input.txt
```

Where `linkedin_input.txt` has the following format:
```
https://www.linkedin.com/in/username/
10
your-email@example.com
your-password
y
```

### Python API

```python
from linkedin_rabbit import scrape_linkedin_posts

result_file = scrape_linkedin_posts(
    profile_url="https://www.linkedin.com/in/username/",
    num_posts=10,
    username="your-email@example.com",
    password="your-password",
    headless=True
)

print(f"Posts saved to: {result_file}")
```

## Requirements

- Python 3.8+
- Selenium
- Chrome/Chromium browser
- ChromeDriver (automatically installed)

## Troubleshooting

- **Login Issues**: Make sure your LinkedIn credentials are correct and your account is not locked.
- **Captcha**: If you encounter a captcha, try running without headless mode to solve it manually.
- **Rate Limiting**: LinkedIn may rate-limit your requests. Try increasing the delay between actions.
- **Chrome/ChromeDriver Issues**: Make sure you have Chrome installed and the ChromeDriver is compatible.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Made with ❤️ by [Tensor Boy](https://www.instagram.com/tensor._.boy/)

## Disclaimer

This tool is for educational purposes only. Use responsibly and respect LinkedIn's terms of service and rate limits. The author is not responsible for any misuse of this tool. 