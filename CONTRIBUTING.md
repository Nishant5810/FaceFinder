# Contributing to FaceFinder

Thank you for your interest in contributing to FaceFinder! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/FaceFinder.git
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On macOS/Linux
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** and test thoroughly
3. **Commit with clear messages**:
   ```bash
   git commit -m "Add clear description of your changes"
   ```
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** on the main repository

## Code Standards

- Follow PEP 8 Python style guide
- Add comments for complex logic
- Test your changes before submitting
- Avoid using emojis in commit messages and documentation

## Reporting Issues

When reporting issues, include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS information

## Questions?

Feel free to open an issue for any questions or discussions.
