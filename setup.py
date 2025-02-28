from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="linkedin-rabbit",
    version="1.0.0",
    author="Tensor Boy",
    author_email="manavgupta@duck.com",
    description="A powerful and stealthy LinkedIn post scraper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tensorboy/linkedin-rabbit",
    packages=find_packages(include=["linkedin_rabbit", "linkedin_rabbit.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "selenium>=4.10.0",
        "webdriver-manager>=3.8.6",
        "argparse>=1.4.0",
        "streamlit>=1.32.0",
        "pandas>=2.1.4",
        "fpdf>=1.7.2",
        "tqdm>=4.66.1",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "linkedin-rabbit=linkedin_rabbit.__main__:main",
            "linkedin-rabbit-cli=linkedin_rabbit.cli_entry:main",
            "linkedin-rabbit-app=linkedin_rabbit.app_entry:main",
        ],
    },
    include_package_data=True,
    keywords="linkedin, scraper, web scraping, data extraction, social media",
) 