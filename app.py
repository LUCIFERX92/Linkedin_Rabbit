#!/usr/bin/env python3
# LinkedIn Rabbit - Streamlit App Entry Point

import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import the linkedin_rabbit package
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import the main function from the app module
from linkedin_rabbit.app import main

if __name__ == "__main__":
    main()
