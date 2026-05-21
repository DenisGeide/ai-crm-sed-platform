# Screenshot Plan

Use this checklist before publishing screenshots.

## Safety Rules

Blur or remove:

- real client names;
- emails, phone numbers, addresses;
- order IDs if they can identify a real person;
- access tokens, API keys, cookies, session IDs;
- server IPs/domains if private;
- database credentials;
- payment provider identifiers;
- internal private URLs.

## Required Screenshots

### 1. Architecture

File:

```text
screenshots/architecture-overview.png
```

Content:

- FastAPI backend;
- PostgreSQL + pgvector;
- Redis;
- WebSocket;
- worker;
- local Ollama/LLM;
- tenant storage.

### 2. CRM Dashboard

File:

```text
screenshots/crm-dashboard.png
```

Content:

- ticket list;
- statuses;
- client card;
- filters or analytics.

### 3. Client Chat / Widget

File:

```text
screenshots/client-chat.png
```

Content:

- client message;
- AI answer;
- clear next step.

### 4. Document Center / PDF Workflow

File:

```text
screenshots/document-center.png
```

Content:

- generated PDF/document;
- status;
- version;
- protected download/action.

### 5. JSON Status Config

File:

```text
screenshots/status-json-config.png
```

Content:

- zero-code status configuration;
- document workflow states;
- no secrets.

### 6. Tests

File:

```text
screenshots/tests-135-passed.png
```

Content:

- terminal/CI output with 135+ passed tests;
- project path can be visible;
- no secrets in logs.

### 7. Code Snippet

File:

```text
screenshots/code-fastapi-rbac-rag.png
```

Content:

- readable code;
- no secrets;
- one focused example, not a huge wall of code.

## Optional Screenshots

- `screenshots/metrics.png`
- `screenshots/worker-logs.png`
- `screenshots/protected-download.png`
- `screenshots/docker-services.png`

