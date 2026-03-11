
# Sales Insight Automator

## Project Goal
A secure AI-powered application where a user uploads a CSV/XLSX sales file, the system analyzes the data, generates an executive sales summary using an LLM (Google Gemini), and emails the summary to a recipient.

## Architecture Diagram

```mermaid
graph TD
    User[User] --> |Upload File, Enter Email| Frontend(Next.js App)
    Frontend --> |API Request (X-API-KEY)| Backend(FastAPI)
    Backend --> |Process Data| Pandas(Data Processing)
    Backend --> |Structured Analytics| Gemini(Google Gemini API)
    Gemini --> |Narrative Summary| Backend
    Backend --> |Send Email (SMTP)| EmailServer(SMTP Server)
    EmailServer --> Recipient[Recipient]

    subgraph Data Flow
        Frontend --&gt; Backend: /upload (CSV/XLSX)
        Frontend --&gt; Backend: /generate-summary
        Frontend --&gt; Backend: /send-email
    end

    subgraph Backend Services
        Backend --&gt; Redis[Redis: Background Tasks/Rate Limiting]
    end

    subgraph Security
        User -- API Key Auth --> Backend
        User -- Rate Limiting --> Backend
        Frontend -- CORS --> Backend
    end
```

## Tech Stack

*   **Frontend:** Next.js, TailwindCSS
*   **Backend:** FastAPI (Python)
*   **AI:** Google Gemini API
*   **Email:** SMTP (compatible with Gmail)
*   **Data Processing:** pandas
*   **Containerization:** Docker, docker-compose
*   **CI/CD:** GitHub Actions
*   **Deployment Targets:** Vercel (frontend), Render (backend)

## Features

### Frontend
*   Drag & drop file upload
*   Email input field
*   Submit button
*   Progress indicator
*   Success / error messages
*   API integration with backend

### Backend API Endpoints
*   `POST /upload`: Accepts CSV or XLSX, validates file size (<10MB), validates file type, parses with pandas.
*   `POST /generate-summary`: Computes analytics (total revenue, top region, best product category, cancellation rate), sends structured analytics to Gemini, receives narrative summary.
*   `POST /send-email`: Sends summary via SMTP.
*   `GET /health`: System health check.

### Security
*   API key authentication (`X-API-KEY` header)
*   Rate limiting (5 requests/minute)
*   Strict CORS policy
*   File validation
*   Input sanitization
*   Structured logging

### AI Engine
*   Prompts Gemini with structured analytics to produce: executive summary, key insights, warnings/anomalies.

## Project Structure

```
sales-insight-automator/
├── frontend/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── file_processor.py
│   │   │   ├── ai_summary_service.py
│   │   │   └── email_service.py
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── api_key_auth.py
│   │   │   └── rate_limiter.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── sales_data.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── logger.py
│   │   └── __init__.py
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
└── .github/
    └── workflows/
        └── ci-cd.yml
```

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/sales-insight-automator.git
    cd sales-insight-automator
    ```

2.  **Environment Variables:**
    Create a `.env` file in the project root by copying `.env.example` and filling in the values:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file with your actual credentials:
    *   `GEMINI_API_KEY`: Your Google Gemini API key.
    *   `SMTP_USERNAME`: Your email address for sending summaries (e.g., your Gmail address).
    *   `SMTP_PASSWORD`: Your email password or app-specific password (for Gmail, you'll need to generate an App Password).
    *   `SMTP_SERVER`: Your SMTP server (e.g., `smtp.gmail.com`).
    *   `SMTP_PORT`: Your SMTP port (e.g., `587` for TLS).
    *   `API_KEY`: A strong, unique API key for securing your backend endpoints.
    *   `NEXT_PUBLIC_BACKEND_URL`: The URL where your backend will be accessible (e.g., `http://localhost:8000` for local development).

3.  **Docker Compose (Local Development):**
    Ensure Docker is installed and running on your machine. Then, from the project root:
    ```bash
    docker-compose up --build
    ```
    This will build the backend Docker image, start the backend service on `http://localhost:8000`, and also start a Redis instance.

## Running the Backend (without Docker Compose)

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run the FastAPI application:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will be available at `http://localhost:8000`.

## Running the Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    # or yarn install
    ```

3.  **Run the Next.js development server:**
    ```bash
    npm run dev
    # or yarn dev
    ```
    The frontend will be available at `http://localhost:3000`.

## API Documentation (Swagger/OpenAPI)

Once the backend is running, you can access the interactive API documentation at:

*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`

## Security Explanation

*   **API Key Authentication:** All sensitive backend endpoints require an `X-API-KEY` header. This key is configured in the `.env` file and validated against a securely stored key.
*   **Rate Limiting:** To prevent abuse and ensure fair usage, a rate limiter is implemented using Redis, allowing a maximum of 5 requests per minute per IP address.
*   **CORS Policy:** A strict Cross-Origin Resource Sharing (CORS) policy is applied to the backend, only allowing requests from the specified frontend origin.
*   **File Validation:** Uploaded files are strictly validated for type (CSV/XLSX) and size (<10MB) to prevent malicious uploads and resource exhaustion.
*   **Input Sanitization:** Although FastAPI provides good default protections, further input sanitization can be implemented in specific service layers if needed to prevent injection attacks.
*   **Structured Logging:** All significant events and errors are logged using structured logging, facilitating easier monitoring, debugging, and security auditing.

## CI/CD with GitHub Actions

The `.github/workflows/ci-cd.yml` file defines a GitHub Actions workflow that runs on every pull request to the `main` branch. This workflow includes steps for:

*   Installing dependencies
*   Linting code (e.g., with `flake8` for Python, `eslint` for JavaScript)
*   Running tests (e.g., `pytest` for Python)
*   Building the Docker image for the backend

This ensures code quality and catches potential issues early in the development cycle.
