<div align="center">

# WCAG Accessibility Evaluation Platform

**A comprehensive, enterprise-grade accessibility evaluation platform implementing the W3C WCAG-EM methodology**

</div>

---

## Overview

The WCAG Accessibility Evaluation Platform is a full-featured web application for conducting comprehensive accessibility audits following the [W3C Website Accessibility Conformance Evaluation Methodology (WCAG-EM)](https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/).

It combines automated testing with axe-core, manual review workflows, and detailed reporting to help organizations achieve and maintain WCAG 2.1 Level AA compliance.

### Why This Platform?

- **Standards-Compliant**: Implements the official W3C WCAG-EM methodology
- **Real-time Progress**: SSE-powered live updates for all long-running tasks
- **Multi-tenant Architecture**: Full organization isolation with PostgreSQL RLS
- **Role-Based Access**: Granular permissions for teams of all sizes
- **Longitudinal Tracking**: Monitor accessibility trends over time
- **Multiple Export Formats**: PDF, CSV, and W3C EARL reports

---

## Features

### Core Capabilities

| Feature                    | Description                                                            |
| -------------------------- | ---------------------------------------------------------------------- |
| **Multi-tenancy**          | Complete organization isolation using PostgreSQL Row-Level Security    |
| **RBAC**                   | 4 roles (Owner, Auditor, Reviewer, Viewer) with granular permissions   |
| **WCAG-EM Sampling**       | Structured + random page sampling per methodology Step 3               |
| **Disability Profiles**    | 4 profiles (Blind, Low Vision, Motor, Cognitive) with priority mapping |
| **Longitudinal Dashboard** | Trend analysis, regression detection, verdict history                  |
| **Real-time SSE**          | Server-Sent Events for live task progress (no polling)                 |

### WCAG-EM Workflow

1. **Define Scope** — Set target URL, conformance level, and evaluation parameters
2. **Explore Website** — Playwright-based crawler discovers pages (robots.txt aware)
3. **Select Sample** — WCAG-EM Step 3 algorithm selects representative pages
4. **Audit Sample** — axe-core engine tests all WCAG 2.1 A/AA criteria
5. **Report Findings** — Generate PDF, CSV, or EARL conformance reports

### Report Formats

- **PDF Report** — WCAG-EM conformance report (WeasyPrint generated)
- **CSV Export** — Machine-readable findings for issue trackers
- **EARL JSON-LD** — W3C Evaluation and Report Language format

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/antaripdebgupta/accessibility-platform.git
cd accessibility-platform

# Create environment file
cp .env.example .env

# Start all services
make dev

# Verify installation
curl http://localhost/api/v1/health
# Expected: {"status":"ok"}
```

### Access the Application

| Service                | URL                           |
| ---------------------- | ----------------------------- |
| **Frontend**           | http://localhost              |
| **API Docs (Swagger)** | http://localhost/api/v1/docs  |
| **API Docs (ReDoc)**   | http://localhost/api/v1/redoc |
| **MinIO Console**      | http://localhost:9001         |

### Development Credentials

In development mode, use the bypass token for API access:

```bash
Authorization: Bearer dev-bypass-token-local-only
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Vue 3 SPA)                       │
│  ├─ Firebase Auth SDK          ├─ Pinia State Management        │
│  └─ EventSource API (SSE)      └─ Tailwind CSS                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx Reverse Proxy                      │
│  ├─ /api/* → FastAPI Backend                                    │
│  └─ /* → Vue Frontend (static assets)                           │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   FastAPI    │        │  PostgreSQL  │        │    MinIO     │
│   Backend    │        │  + RLS       │        │   Storage    │
│  (Async)     │        │  (Multi-     │        │  (Reports,   │
│              │        │   tenant)    │        │  Screenshots)│
└──────┬───────┘        └──────────────┘        └──────────────┘
       │
       ▼
┌──────────────┐                ┌──────────────┐
│    Redis     │───────────────▶│   Celery     │
│  (Broker +   │                │   Worker     │
│   Pub/Sub)   │                │ (Playwright, │
└──────────────┘                │   axe-core)  │
                                └──────────────┘
```

### Tech Stack

**Backend**

- FastAPI (async Python 3.12)
- PostgreSQL 16 with Row-Level Security
- Redis 7.2 for task queue & SSE pub/sub
- Celery for distributed task processing
- Playwright for browser automation
- Firebase Admin SDK for authentication

**Frontend**

- Vue 3 (Composition API)
- Pinia state management
- Vue Router
- Tailwind CSS
- Firebase Auth SDK

**Infrastructure**

- Docker Compose orchestration
- Nginx reverse proxy
- MinIO S3-compatible storage

---

## Development Commands

```bash
# Start development environment
make dev

# View logs
make logs

# Stop services
make down

# Reset database
make reset-db

# Run migrations
make migrate

# Seed WCAG criteria & dev user
make seed

# Enter API container shell
make shell-api

# Enter PostgreSQL shell
make shell-db
```

---

## Feature

| Category           | Feature                  |
| ------------------ | ------------------------ |
| **Authentication** | Firebase Auth            |
| **Multi-tenancy**  | Organization Isolation   |
| **Security**       | PostgreSQL RLS           |
| **Access Control** | RBAC (4 roles)           |
| **Invitations**    | Email-based invites      |
| **WCAG-EM**        | Full 5-step workflow     |
| **Crawler**        | Playwright spider        |
| **Sampling**       | WCAG-EM Step 3 algorithm |
| **Scanner**        | axe-core integration     |
| **Profiles**       | 4 disability profiles    |
| **Dashboard**      | Longitudinal trends      |
| **Real-time**      | SSE task progress        |
| **Reports**        | PDF/CSV/EARL exports     |
| **Storage**        | MinIO integration        |
| **Audit**          | Full audit logging       |

## Acknowledgments

- [W3C WAI](https://www.w3.org/WAI/) for WCAG guidelines and WCAG-EM methodology
- [Deque Systems](https://www.deque.com/) for the axe-core accessibility engine
- [Playwright](https://playwright.dev/) for reliable browser automation
