# Contributing to ARIS Studio

Thank you for your interest in contributing to **ARIS Studio (Adaptive Runtime Intelligence System)**! We welcome contributions from researchers, embedded firmware developers, compiler engineers, and frontend developers.

---

## 1. Development Environment Setup

### Prerequisites
- **Python 3.11, 3.12, or 3.13**
- **Node.js 18+ & npm 9+**
- **Arduino CLI v1.5.1+** with `arduino:avr` core installed

### Installation Steps
```bash
# Clone the repository
git clone https://github.com/medhakg205/ARIS.git
cd ARIS

# Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd aris_desktop
npm install
cd ..
```

---

## 2. Running Verification Tests

Before submitting any Pull Request, you **must** ensure all automated test suites pass with zero failures:

```bash
# 1. Backend test suite (278 tests)
python -m pytest backend/tests

# 2. Embedded runtime test suite (21 tests)
python -m pytest embedded/tests

# 3. Frontend Vitest suite (36 tests)
cd aris_desktop
npm test

# 4. TypeScript strict verification
npx tsc --noEmit

# 5. Production desktop build
npm run build
```

---

## 3. Coding Standards & Guidelines

### Python (Backend)
- Adhere strictly to **PEP 8** style guidelines.
- Use explicit type annotations on all function signatures (`typing` / Pydantic models).
- Database queries must execute through `backend.database.db_engine`.
- Never perform blocking I/O inside asynchronous FastAPI route handlers; use async executors or background tasks.

### TypeScript & React (Desktop)
- Strict mode enabled (`noImplicitAny: true`).
- Prefer functional components with React hooks.
- Use Tailwind CSS classes for styling; adhere to the dark-mode aesthetic (slate/zinc palette with subtle neon borders).
- Keep components modular and reusable in `aris_desktop/src/components/`.

### Embedded C++ (Runtime)
- **Zero dynamic allocation:** `malloc()`, `calloc()`, and `new` are strictly prohibited.
- **Microcontroller constraints:** Minimize static memory; keep the LEAN footprint under 16 bytes of static SRAM.
- Code must compile with `avr-gcc` using `-std=gnu++11` and `-Os`.

---

## 4. Git Workflow & Commit Guidelines

- Work on dedicated feature branches: `git checkout -b feature/my-feature`.
- Write clear, descriptive commit messages:
  - `feat: add Timer2 capture support for AVR8`
  - `fix: prevent serial port contention on Windows upload`
  - `docs: update memory preflight documentation`
- Never commit private `.db`, log files, or build artifacts.

---

## 5. Reporting Issues

Please open a GitHub issue with:
1. Target microcontroller board (e.g. Arduino Uno R3, ATmega328P).
2. Operating system and Arduino CLI version.
3. Minimal reproducible `.ino` sketch.
4. Full compiler output and error trace.
