# Architecture Overview

## Purpose

AI CRM + SED Platform is designed as a modular FastAPI-based backend with CRM, chat, AI/RAG, document workflow, jobs, security and observability modules.

The core idea is to connect a customer request with the full operational lifecycle:

1. Customer message.
2. AI classification and RAG answer.
3. CRM ticket creation.
4. Operator workflow.
5. PDF/document workflow.
6. Audit and analytics.

## Backend Modules

- `crm`: tickets, clients, employees, comments, analytics, exports.
- `chat`: client chat, message history, uploads, operator workflow, WebSocket.
- `documents`: PDF generation, versions, approvals, archive, protected downloads.
- `ai`: intent/action pipeline, RAG, Ollama client, fallbacks, evaluations.
- `jobs`: background queue, retries, status lifecycle, DLQ, audit.
- `security`: auth hardening, RBAC, signed URLs, upload validation.
- `observability`: request IDs, structured logs, health/readiness, metrics.
- `config`: site profile, tenant profile, employee seed/config.

## Data Layer

The data layer is built around PostgreSQL and Alembic migrations.

Important design points:

- tenant-aware data model;
- indexed CRM lists and audit queries;
- pgvector-based knowledge search;
- persistent job/audit tables;
- document and upload metadata;
- separation between database records and protected file storage.

## AI/RAG Pipeline

The AI pipeline is separated into explicit stages:

1. Intent classification.
2. Action extraction.
3. Knowledge search.
4. Contextual reply generation.
5. Confidence scoring.
6. Escalation/operator handoff.
7. Safe fallback if LLM is unavailable.

This keeps business actions separate from simple informational answers.

## Security Baseline

The project includes:

- JWT/session authentication;
- RBAC checks;
- tenant-aware access checks;
- CORS/security headers;
- protected upload/download paths;
- signed document download URLs;
- audit logs;
- anti-XSS helpers;
- restricted production defaults.

## Deployment Model

The system is prepared for local, staging and production-like launches:

- FastAPI app service;
- worker service;
- PostgreSQL;
- Redis;
- reverse proxy/TLS layer;
- Docker Compose overlays;
- health/readiness endpoints;
- metrics endpoint;
- backup/restore scripts.

