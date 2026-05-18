# User Account Management Web App

A full-stack web application built with Python and FastHTML for managing user accounts in an internal admin context. Supports account creation, credential management, search, and soft-deletion via archiving.

---

## Features

- **Account Creation** — Register new users with validated inputs
- **Password Management** — Secure password hashing for credential storage and updates
- **User Search** — Query and filter active user accounts
- **Soft Archiving** — Archive users instead of permanently deleting them, preserving data integrity
- **Archive Management** — View and restore archived users on demand
- **Audit Logging** — Structured logging and error handling across all account operations
- **CLI Support** — Command-line interface for administrative tasks

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Web Framework | FastHTML |
| Database | SQLite |
| Auth | Password hashing (bcrypt) |
| Logging | Python `logging` module |

---

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
git clone https://github.com/your-username/user-account-management.git
cd user-account-management
pip install -r requirements.txt
```

### Running the App

```bash
python main.py
```

The app will be available at `http://localhost:5000` by default.

### CLI Usage

```bash
python cli.py --help
```

---

## Project Structure

```
.
├── main.py          # App entry point and route definitions
├── models.py        # User data models and database schema
├── auth.py          # Password hashing and authentication logic
├── cli.py           # Command-line admin interface
├── logger.py        # Logging configuration
└── README.md
```

---

## Why I Built This

I built this project to deepen my understanding of backend service design, authentication workflows, and internal tooling. Working through password hashing, soft-delete patterns, and a CLI layer gave me hands-on experience with the kinds of systems commonly found in real-world admin dashboards and identity management services.

---

## License

MIT
