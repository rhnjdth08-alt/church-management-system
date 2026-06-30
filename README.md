# Church Management System

A starter backend for the Church Management System MVP.

## Setup

Install dependencies:

```powershell
C:/Users/Onwa/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pip install -r requirements.txt
```

Run the app:

```powershell
C:/Users/Onwa/AppData/Local/Python/pythoncore-3.14-64/python.exe -m uvicorn app.main:app --reload
```

## Project structure

- `backend/app` - FastAPI application source files
- `backend/tests` - unit and integration tests
- `church.db` - local SQLite database (created on startup)

## Next steps

- Implement member create/edit APIs
- Add member directory listing and validation
- Extend the data model for households and divisions
