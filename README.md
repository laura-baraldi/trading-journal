# Trading Journal

A full-stack trading journal for recording trades, managing trading accounts, analysing performance and visualising results over time.

Built with **Next.js, React, TypeScript, FastAPI, Supabase and PostgreSQL**. The application includes authentication, CSV import, server-side pagination, performance analytics, a monthly trading calendar, automated testing and a public demo.

## Live Demo

**[Try the live demo](https://trading-journal-puce-one.vercel.app)**

From the login page, select **Try demo** to access a pre-populated trading account without creating an account. The demo contains sample trades across multiple instruments and supports the main application workflows.

The demo uses a shared authenticated Supabase account. Its data is automatically restored after periods of inactivity, allowing visitors to create, edit and delete demo data without permanently changing the initial dataset.

---

## Why I Built This

Tracking trades manually can make it difficult to understand what is working, what is not, and how performance changes over time.

The project started as a Python command-line application for logging trades, calculating R-multiples and reviewing aggregate statistics. As the requirements grew to include multiple accounts, real P/L tracking, persistent data and performance visualisation, it evolved into the full-stack application it is today.

The original CLI is retained in `legacy-cli/` as a record of that progression.

## Features

### Trading and account management

- Supabase authentication and protected API endpoints
- Multiple trading accounts with account CRUD operations
- Trade creation, editing and deletion
- Long and short positions
- Entry and exit timestamps, trade-date validation and account-level organisation
- Automatic R-multiple calculation and P/L tracking

### Import and data management

- CSV trade import with automatic delimiter detection
- Automatic mapping of common broker column names
- Numeric and datetime format normalisation
- Row-level validation and structured import errors
- Bulk persistence after successful validation
- Server-side trade pagination (20 records per page)

### Analytics and visualisation

- Aggregate trading statistics and performance charts
- R-multiple and P/L analysis
- Preset date filters (all time, last 30 days, last 90 days) and custom date ranges
- Monthly trading calendar with daily P/L, R-multiple and trade-count summaries
- Backend aggregation across the complete filtered dataset, not only the currently displayed page

### Security and reliability

- User-scoped database queries and PostgreSQL Row Level Security (RLS)
- Account ownership checks before trade persistence
- API rate limiting with SlowAPI
- Per-user rate limits for authenticated endpoints and IP-based limits for public demo login
- Frontend and backend validation
- Controlled API error responses
- Automated frontend, backend, integration and browser end-to-end tests
- GitHub Actions workflows for CI, E2E tests and scheduled demo resets
- Responsive desktop and mobile interface

---

## Tech Stack

| Area                        | Technologies                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------- |
| Frontend                    | Next.js 16, React 19, TypeScript, Tailwind CSS, Recharts, React DayPicker             |
| Backend                     | Python 3.11+, FastAPI, Pydantic, SlowAPI, python-dotenv                               |
| Database and authentication | Supabase Auth, Supabase JavaScript and Python clients, PostgreSQL, Row Level Security |
| Backend testing             | Pytest, pytest-cov, FastAPI `TestClient`                                              |
| Frontend testing            | Vitest, React Testing Library, jsdom, V8 coverage                                     |
| End-to-end testing          | Playwright                                                                            |
| Tooling and deployment      | Git, GitHub Actions, Vercel, Supabase CLI, Docker, ESLint, npm                        |

---

## Architecture

```text
┌──────────────────────────────┐
│        Next.js frontend      │
│                              │
│ React · TypeScript · Charts  │
└──────────────┬───────────────┘
               │
               │ HTTP requests + Bearer token
               ▼
┌──────────────────────────────┐
│        FastAPI backend       │
│                              │
│ Routers · Auth · Pydantic    │
│ Analytics · CSV processing   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        Data-access layer     │
│                              │
│ Accounts · Trades · Queries  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           Supabase           │
│                              │
│ Auth · PostgreSQL · RLS      │
└──────────────────────────────┘
```

The frontend communicates with FastAPI for application data. The backend is organised into dedicated routers, Pydantic schemas and database modules:

- **Routers** handle HTTP endpoints and coordinate application operations.
- **Schemas** validate request and response data.
- **Database modules** isolate Supabase persistence and query logic.
- **Authentication** verifies Supabase access tokens before protected operations.
- **Business logic** handles calculations, CSV processing and data aggregation.

Authenticated requests include the user's Supabase bearer token. FastAPI verifies the token and scopes database operations to the authenticated user. PostgreSQL Row Level Security provides an additional database-level protection layer.

---

## Authentication and Data Isolation

Authentication is handled by Supabase Auth. The frontend sends the current user's access token with protected API requests, and the backend verifies the token before accessing account or trade data.

Database operations are scoped by the authenticated user ID. When creating a trade, the backend also verifies that the selected account belongs to that user. If the account does not exist or belongs to another user, the request is rejected with `404 Not Found`.

PostgreSQL Row Level Security adds another layer of isolation at database level. Supabase integration tests use separate test users to verify that one user cannot access or modify another user's data.

This means data isolation is enforced at both the application and database layers.

---

## CSV Import

Authenticated users can select an account and import trade history from a CSV file. The importer is designed to handle exports with different column names and formatting rather than relying on one fixed broker template.

The backend performs the import in stages:

1. Validates the uploaded file and detects its delimiter.
2. Maps common broker column names to the journal's trade fields.
3. Detects and normalises numeric and datetime formats.
4. Validates each row and calculates R when a stop loss is present.
5. Persists the validated trades in a bulk operation.

Supported formats include dot and comma decimal separators, common currency symbols, ISO and broker datetime formats, mixed datetime formats and optional stop-loss values.

If required columns are missing or ambiguous, or if a row contains invalid data, the import is rejected before any trades are saved. The API returns structured error details identifying the affected row, column and field. The selected account is checked against the authenticated user before persistence.

---

## Performance Analytics, Filtering and Pagination

The journal evaluates performance using both monetary P/L and R-multiple.

R-multiple expresses a trade's result relative to its original risk, making trades with different position sizes and monetary values more comparable.

For a long trade:

```text
R = (exit - entry) / (entry - stop)
```

For a short trade:

```text
R = (entry - exit) / (stop - entry)
```

The dashboard provides aggregate statistics and a chronological performance chart. Users can analyse all available data, the last 30 days, the last 90 days or a custom date range.

### Complete analytics with paginated history

Trade history is paginated on the server and returns 20 records per page. Dashboard statistics, however, are calculated across the complete selected dataset—not only the trades currently visible on the page or the recent trades shown on the dashboard.

The backend retrieves the fields required for analytics in bounded batches, calculates the aggregate results and returns them to the frontend. This keeps the statistics complete without requiring the browser to load the entire trade history.

The selected date range is applied consistently to dashboard statistics, chart data, recent trades and the full trade-history page. Changing the selected account or date range resets pagination to the first page.

---

## Monthly Trading Calendar

The dashboard includes a monthly calendar built with React DayPicker. It summarises trading activity for the selected account and makes daily performance patterns easier to review.

Each trading day can display:

- Total P/L
- Number of trades
- Total R-multiple, when available

Profitable and losing days use distinct visual states, and users can navigate between months without leaving the dashboard.

Calendar aggregation is performed by the FastAPI backend for the complete requested month. The database layer retrieves the fields needed for the calculation in bounded batches, and the frontend receives daily aggregate values through a protected `/calendar` endpoint rather than calculating them from a partial trade list.

Calendar data refreshes when the selected account or month changes and after a trade is created, edited or deleted.

---

## Demo System

The public demo allows visitors to explore the application without registering. The login page exposes a **Try demo** action, which requests a demo session from the FastAPI backend.

Demo account credentials remain server-side and are never exposed through `NEXT_PUBLIC_*` environment variables.

```text
Visitor
   ↓
Try demo
   ↓
Next.js frontend
   ↓
POST /demo-login
   ↓
FastAPI backend
   ↓
Supabase Auth
   ↓
Demo session
```

The demo account starts with a pre-populated trading account and sample trades covering:

- XAUUSD, EURUSD, GBPUSD and NAS100
- Long and short positions
- Winning, losing and breakeven trades

### Activity tracking and rate limiting

The public `/demo-login` endpoint is rate-limited by client IP because the visitor is not authenticated yet. Once the demo session is created, protected requests are authenticated normally and use the demo user's ID for per-user rate limiting.

Protected API requests made by the demo user update a `demo_state` record containing the latest activity timestamp. This prevents the shared dataset from being reset while the demo has recently been in use.

### Automatic and manual reset

A GitHub Actions workflow runs the demo reset script every hour. The script:

1. Authenticates as the demo user.
2. Reads the latest demo activity.
3. Checks whether the account has been inactive for at least 30 minutes.
4. Skips the reset if the demo was recently active.
5. Otherwise removes the existing demo trades and accounts.
6. Recreates the original demo account.
7. Generates and inserts the 120 sample trades.

The workflow can also be triggered manually through `workflow_dispatch`. An authorised `force_reset` input can bypass the inactivity check and immediately restore the demo dataset. When `force_reset` is disabled, the regular inactivity check remains in place.

Automatic and manual resets use the same dataset generation and restoration logic.

---

## Validation and API Error Handling

Validation is performed at more than one layer. The frontend provides immediate feedback and prevents incomplete forms from being submitted, but the backend independently validates incoming data with FastAPI and Pydantic. The API does not rely on the frontend to send valid values.

Examples of backend validation include:

- Required entry and exit dates
- Exit date cannot be before entry date
- Valid trade direction
- Non-empty trade symbol
- Required account name
- Required currency
- Required starting balance

The backend also converts authentication, resource, rate-limit and database failures into controlled HTTP responses.

| Situation                                  | Response                  |
| ------------------------------------------ | ------------------------- |
| Invalid or expired token                   | `401 Unauthorized`        |
| Missing or inaccessible resource           | `404 Not Found`           |
| Rate limit exceeded                        | `429 Too Many Requests`   |
| Database or authentication service failure | `503 Service Unavailable` |

SlowAPI handles rate-limit violations centrally. Database queries pass through a centralised execution helper; dependency failures are converted into `DatabaseError` and handled as `503 Service Unavailable` responses.

This keeps API errors predictable and avoids exposing raw dependency errors to the frontend.

---

## Automated Testing

Testing covers individual units, API behaviour, database security and complete browser workflows.

### Backend — Pytest

Backend tests cover:

- Bearer-token handling and authentication
- Demo authentication and activity tracking
- API endpoints and request validation
- API rate limiting, per-user isolation and IP fallback
- Account and trade CRUD operations
- Account ownership checks
- R-multiple calculations
- Database transformations and error handling
- Demo dataset generation and reset behaviour
- CSV parsing, column mapping and value normalisation
- CSV row validation and bulk persistence
- Server-side trade pagination
- Date-range query validation and filtering
- Dashboard aggregation across the complete dataset and batched trade metrics
- Monthly calendar aggregation and batched database loading

External dependencies are mocked in unit tests where appropriate.

### Supabase integration tests

Separate integration tests communicate with Supabase and cover:

- Real database connectivity
- Row Level Security
- Cross-user data isolation

These tests require the relevant test-user credentials and database configuration.

### Frontend — Vitest and React Testing Library

Frontend tests cover:

- Authentication flows and demo login
- Page behaviour, forms and user interactions
- API requests and error/loading states
- Account and trade management
- Statistics and chart behaviour
- Reusable and responsive UI components
- CSV import success, loading and error states
- Date preset and custom-range interactions
- Filtered dashboard and trade-history requests
- Pagination reset when filters change
- Calendar rendering, month navigation and responsive behaviour
- Calendar refresh after trade changes

### End-to-end — Playwright

Playwright tests exercise the running application through a real browser, covering complete flows across the frontend, backend and database.

The E2E suite covers:

- Public demo login
- Account creation and deletion
- Trade creation, editing and deletion
- Valid CSV import
- Invalid CSV rejection
- Manual trade-form validation
- Dashboard statistics using deterministic trade data

The dashboard statistics test creates an isolated account and known trades, then verifies exact values such as total trade count, win rate, P/L, account balance, total R and average R. This checks the full path from browser interaction through the API and database to the rendered dashboard.

#### Shared browser authentication state

Authenticated E2E tests use a shared Playwright `storageState` generated by a dedicated setup project. The setup authenticates once and stores the browser session, avoiding repeated calls to the rate-limited public demo-login endpoint.

The public demo-login flow is tested separately from an unauthenticated browser state, so the login process itself is still exercised.

E2E tests create temporary accounts with unique names and clean them up after execution. This keeps assertions deterministic and reduces dependence on existing demo data.

The generated browser authentication state is stored in:

```text
frontend/playwright/.auth/
```

This directory is ignored by Git because it can contain active session data and must not be committed.

### Coverage

During development, the frontend and backend unit-test suites reached **100% code coverage**. Coverage is used as a development signal alongside behavioural, integration and end-to-end tests—not as a replacement for them.

---

## Continuous Integration

GitHub Actions runs automated checks on pushes and pull requests.

### Backend workflow

- Installs Python dependencies
- Runs the backend test suite
- Collects coverage, including branch coverage
- Runs Supabase integration and RLS tests when the required secrets are configured

### Frontend workflow

- Installs dependencies with `npm ci`
- Runs ESLint
- Runs Vitest tests with coverage
- Creates a production Next.js build

### End-to-end workflow

- Runs on Ubuntu
- Installs Python and frontend dependencies
- Installs Playwright browsers and required system dependencies
- Starts the FastAPI backend and Next.js frontend
- Authenticates the shared demo session through the Playwright setup project
- Runs the Chromium E2E suite

Supabase and demo credentials are provided through GitHub Actions secrets rather than committed to the repository.

A separate scheduled workflow runs the demo reset script and restores the shared demo dataset when it has been inactive.

---

## Repository Structure

```text
trading-journal/
│
├── backend/
│   ├── api.py                 # FastAPI setup, middleware and router registration
│   ├── auth.py                # Authentication and demo activity helpers
│   ├── rate_limit.py          # SlowAPI configuration and rate-limit keys
│   ├── calculations.py        # R, dashboard and calendar calculations
│   ├── routes/                # FastAPI route modules
│   ├── schemas/               # Pydantic request and response models
│   ├── database/              # Supabase data-access layer
│   ├── imports/               # CSV parsing, mapping and validation
│   ├── demo.py                # Demo dataset generation and reset logic
│   ├── tests/                 # Unit and integration tests
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── app/                   # Pages and page tests
│   ├── components/            # Reusable UI components and tests
│   ├── lib/                   # API and Supabase configuration
│   ├── e2e/                   # Playwright tests and CSV fixtures
│   └── playwright.config.ts
│
├── supabase/
│   └── migrations/            # Database schema and RLS migrations
│
├── legacy-cli/                # Original command-line implementation
│
├── .github/
│   └── workflows/             # Backend, frontend, E2E and demo-reset workflows
│
├── .env.example
└── README.md
```

---

## Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/laura-baraldi/trading-journal.git
cd trading-journal
```

### 2. Database (optional local setup)

The database schema, constraints and Row Level Security policies are versioned in `supabase/migrations/`.

Docker and the Supabase CLI are required only to recreate and test the database locally. They are not needed when connecting to a hosted Supabase project.

Start the local Supabase database:

```bash
npx supabase db start
```

The migration files are applied in timestamp order.

Stop the local Supabase stack:

```bash
npx supabase stop
```

On Windows PowerShell, use `npx.cmd` instead of `npx`.

### 3. Backend

From the project root:

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_publishable_key
CORS_ORIGINS=http://localhost:3000

# Required only for public demo functionality and authenticated E2E tests
DEMO_EMAIL=
DEMO_PASSWORD=
```

Demo credentials are only needed when running the public demo functionality and authenticated E2E tests. They must remain server-side and must never be exposed through frontend environment variables.

Start FastAPI:

```bash
python -m uvicorn api:app --reload
```

Backend URL: `http://127.0.0.1:8000`

### 4. Frontend

In a separate terminal, from the project root:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Start Next.js:

```bash
npm run dev
```

Frontend URL: `http://localhost:3000`

---

## Running Tests Locally

### Backend

From `backend/`:

```bash
python -m pytest tests
```

With coverage:

```bash
python -m pytest tests --cov=api --cov=auth --cov=database --cov=calculations --cov=demo --cov=imports --cov=routes --cov=schemas --cov=rate_limit --cov-branch --cov-report=term-missing
```

Supabase integration tests are located in `backend/tests/integration/` and require the relevant test-user credentials and database configuration.

### Frontend

From `frontend/`:

```bash
npm test -- --run
npm test -- --run --coverage
npm run lint
npm run build
```

### Playwright end-to-end tests

Both FastAPI and Next.js must be running. From `frontend/`:

```bash
npx playwright test --project=chromium
```

On Windows PowerShell:

```powershell
npx.cmd playwright test --project=chromium
```

The Chromium project runs the authentication setup first and reuses the generated browser session for authenticated tests.

To test the public demo-login flow separately from an unauthenticated browser state:

```bash
npx playwright test --project=demo-login
```

On Windows PowerShell:

```powershell
npx.cmd playwright test --project=demo-login
```

To open the latest Playwright HTML report:

```bash
npx playwright show-report
```

The generated browser state is stored in `frontend/playwright/.auth/`. It is ignored by Git and must not be committed.

---

## Deployment

The frontend and backend are deployed as separate Vercel projects. Supabase provides authentication and PostgreSQL.

```text
Vercel
├── Next.js frontend
└── FastAPI backend

Supabase
├── Authentication
└── PostgreSQL
```

Production configuration is supplied through environment variables. Sensitive values, including demo credentials, are stored in server-side deployment settings and GitHub Actions secrets rather than hardcoded or committed to the repository.

---

## Project Evolution

The project grew incrementally from a small Python CLI into a full-stack application. Each iteration introduced a new requirement or architectural layer.

```text
Python CLI
    ↓
Local file persistence
    ↓
Supabase database
    ↓
FastAPI backend
    ↓
Next.js frontend
    ↓
Authentication and multiple accounts
    ↓
Charts and performance statistics
    ↓
Validation and automated tests
    ↓
RLS integration testing
    ↓
Deployment and public demo
    ↓
Automatic CSV import
    ↓
Server-side pagination and date filters
    ↓
Monthly trading calendar
    ↓
API rate limiting
    ↓
Playwright end-to-end testing
```

### From CLI to web application

The first version was a Python command-line application. It handled adding, viewing, editing and deleting trades, calculating R-multiples, generating aggregate statistics and validating input. Trades were initially stored locally.

As the project grew, local persistence was replaced with Supabase. This introduced remote storage, CRUD operations, generated IDs, database records and relationships.

FastAPI was then introduced to separate HTTP endpoints, authentication, validation, calculations and database operations from the user interface. As the backend grew, route handlers, Pydantic schemas and persistence logic were organised into dedicated modules.

The command-line interface was replaced by a Next.js, React and TypeScript frontend, introducing reusable components, application state, controlled forms, asynchronous requests, authentication state, responsive layouts, charts and loading/error states.

### Multi-user accounts and analytics

Supabase Auth transformed the application from a single-user journal into a multi-user system. User-owned records, bearer-token verification and Row Level Security were added to protect account and trade data.

Multiple trading accounts were introduced so users could organise trades separately and analyse performance per account. Account data includes details such as account name, starting balance, currency, broker and account type.

The application then expanded beyond trade storage with P/L tracking, R-multiple analytics, performance charts, date filters and the monthly calendar.

### Reliability and testing

Validation was progressively added to the frontend and backend. Database calls were centralised so dependency failures could be converted into predictable API responses.

Testing expanded from individual functions and components to API tests, Supabase integration tests, RLS checks and Playwright browser workflows. GitHub Actions now runs the relevant checks automatically.

### Import, scale and demo access

CSV import was added to support broker exports with different formats. Dedicated backend modules handle file reading, column mapping, normalisation and row validation before bulk persistence.

As trade histories grew, server-side pagination and bounded analytics queries were introduced. The monthly calendar moved daily aggregation to the backend, and SlowAPI rate limiting was added to protect public and authenticated endpoints.

Finally, the public demo system made it possible to evaluate the deployed application without registration. Activity tracking and scheduled GitHub Actions resets keep its shared sample dataset available for visitors.

---

## What I Learned

Building the project provided practical experience across the full application lifecycle.

### Software design

- Separating user interface, API routing, authentication, validation, business logic, persistence, testing and deployment
- Refactoring a growing application into modules with clearer responsibilities
- Understanding how requirements influence architecture as a project evolves

### Backend development

- REST APIs and HTTP request/response handling
- FastAPI routers and dependency injection
- Bearer-token authentication
- Pydantic request and response models
- Server-side validation and exception handling
- API rate limiting and middleware
- Database access and environment-based configuration

### Frontend development

- React components, props and state
- Event handlers and controlled forms
- Asynchronous API requests
- Conditional rendering and loading/error states
- TypeScript and responsive layouts
- Charts and data visualisation

### Databases and security

- Persistent relational data
- CRUD operations and user-owned records
- Supabase authentication
- PostgreSQL Row Level Security
- Cross-user isolation and integration testing

### Testing and debugging

- Unit and component testing
- Mocking external dependencies
- API and integration testing
- Parameterised tests
- Rate-limit behavioural testing
- Browser end-to-end testing
- Shared browser authentication state
- Test-data isolation and cleanup
- Deterministic E2E assertions
- CI execution and code coverage

A significant part of the work involved debugging interactions between the frontend, backend, authentication layer and database rather than treating each layer independently.

---

## Current Status and Future Improvements

The original CLI has been superseded by the full-stack web application. The current version includes authentication, account and trade management, CSV import, server-side pagination, date filtering, backend analytics, charts, a monthly calendar, validation, RLS, API rate limiting, automated tests, CI, deployment and public demo access.

Potential future improvements include:

- More advanced trading analytics and account statistics
- Calendar day details and trade drill-down
- CSV export
- Further dashboard visualisation improvements
- Production observability and structured logging
- Broader cross-browser E2E coverage
- Shared rate-limit storage for multi-instance deployments
- Performance improvements for larger datasets
