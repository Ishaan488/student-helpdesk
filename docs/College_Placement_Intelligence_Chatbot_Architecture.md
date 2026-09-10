# College Placement Intelligence Chatbot
## Complete System Architecture and Technical Design Documentation

**Version:** 1.0  
**Status:** Architecture / Design Specification  
**Primary Goal:** Build a secure, scalable, accurate AI-powered assistant for college placement information.

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Design Principles](#3-design-principles)
4. [System Requirements](#4-system-requirements)
5. [High-Level Architecture](#5-high-level-architecture)
6. [Data Architecture](#6-data-architecture)
7. [Query Classification and Routing](#7-query-classification-and-routing)
8. [Structured Data Layer](#8-structured-data-layer)
9. [Rules Engine](#9-rules-engine)
10. [RAG and Knowledge Retrieval](#10-rag-and-knowledge-retrieval)
11. [Knowledge Graph Layer](#11-knowledge-graph-layer)
12. [Controlled Web Search](#12-controlled-web-search)
13. [Security and Authorization Architecture](#13-security-and-authorization-architecture)
14. [Guardrails](#14-guardrails)
15. [Caching and Cost Optimization](#15-caching-and-cost-optimization)
16. [LLM Architecture](#16-llm-architecture)
17. [Data Ingestion Pipeline](#17-data-ingestion-pipeline)
18. [Complete Request Lifecycle](#18-complete-request-lifecycle)
19. [Admin and Knowledge Management](#19-admin-and-knowledge-management)
20. [Database Design](#20-database-design)
21. [API Architecture](#21-api-architecture)
22. [Background Jobs](#22-background-jobs)
23. [Observability and Monitoring](#23-observability-and-monitoring)
24. [Evaluation and Testing](#24-evaluation-and-testing)
25. [Recommended Technology Stack](#25-recommended-technology-stack)
26. [Deployment Architecture](#26-deployment-architecture)
27. [Development Roadmap](#27-development-roadmap)
28. [Architecture Decisions and Tradeoffs](#28-architecture-decisions-and-tradeoffs)

---

# 1. Executive Summary

This system is an AI-powered placement intelligence platform for college students.

Students should be able to ask questions such as:

- "Am I eligible for Company X?"
- "Which companies can I apply for?"
- "What is the placement policy?"
- "What is the interview process of Company Y?"
- "Compare Company A and Company B."
- "What skills should I learn for upcoming companies?"
- "What is the latest information about Company X?"

The system must provide answers from multiple data sources while maintaining:

- High factual accuracy.
- Strict access control.
- Low LLM cost.
- Data freshness.
- Source traceability.
- Protection against information leakage.

The system is **not designed as a simple RAG chatbot**.

Instead, it is a Placement Intelligence Platform where the LLM acts primarily as an intelligent natural-language interface over deterministic systems.

## Core Architectural Principle

> Use deterministic systems for truth, retrieval systems for knowledge, authorization systems for access, and LLMs for language and reasoning.

This principle drives the entire architecture.

---

# 2. Problem Statement

College placement information exists in multiple formats and systems.

Examples include:

## Structured information

- Company name.
- Package.
- Role.
- Eligibility CGPA.
- Allowed branches.
- Maximum backlogs.
- Application deadline.
- Test date.
- Interview date.
- Selection status.

## Unstructured information

- Placement policy PDFs.
- Job descriptions.
- Circulars.
- Interview experiences.
- TPO announcements.
- Company presentations.

## Relationship information

- Students → Skills.
- Companies → Roles.
- Roles → Required Skills.
- Students → Eligibility.
- Companies → Placement Drives.

## External information

- Latest company news.
- Company products.
- Company technologies.
- Public hiring information.

The challenge is that these data types should not all be queried in the same way.

For example:

> "Which companies allow CSE students with CGPA above 7?"

This is a structured database query.

> "Explain the dream offer policy."

This is a document retrieval and explanation problem.

> "Am I eligible for Company X?"

This is a deterministic rules evaluation problem.

> "Which companies require skills that I already have?"

This is potentially a relationship or graph query.

> "What is Company X doing recently in AI?"

This may require controlled web search.

Therefore, a single vector database cannot be the architecture of the system.

---

# 3. Design Principles

## 3.1 LLM is not the source of truth

The LLM must never be considered authoritative for:

- Eligibility decisions.
- Placement rules.
- Student status.
- Official dates.
- Selection status.

The LLM receives verified information and explains it.

```text
DATABASE / RULES ENGINE = TRUTH
LLM = INTERPRETATION AND LANGUAGE
```

---

## 3.2 Retrieval should depend on the question type

```text
Structured question
        ↓
PostgreSQL

Eligibility question
        ↓
Rules Engine

Document question
        ↓
Hybrid RAG

Relationship question
        ↓
Knowledge Graph

External/current question
        ↓
Controlled Web Search
```

---

## 3.3 Authorization happens before retrieval

Restricted information should ideally never enter the LLM context.

Incorrect design:

```text
Retrieve everything
        ↓
Give to LLM
        ↓
Ask LLM not to reveal secrets
```

Correct design:

```text
Authenticate User
        ↓
Determine Permissions
        ↓
Retrieve ONLY authorized data
        ↓
LLM generates answer
```

---

## 3.4 Every answer should have evidence

The system should be able to identify the source of important factual claims.

Possible evidence:

- Database record.
- Placement policy section.
- Official circular.
- Company job description.
- Official website.

---

## 3.5 Data must be versioned

Placement policies and company criteria change.

The system must understand:

- Which version is active.
- When it became effective.
- When it expired.
- Which answers were generated from which version.

---

# 4. System Requirements

## Functional Requirements

### Student Features

- Ask placement-related questions.
- Check personal eligibility.
- View upcoming companies.
- Understand placement policies.
- Search company information.
- Compare companies.
- Get personalized recommendations.
- Access relevant documents.
- Receive source-backed answers.

### Admin/TPO Features

- Upload documents.
- Create placement drives.
- Define eligibility criteria.
- Publish or unpublish information.
- Manage visibility.
- Update policies.
- Review AI-extracted data.
- View analytics.

---

## Non-Functional Requirements

### Accuracy

Critical answers should rely on deterministic systems whenever possible.

### Security

Students must never access unauthorized placement information.

### Scalability

The architecture should support hundreds or thousands of daily queries.

### Low Cost

Simple questions should avoid expensive models.

### Observability

Every AI request should be traceable and debuggable.

---

# 5. High-Level Architecture

```text
                              ┌────────────────────┐
                              │   STUDENT / ADMIN  │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │    API Gateway     │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ Authentication    │
                              │ Authorization     │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ Input Guardrails   │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ Cache Layer        │
                              │ Redis              │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ Query Router       │
                              │ Intent Detection   │
                              └──────┬─────┬───────┘
                                     │     │
             ┌───────────────────────┼─────┼─────────────────────┐
             │                       │     │                     │
             ▼                       ▼     ▼                     ▼
      ┌──────────────┐       ┌──────────────┐       ┌─────────────────┐
      │ PostgreSQL   │       │ Hybrid RAG   │       │ Rules Engine    │
      │ Structured   │       │ Vector+Text  │       │ Deterministic   │
      └──────────────┘       └──────────────┘       └─────────────────┘
             │                       │                     │
             └───────────────────────┼─────────────────────┘
                                     │
                              ┌──────▼───────┐
                              │ Knowledge    │
                              │ Graph        │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │ Web Search   │
                              │ (Controlled) │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌────────────────────┐
                              │ Evidence Layer     │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ Model Router       │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ Answer Generation  │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ Output Validation  │
                              └─────────┬──────────┘
                                        │
                                        ▼
                                    USER
```

---

# 6. Data Architecture

The platform should separate information according to how it needs to be queried.

## Layer 1: Structured Data

Use PostgreSQL.

Contains:

- Students.
- Companies.
- Placement drives.
- Roles.
- Packages.
- Eligibility criteria.
- Dates.
- Registration status.

---

## Layer 2: Unstructured Knowledge

Contains:

- PDFs.
- Circulars.
- Placement policies.
- Job descriptions.
- Announcements.
- Interview experiences.

Use hybrid search and embeddings.

---

## Layer 3: Rules

Contains deterministic policies.

Examples:

```text
CGPA >= 7
Active Backlogs == 0
Branch IN [CSE, IT]
```

---

## Layer 4: Relationships

Contains graph-like information.

Examples:

```text
Student → HAS_SKILL → Python

Company → OFFERS → Software Engineer Role

Role → REQUIRES → Data Structures

Student → ELIGIBLE_FOR → Placement Drive
```

---

## Layer 5: External Information

Controlled web information.

External information is never allowed to override official college placement data.

---

# 7. Query Classification and Routing

Every query first goes through a router.

Example intent categories:

```text
COMPANY_FACT
ELIGIBILITY_CHECK
PLACEMENT_POLICY
UPCOMING_DRIVES
STUDENT_STATUS
DOCUMENT_QUERY
RELATIONSHIP_QUERY
EXTERNAL_INFORMATION
GENERAL_CONVERSATION
```

Example:

```text
User:
"Can I apply to TCS?"

                ↓

Intent:
ELIGIBILITY_CHECK

                ↓

Company:
TCS

                ↓

Rules Engine
```

---

## Router Confidence

Example:

```json
{
  "intent": "ELIGIBILITY_CHECK",
  "confidence": 0.98,
  "entities": {
    "company": "TCS"
  }
}
```

If confidence is below a threshold:

```text
Ask a clarifying question.
```

Do not guess the user's intent.

---

# 8. Structured Data Layer

PostgreSQL should be the primary source of truth.

## Example Entities

### Students

```text
students
--------
id
college_id
branch
batch
cgpa
active_backlogs
placement_status
created_at
updated_at
```

### Companies

```text
companies
---------
id
name
official_website
industry
description
created_at
updated_at
```

### Placement Drives

```text
placement_drives
----------------
id
company_id
academic_year
role
ctc
location
status
registration_deadline
test_date
interview_date
```

### Eligibility Rules

```text
eligibility_rules
-----------------
id
placement_drive_id
minimum_cgpa
maximum_active_backlogs
allowed_branches
additional_conditions
```

---

## Safe Tool Layer

The LLM must not directly execute unrestricted SQL.

Instead expose controlled backend operations:

```text
getMyEligibility(student_id, company_id)

getUpcomingDrives(student_id)

getPublicCompanyInfo(company_id)

getEligibleCompanies(student_id)
```

The backend validates authorization and performs the actual database queries.

---

# 9. Rules Engine

The rules engine handles deterministic decisions.

## Example

Company eligibility:

```text
minimum_cgpa >= 7.0
active_backlogs == 0
branch IN [CSE, IT]
```

Student:

```text
CGPA = 7.4
Backlogs = 0
Branch = CSE
```

Rules engine output:

```json
{
  "eligible": true,
  "failed_rules": []
}
```

The LLM receives the result and explains it.

## Principle

```text
Rules Engine decides.
LLM explains.
```

---

# 10. RAG and Knowledge Retrieval

RAG should only be used for unstructured knowledge.

## Data Sources

- Placement policies.
- Circulars.
- PDFs.
- Company documents.
- Interview experiences.
- FAQs.

---

## Document Pipeline

```text
Document Upload
        ↓
Validation
        ↓
OCR if required
        ↓
Text Extraction
        ↓
Document Classification
        ↓
Permission Classification
        ↓
Section Detection
        ↓
Semantic Chunking
        ↓
Metadata Generation
        ↓
Embedding Generation
        ↓
Vector Storage
        ↓
Keyword Indexing
```

---

## Chunk Metadata

Each chunk should contain metadata such as:

```json
{
  "chunk_id": "chunk_123",
  "document_id": "doc_45",
  "document_type": "PLACEMENT_POLICY",
  "academic_year": "2026",
  "visibility": "STUDENT",
  "allowed_roles": ["STUDENT", "TPO"],
  "effective_from": "2026-07-01",
  "effective_until": null,
  "version": 4
}
```

---

## Hybrid Search

Do not use only embeddings.

Use:

```text
Semantic Search
+
Keyword/BM25 Search
+
Metadata Filtering
+
Reranking
```

Pipeline:

```text
Query
  ↓
Semantic Search → Top 30
  +
Keyword Search → Top 30
  ↓
Merge Results
  ↓
Authorization Filter
  ↓
Reranker
  ↓
Top Relevant Evidence
```

---

# 11. Knowledge Graph Layer

A graph database should be added when relationship queries become important.

Example:

```text
(Student)
   │
   ├── HAS_SKILL ──► (Skill)
   │
   └── ELIGIBLE_FOR ──► (Placement Drive)

(Placement Drive)
   │
   └── CONDUCTED_BY ──► (Company)

(Company)
   │
   └── OFFERS ──► (Role)

(Role)
   │
   └── REQUIRES ──► (Skill)
```

Example question:

> Which upcoming companies require skills that I already possess?

This is naturally represented as a graph traversal.

Do not introduce a graph database prematurely. PostgreSQL is sufficient for many relationships.

---

# 12. Controlled Web Search

Web search is a fallback.

## Decision Process

```text
Question
   ↓
Is internal knowledge sufficient?
   │
   ├── Yes → Use internal data
   │
   └── No
        ↓
Is web search allowed?
        │
        ├── No → Explain limitation
        │
        └── Yes
             ↓
        Search trusted sources
             ↓
        Extract relevant information
             ↓
        Treat as untrusted external data
             ↓
        Generate cited answer
```

## Source Priority

1. Official college policy.
2. Official college placement notice.
3. Official company recruitment document.
4. Official company website.
5. Reputable external sources.
6. Student-contributed information.

External information must never override official college rules.

---

# 13. Security and Authorization Architecture

Prompt instructions are not a security system.

The core security model should be:

```text
Authentication
        ↓
Authorization
        ↓
Permission-aware Retrieval
        ↓
Permission-aware Tools
        ↓
LLM
        ↓
Output Validation
```

---

## RBAC

Roles:

```text
STUDENT
TPO
PLACEMENT_ADMIN
SUPER_ADMIN
```

---

## ABAC

Role alone is insufficient.

Access may depend on:

- Branch.
- Batch.
- Placement status.
- Company.
- Drive stage.
- Academic year.

Example:

```text
Information is visible if:

Role == STUDENT
AND Batch == target_batch
AND Publication_Status == PUBLISHED
```

---

## Principle

Restricted information should never enter the LLM context for unauthorized users.

---

# 14. Guardrails

Guardrails should exist at multiple layers.

## Layer 1: Input Guardrails

Detect:

- Prompt injection.
- Requests for hidden information.
- Attempts to bypass permissions.
- Malicious instructions.

---

## Layer 2: Retrieval Guardrails

Apply metadata and authorization filters.

```text
User Permission Context
        ↓
Vector Query with Permission Filters
        ↓
Only Authorized Chunks
```

---

## Layer 3: Tool Guardrails

Do not expose unrestricted tools.

Bad:

```text
getAllStudentData()
```

Better:

```text
getMyEligibility()

getMyUpcomingCompanies()

getPublicCompanyInformation()
```

---

## Layer 4: Output Guardrails

Check for:

- Restricted information.
- Other student information.
- Internal analytics.
- Unreleased shortlists.
- Confidential content.

---

# 15. Caching and Cost Optimization

Semantic answer caching alone is unsafe.

Example:

```text
Can I apply with 0 backlogs?
Can I apply with 1 backlog?
```

These queries are semantically similar but can have different answers.

Therefore caching must be context-aware.

---

## Cache Level 1: Exact Query Cache

Cache key:

```text
normalized_query
+
permission_scope
+
knowledge_version
+
academic_year
```

---

## Cache Level 2: Structured Result Cache

Example:

```text
student_id
+
company_id
+
eligibility_rule_version
```

Cache deterministic results instead of only natural-language answers.

---

## Cache Level 3: Retrieval Cache

Cache retrieved evidence:

```text
document_ids
chunk_ids
```

Generate a new answer if required.

---

## Cache Level 4: Permission-Aware Answer Cache

Only for safe public information.

Never share cached responses across users with different permission scopes.

---

## Cache Level 5: Prompt Caching

Keep stable prompt components together:

```text
Static System Instructions
Static Security Rules
Static Tool Definitions

Dynamic User Context
Dynamic Retrieved Evidence
User Query
```

---

# 16. LLM Architecture

Use model routing.

```text
Query
  ↓
Cheap Intent Classifier
  ↓
┌─────────────────────────────────────┐
│ Simple structured query → No LLM    │
│ Eligibility → Rules + Small LLM     │
│ Simple RAG → Medium Model           │
│ Complex reasoning → Strong Model    │
└─────────────────────────────────────┘
```

The strongest model should not process every request.

---

# 17. Data Ingestion Pipeline

Admin uploads:

- PDF.
- DOCX.
- CSV.
- Excel.
- Manual form.

Pipeline:

```text
Upload
  ↓
Validation
  ↓
Text/Data Extraction
  ↓
AI-Assisted Classification
  ↓
Structured Data Extraction
  ↓
Human Verification
  ↓
Draft Version
  ↓
Publish
  ↓
Indexes Updated
  ↓
Caches Invalidated
```

---

## Draft vs Published

```text
DRAFT
  ↓
ADMIN REVIEW
  ↓
PUBLISHED
  ↓
STUDENT ACCESSIBLE
```

Students should never retrieve draft information.

---

# 18. Complete Request Lifecycle

Example:

> "Am I eligible for Microsoft?"

## Step 1 — Authenticate

Identify:

```text
student_id
role
branch
batch
```

## Step 2 — Load Context

Retrieve required student data.

## Step 3 — Input Security

Screen for malicious intent.

## Step 4 — Cache Lookup

Check exact and deterministic caches.

## Step 5 — Intent Classification

```text
ELIGIBILITY_CHECK
```

## Step 6 — Resolve Entities

Find Company ID.

## Step 7 — Retrieve Current Drive

Only active, applicable placement drive.

## Step 8 — Execute Rules

Evaluate student data against rules.

## Step 9 — Generate Explanation

Provide verified result to LLM.

## Step 10 — Output Validation

Check for policy violations.

## Step 11 — Return Answer

Include relevant source information.

---

# 19. Admin and Knowledge Management

The admin system is a major part of the product.

Features should include:

- Company management.
- Placement drive management.
- Eligibility rule management.
- Policy publishing.
- Document upload.
- Access-level assignment.
- Version history.
- AI extraction review.
- Audit logs.

Critical data should require human verification before publication.

---

# 20. Database Design

Recommended primary database: PostgreSQL.

Core tables:

```text
users
students
roles
permissions
companies
placement_drives
eligibility_rules
placement_policies
documents
document_versions
document_chunks
skills
student_skills
roles
company_roles
audit_logs
```

---

## Important Versioning Fields

For policies and documents:

```text
version
status
effective_from
effective_until
published_at
created_by
updated_by
```

---

# 21. API Architecture

Example endpoints:

## Student

```text
POST /chat
GET  /companies
GET  /companies/:id
GET  /placement-drives
GET  /me/eligibility/:companyId
GET  /me/recommendations
```

## Admin

```text
POST /admin/documents
POST /admin/companies
POST /admin/drives
POST /admin/eligibility-rules
POST /admin/policies/:id/publish
```

---

# 22. Background Jobs

Use a queue system for expensive tasks.

Jobs:

```text
DOCUMENT_PROCESSING
OCR_PROCESSING
EMBEDDING_GENERATION
KNOWLEDGE_GRAPH_UPDATE
CACHE_INVALIDATION
WEB_REFRESH
EVALUATION_RUN
```

Recommended queue:

```text
BullMQ + Redis
```

---

# 23. Observability and Monitoring

Every request should produce a trace.

Store:

```text
request_id
user_id
intent
router_confidence
tools_called
retrieved_documents
retrieved_chunks
model
input_tokens
output_tokens
latency
estimated_cost
cache_hit
security_decision
```

Metrics:

```text
Requests per day
Average latency
LLM cost per request
Cache hit rate
Retrieval success rate
Hallucination rate
Blocked security requests
```

---

# 24. Evaluation and Testing

Create a benchmark dataset.

Suggested minimum:

```text
500 to 2000 realistic questions
```

Categories:

- Eligibility.
- Policies.
- Company information.
- Ambiguous questions.
- Outdated information.
- Restricted data.
- Prompt injection.
- Multi-step reasoning.

Each evaluation case should contain:

```text
Question
Expected intent
Expected data source
Expected access decision
Expected answer
Expected sources
```

---

# 25. Recommended Technology Stack

## Frontend

```text
Next.js
TypeScript
Tailwind CSS
```

## Backend

```text
Node.js
TypeScript
NestJS
```

Alternative:

```text
Fastify
```

## Database

```text
PostgreSQL
```

## Vector Search

Initial architecture:

```text
pgvector
```

## Cache

```text
Redis
```

## Background Jobs

```text
BullMQ
Redis
```

## Object Storage

```text
Cloudflare R2
or
Amazon S3
```

## Knowledge Graph

Later phase:

```text
Neo4j
```

---

# 26. Deployment Architecture

```text
                    INTERNET
                        │
                        ▼
                 ┌─────────────┐
                 │ CDN / WAF   │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Next.js App │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Backend API │
                 └───┬─────┬───┘
                     │     │
                     ▼     ▼
                PostgreSQL Redis
                     │
                     ▼
                Object Storage
```

As scale increases:

```text
Load Balancer
     │
API Instances
     │
Redis Queue
     │
Worker Instances
```

---

# 27. Development Roadmap

## Phase 1 — Foundation

Build:

- Authentication.
- Student profiles.
- Companies.
- Placement drives.
- Eligibility rules.
- Admin panel.

Do not build RAG first.

---

## Phase 2 — Chat Intelligence

Build:

- Query routing.
- Structured query tools.
- Rules engine.
- Basic chat interface.

---

## Phase 3 — Knowledge Retrieval

Build:

- Document upload.
- Processing pipeline.
- Embeddings.
- Hybrid search.
- Citations.

---

## Phase 4 — Security

Build:

- ABAC.
- Permission-aware retrieval.
- Tool restrictions.
- Input guardrails.
- Output validation.

---

## Phase 5 — Optimization

Build:

- Redis caching.
- Retrieval caching.
- Model routing.
- Token budgets.
- Monitoring.

---

## Phase 6 — Advanced Intelligence

Potential features:

- Knowledge graph.
- Personalized company recommendations.
- Skill gap analysis.
- Company comparisons.
- Placement analytics.
- Controlled web search.

---

# 28. Architecture Decisions and Tradeoffs

## Why not pure RAG?

Because structured questions should be answered deterministically.

---

## Why not let the LLM generate SQL?

Because unrestricted SQL generation introduces:

- Security risks.
- Incorrect queries.
- Unauthorized access.
- Difficult debugging.

Use controlled backend tools.

---

## Why not use semantic answer caching aggressively?

Because semantically similar questions can have materially different answers.

Cache deterministic results and retrieval results more aggressively than final answers.

---

## Why not rely on prompts for security?

Because prompts are instructions, not access control.

Security must be enforced in:

- Database queries.
- Retrieval filters.
- Tool permissions.
- Authorization middleware.

---

## Why not add Neo4j immediately?

Because it increases operational complexity.

Use it only when relationship queries provide meaningful value.

---

# Final Architecture Summary

```text
                         USER
                           │
                           ▼
                  Authentication
                           │
                           ▼
                   Authorization / ABAC
                           │
                           ▼
                    Input Guardrails
                           │
                           ▼
                      Cache Layer
                           │
                           ▼
                      Query Router
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
     PostgreSQL        Hybrid RAG       Rules Engine
          │                │                 │
          └────────────────┼─────────────────┘
                           │
                           ▼
                    Knowledge Graph
                           │
                           ▼
                  Controlled Web Search
                           │
                           ▼
                     Evidence Layer
                           │
                           ▼
                       Model Router
                           │
                           ▼
                   Answer Generation
                           │
                           ▼
                   Output Validation
                           │
                           ▼
                         USER
```

# Final Principle

The system should never be architected around the assumption that an LLM is reliable enough to act as the source of truth.

The LLM is the interface layer.

The actual intelligence and reliability come from:

- Correct data modeling.
- Deterministic rules.
- Permission-aware retrieval.
- Versioned knowledge.
- Hybrid search.
- Controlled tools.
- Evidence validation.
- Caching.
- Monitoring.

If implemented correctly, this can evolve from a college chatbot into a complete Placement Intelligence Platform capable of supporting students, placement officers, and potentially multiple colleges.
