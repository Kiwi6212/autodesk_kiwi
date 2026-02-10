# Contributing Guide

Thank you for your interest in contributing to AutoDesk Kiwi.

---

## How to Contribute

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/autodesk_kiwi.git
cd autodesk_kiwi
```

### 2. Create a Branch

```bash
git checkout -b feature/my-feature
```

### 3. Set Up the Environment

```bash
cd api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 4. Make Your Changes

- Follow the existing code style
- Add tests when possible
- Write clear commit messages
- Keep changes focused and atomic

### 5. Test Your Changes

```bash
cd api
uvicorn main:app --reload
```

### 6. Commit and Push

```bash
git add .
git commit -m "feat: add feature description"
git push origin feature/my-feature
```

### 7. Create a Pull Request

Target the `main` branch. Include:
- What changes you made
- Why these changes are needed
- Screenshots (if UI changes)
- Any breaking changes

---

## Code Standards

### Python (Backend)

- Python 3.12+
- Type hints on all function signatures
- Logging via `logger` instead of `print()`
- PEP 8 compliance
- Grouped imports (stdlib, third-party, local)
- Specific exception handling

### JavaScript (Frontend)

- ES6+ syntax
- Alpine.js best practices
- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Minimal global scope pollution

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting (no logic change) |
| `refactor` | Code refactoring |
| `test` | Tests |
| `chore` | Maintenance |

---

## Reporting Bugs

Open an issue with:
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, browser)
- Screenshots if applicable

---

## Feature Requests

Open an issue with:
- Feature description
- Problem it solves
- Proposed solution
- Use cases

---

## Pull Request Checklist

- [ ] Tested locally
- [ ] No secrets committed
- [ ] Clear commit messages
- [ ] Documentation updated if needed
- [ ] All tests pass
- [ ] No breaking changes (or documented)

---

## Questions?

Check existing [Issues](https://github.com/Kiwi6212/autodesk_kiwi/issues) or open a new one.
