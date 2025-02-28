# Contributing to LinkedIn Rabbit

Thank you for considering contributing to LinkedIn Rabbit! This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in the [Issues](https://github.com/tensorboy/linkedin-rabbit/issues)
- If not, create a new issue with a clear title and description
- Include steps to reproduce the bug, expected behavior, and actual behavior
- Include screenshots if applicable
- Include your environment details (OS, Python version, etc.)

### Suggesting Enhancements

- Check if the enhancement has already been suggested in the [Issues](https://github.com/tensorboy/linkedin-rabbit/issues)
- If not, create a new issue with a clear title and description
- Explain why this enhancement would be useful to most users

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Add or update tests as necessary
5. Run the tests to make sure they pass
6. Update documentation as necessary
7. Submit a pull request

## Development Setup

1. Clone the repository
```bash
git clone https://github.com/tensorboy/linkedin-rabbit.git
cd linkedin-rabbit
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies
```bash
pip install -e ".[dev]"
```

4. Run tests
```bash
pytest
```

## Coding Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Write docstrings for all functions, classes, and modules
- Add type hints where appropriate
- Write tests for new features

## Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## License

By contributing to LinkedIn Rabbit, you agree that your contributions will be licensed under the project's [MIT License](LICENSE). 