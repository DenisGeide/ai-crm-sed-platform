# Demo Flow

This demo is designed for a recruiter, CTO, client or technical interviewer.

## 1. Client Chat

Show the client-facing chat or widget.

Example request:

```text
I want to place an order and need an official document.
```

What to show:

- AI reply;
- request classification;
- collected client data;
- clear handoff to CRM when operator action is required.

## 2. CRM Ticket

Open the CRM operator dashboard.

What to show:

- new ticket in the list;
- ticket status and priority;
- client card;
- message history;
- linked documents;
- operator action buttons.

## 3. Document Workflow

Show document generation and lifecycle.

What to show:

- generated PDF;
- document version;
- status transition;
- protected/signed download link;
- relation between ticket and document.

## 4. AI/RAG

Show how the system answers using a knowledge base.

What to show:

- knowledge base result;
- contextual reply;
- safe fallback if local LLM is unavailable;
- tenant-specific configuration if available.

## 5. Observability / Tests

Show engineering readiness.

What to show:

- `/health` or `/health/ready`;
- `/metrics`;
- background worker logs;
- `135+ passed` test result;
- Docker Compose services running.

## Suggested Demo Assets

- Short screen recording: 60-90 seconds.
- 5-7 screenshots.
- One architecture diagram.
- One sanitized code snippet.

