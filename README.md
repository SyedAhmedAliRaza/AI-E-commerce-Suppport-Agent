# TechMania AI E-Commerce Support Agent

An intelligent, full-stack customer support and automated refund processing platform powered by FastAPI, Next.js, ChromaDB vector store RAG, Google Sheets integration, and automated HTML email notifications.

## Short Description

**TechMania AI E-Commerce Support Agent** is a full-stack AI platform designed to automate e-commerce customer support workflows. It integrates natural language processing via Google Gemini, docx policy retrieval-augmented generation (RAG) using ChromaDB, real-time Google Sheets lookup for product catalogs and order status, and automated HTML refund confirmation email generation via SMTP.

---

## Features

- **Automated Refund Eligibility & Workflow**: Evaluates customer refund requests against company policy rules (30-day return window, damage/defective item guarantees), updates order status in real time, and requests bank payout details.
- **Policy RAG Search (ChromaDB)**: Extracts and vector-indexes company policy documents (`.docx`) into ChromaDB for contextual retrieval during customer inquiries.
- **Google Sheets Database Synchronization**: Fetches and manages products, order tracking information, and customer interaction logs directly from Google Sheets with automatic local CSV fallbacks.
- **Automated Email Dispatch**: Generates and dispatches responsive HTML refund evaluation emails to customers via SMTP.
- **Modern Responsive UI**: Built with Next.js 15, Tailwind CSS, and glassmorphic aesthetics for a smooth user experience.

---

## System Architecture & Tech Stack

- **Backend Framework**: Python FastAPI, Uvicorn
- **AI & Vector DB**: Google Gemini API, ChromaDB (offline vector embeddings)
- **Database & Integrations**: Google Sheets API (`gspread`), `python-docx`
- **Email Service**: Python `smtplib` with MIME HTML templates
- **Frontend Framework**: Next.js 15 (React 19, TypeScript)
- **Styling**: Vanilla CSS with Tailwind CSS v4, Lucide React icons

---

## Repository Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application endpoints & server startup
│   ├── agent_engine.py      # Core AI agent logic, intent routing & refund workflow
│   ├── config.py            # Settings & environment variable configuration
│   ├── services/
│   │   ├── chroma_service.py # Vector store management for chat & policy RAG
│   │   ├── email_service.py  # SMTP & HTML email generation service
│   │   ├── policy_service.py # Word document (.docx) parsing & indexing
│   │   └── sheets_service.py # Google Sheets API & CSV data provider
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages and global styles
│   │   ├── components/      # Chat interface & header components
│   │   ├── lib/             # API client utilities
│   │   └── types/           # TypeScript interface definitions
│   └── package.json         # Node.js dependencies & scripts
├── .gitignore               # Git ignore rules
├── LICENSE                  # MIT License
└── README.md                # Project documentation
```

---

## Quick Start Guide

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm
- Google Gemini API Key (optional, for LLM response generation)
- Google Service Account Credentials JSON (optional, for live Google Sheets integration)

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

5. **Start the FastAPI server**:
   ```bash
   python main.py
   ```
   The backend API will run at `http://localhost:8000`.

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and service integration status |
| `POST` | `/chat` | Submit a customer query to the AI Agent Engine |
| `GET` | `/chat/history/{session_id}` | Retrieve chat message history for a session |
| `GET` | `/chat/sessions` | List all stored chat sessions |
| `GET` | `/products` | Fetch current product catalog |
| `GET` | `/orders` | Fetch customer orders database |
| `GET` | `/logs` | Fetch interaction and refund logs |
| `POST` | `/policy/upload` | Upload and vector-index a new `.docx` policy file |
| `POST` | `/policy/reindex` | Trigger policy re-indexing into ChromaDB |
