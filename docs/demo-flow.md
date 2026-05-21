# Demo Flow

This demo shows an end-to-end customer support and document workflow inside the AI CRM + SED Platform.

The scenario demonstrates how a client request moves from chat to AI processing, CRM handoff, document generation, operator workflow and operational monitoring.

## 1. Client Request

A customer starts a conversation in the web chat/widget and asks for help with an order or official document.

Example request:

```text
I want to place an order and need an official document.
```

The system collects the required context, keeps the conversation history and prepares the request for further processing.

Demonstrated capabilities:

- client-facing chat widget;
- message history and client context;
- AI-assisted data collection;
- structured request handoff to CRM.

## 2. AI Classification And RAG Reply

The AI pipeline classifies the request, extracts the expected action and prepares a contextual answer using the tenant knowledge base.

If the request can be answered automatically, the client receives a response.  
If operator action is required, the system escalates the conversation into CRM.

Demonstrated capabilities:

- intent classification;
- action extraction;
- RAG response from a knowledge base;
- local LLM/Ollama pipeline;
- fallback behavior if AI is unavailable;
- tenant-specific configuration.

## 3. CRM Ticket Workflow

The request appears in the CRM dashboard as a ticket with client data, priority, status, comments and message history.

An operator can take the ticket into work, continue the conversation and update the request state.

Demonstrated capabilities:

- CRM ticket creation;
- client card;
- operator workflow;
- status and priority management;
- comments and message history;
- employee role and permission model.

## 4. Document Workflow

The system generates a PDF document connected to the ticket and stores it in the document workflow.

The document can move through review, approval, versioning and archive stages.

Demonstrated capabilities:

- PDF generation;
- document versioning;
- approval workflow;
- protected/signed download links;
- relation between CRM ticket and document;
- document audit trail.

## 5. Realtime Updates And Audit

CRM events, chat updates and document actions are delivered in realtime where needed.

Important actions are stored in audit logs, so management can inspect what happened and who performed each operation.

Demonstrated capabilities:

- WebSocket realtime updates;
- Redis Pub/Sub backend;
- audit logging;
- operator activity tracking;
- operational visibility.

## 6. Configuration And White-Label Logic

The platform can be adapted for different tenants through site profiles and configuration-driven business rules.

This allows changing interface labels, statuses, document settings and employee roles without rewriting core backend logic.

Demonstrated capabilities:

- tenant-aware API;
- isolated tenant storage;
- configurable CRM/document statuses;
- white-label site profile;
- role-based access control.

## 7. Engineering Readiness

The project includes checks and infrastructure pieces needed for a production-style backend.

Demonstrated capabilities:

- `/health` and `/health/ready` endpoints;
- `/metrics` endpoint;
- background jobs with retries and DLQ;
- Docker Compose app/worker/database stack;
- backup/restore workflow;
- upload validation and protected files;
- automated test suite with 135+ passed tests.

## Demo Result

The demo shows a complete controlled workflow:

1. Customer sends a request in chat.
2. AI classifies the request and prepares a response.
3. CRM ticket is created when operator action is needed.
4. Operator works with the client context.
5. PDF document is generated and linked to the ticket.
6. Realtime events, audit logs and metrics provide operational visibility.
