# United Agencies Karachi ERP Desktop

Electron desktop application for United Agencies Karachi operations.

## What This App Handles

- Sign-in for office users
- Invoice listing, creation, and PDF generation
- Inventory listing, search, add, and edit workflows
- Product selection from inventory during invoice creation
- Stock deduction when invoices are saved
- Order logging with attached PDF or image files
- Payment status tracking for pending and received receivables
- Business Intelligence reporting for sales, collections, institution reach, and inventory pressure

## Data Layer

The desktop app supports:

- PostgreSQL through `POSTGRES_URL` or `db.config.json`
- Local SQLite fallback in the Windows app-data directory

Example PostgreSQL configuration is available in `db.config.example.json`.

## Files

- `main.js`: Electron main process, schema setup, data access, and IPC handlers
- `preload.js`: safe renderer bridge exposed to the UI
- `renderer/`: HTML, CSS, and browser-side UI logic
- `backend/`: Python helpers used by the desktop app
- `assets/`: logo and app image assets

## Run

```bash
npm install
npm start
```

## Build

```bash
npm run dist
```

The Windows installer is generated in `dist/`.
