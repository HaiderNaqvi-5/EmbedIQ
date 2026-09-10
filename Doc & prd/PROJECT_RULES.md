# EmbedIQ — Project Development Rules

These rules are mandatory for all development work on the EmbedIQ project.

The purpose of these rules is to maintain project continuity across sessions, prevent unnecessary architectural drift, keep the implementation aligned with the approved PRD, and make every development decision traceable.

---

# 1. PRD IS THE SOURCE OF TRUTH

The project's PRD is the authoritative definition of what EmbedIQ is supposed to become.

The PRD must always be consulted before implementing a feature that affects:

- architecture
- data flow
- APIs
- database structure
- crawler behavior
- RAG behavior
- authentication
- background jobs
- widget behavior
- frontend/backend boundaries
- security
- project scope
- technology choices

Do not silently contradict, reinterpret, or replace a requirement defined in the PRD.

If implementation details are missing from the PRD, follow the clarification rules below.

---

# 2. THE PRD IS LOCKED

The PRD must be treated as a locked document.

Do NOT modify the PRD simply because the implementation would be easier another way.

Do NOT silently update requirements while implementing a feature.

Do NOT change architecture, scope, technology choices, workflows, or requirements defined by the PRD without explicit approval from the project owner.

Only the project owner can authorize a PRD change.

---

# 3. PRD CHANGE PROCEDURE

If you believe the PRD must be changed, STOP before changing it.

Explain:

1. What the current PRD requires.
2. What problem has been discovered.
3. Why the existing requirement cannot or should not be followed.
4. What change you recommend.
5. What parts of the project will be affected.
6. Whether existing implementation will need modification.
7. Whether the change introduces new complexity or dependencies.

Then explicitly ask for approval.

Example:

"The current PRD requires X.

While implementing Y, I discovered Z.

I recommend changing X to A because...

This will affect:
- ...
- ...
- ...

Do you want me to update the PRD and proceed with this change?"

Do not modify the PRD until approval is explicitly given.

After approval:

1. Update the PRD.
2. Record the decision in the current session documentation.
3. Record the impact in implementation.md.
4. Then modify the implementation.

---

# 4. ASK WHEN A REQUIREMENT IS AMBIGUOUS

Do not make important product decisions on behalf of the project owner.

If something required for implementation is genuinely ambiguous, explicitly ask what should happen.

This particularly applies when the decision affects:

- product behavior
- architecture
- database design
- security
- APIs
- user experience
- business rules
- feature scope
- third-party services
- permanent technical choices

Before asking, inspect:

1. the PRD;
2. implementation.md;
3. relevant previous session documentation;
4. the existing codebase.

If the answer already exists there, follow it instead of asking again.

Do not ask questions about trivial implementation details that can safely be determined from existing conventions.

---

# 5. DO NOT GUESS PRODUCT REQUIREMENTS

Never invent requirements just to complete a task.

There is a difference between:

IMPLEMENTATION DETAIL

and

PRODUCT DECISION.

Normal implementation details may be decided using established project conventions.

Product decisions must come from:

1. the PRD;
2. an already approved documented decision;
3. explicit clarification from the project owner.

When uncertain which category something belongs to, ask.

---

# 6. KEEP THE IMPLEMENTATION SIMPLE

Avoid over-engineering.

Use the simplest implementation that correctly satisfies the PRD and current task.

Do NOT introduce:

- unnecessary abstraction layers
- unnecessary design patterns
- premature microservices
- unnecessary packages
- unnecessary infrastructure
- speculative features
- premature optimization
- generic frameworks for hypothetical future requirements
- complex fallback systems unless required
- features that are only "nice to have"

Do not build Phase 2 or future features while implementing MVP functionality unless explicitly requested.

The preferred principle is:

> Build the smallest clean implementation that completely satisfies the current requirement.

Simple does NOT mean careless.

Security, data isolation, validation, error handling, and requirements explicitly marked as mandatory in the PRD must still be implemented correctly.

---

# 7. WORK ON THE REQUESTED SCOPE ONLY

When assigned a feature, stay within that feature's scope.

For example, if the task is:

"Implement the crawler"

do not independently redesign:

- authentication
- RAG
- widget architecture
- frontend
- database architecture

unless the crawler genuinely requires a related change.

If another subsystem must change, explain why before making a significant architectural change.

---

# 8. PROJECT DOCUMENTATION STRUCTURE

Inside the EmbedIQ project documentation area, maintain the following structure:

Doc & prd/
│
├── PRD.md (Source of Truth / PROJECT_SPEC.md)
│
├── PROJECT_RULES.md (Locked Development Rules)
│
├── implementation.md (Current state of the codebase)
│
└── sessions/
    ├── prd_and_architecture.md
    ├── crawler.md
    ├── authentication.md
    ├── rag.md
    ├── widget.md
    ├── branding.md
    └── ...

PRD.md
    = what the project is supposed to become.

implementation.md
    = what the project currently is.

sessions/
    = detailed historical record of how individual features were implemented.

These three documentation layers serve different purposes and must not be mixed together.

---

# 9. SESSION DOCUMENTATION IS MANDATORY

At the end of every development session, document the work completed during that session.

Documentation must be created BEFORE considering the session complete.

The session documentation belongs inside:

Doc & prd/sessions/

Organize documentation by the feature worked on.

Examples:

crawler work:

Doc & prd/sessions/crawler.md

authentication work:

Doc & prd/sessions/authentication.md

RAG work:

Doc & prd/sessions/rag.md

widget work:

Doc & prd/sessions/widget.md

If an existing feature file already exists, update it instead of creating unnecessary duplicate documentation.

---

# 10. FEATURE SESSION FILE FORMAT

Every feature session document must explain enough information that another developer or AI agent can understand what happened without reconstructing the entire session from Git history.

Use this structure:

# Feature: [Feature Name]

## Current Status

NOT STARTED / IN PROGRESS / PARTIALLY COMPLETE / COMPLETE / BLOCKED

## Objective

What this feature is supposed to accomplish according to the PRD.

## Work Completed

Describe exactly what was implemented.

## Files Created

- path/to/file
- path/to/file

Explain the purpose of important files.

## Files Modified

- path/to/file
- path/to/file

Explain significant modifications.

## Implementation Details

Describe the important technical implementation.

Do not simply say:

"Implemented crawler."

Explain what was actually implemented.

## Important Decisions

Record technical or product decisions made during implementation.

For each significant decision explain:

- decision
- reason
- alternatives considered when relevant

## PRD References

State which PRD requirements this implementation satisfies.

Example:

- FR-004 — Same-site page discovery
- FR-005 — Static crawling
- FR-006 — Playwright fallback

## Problems Encountered

Document significant problems, bugs, unexpected behavior, or limitations discovered during the session.

## Remaining Work

Explicitly list anything unfinished.

## Testing Performed

Record:

- tests added
- commands run
- manual tests performed
- important results

Do not claim something works if it was not tested.

## Known Issues

List unresolved problems.

If none:

None currently known.

## Next Recommended Step

State the logical next task based on the PRD and implementation state.

---

# 11. UPDATE implementation.md AFTER EVERY SESSION

After updating the relevant feature session file, update:

Doc & prd/implementation.md

This file represents the CURRENT STATE of the entire project.

It must not become a massive chronological development diary.

Detailed history belongs in sessions/.

implementation.md should provide a concise map of:

- what exists
- what works
- what is partially implemented
- what has not been implemented
- what is blocked
- where detailed implementation history can be found

---

# 12. implementation.md FORMAT

Maintain approximately this structure:

# EmbedIQ — Current Implementation State

Last Updated: [date]

## Overall Status

Briefly explain the current state of the project.

## Implemented

### Authentication

Status: COMPLETE

Implemented:
- ...
- ...

Detailed history:
`sessions/authentication.md`

### Crawler

Status: IN PROGRESS

Implemented:
- URL validation
- same-domain discovery
- static HTML fetching

Remaining:
- Playwright fallback
- additional crawler tests

Detailed history:
`sessions/crawler.md`

### Knowledge Pipeline

Status: NOT STARTED

PRD requirements:
- canonical website.md
- chunking
- embeddings
- pgvector indexing

### RAG

Status: NOT STARTED

### Branding

Status: NOT STARTED

### Widget

Status: NOT STARTED

## Current System Flow

Keep this synchronized with the implementation that actually exists.

Example:

User
↓
Authentication
↓
Create Bot
↓
Crawler
↓
[remaining pipeline not implemented]

Do NOT show unimplemented components as though they already exist.

## Remaining MVP Requirements

List the remaining requirements from PRD.md.

## Current Blockers

List known blockers.

If none:

None.

## Session Documentation

- PRD & Baseline → `sessions/prd_and_architecture.md`
- Authentication → `sessions/authentication.md`
- Crawler → `sessions/crawler.md`
- RAG → `sessions/rag.md`
- Widget → `sessions/widget.md`

Only reference files that actually exist.

---

# 13. implementation.md MUST DESCRIBE REALITY

implementation.md must describe what the CODEBASE currently does.

PRD.md describes the desired product.

These are deliberately different.

Never mark something IMPLEMENTED simply because it exists in the PRD.

Use:

NOT STARTED
IN PROGRESS
PARTIALLY COMPLETE
COMPLETE
BLOCKED

A feature may only be marked COMPLETE when its required behavior has been implemented and reasonably tested.

---

# 14. USE PREVIOUS SESSION DOCUMENTATION

Before modifying an existing feature:

1. Read the relevant PRD section.
2. Read implementation.md.
3. Read the corresponding sessions/<feature>.md file if it exists.
4. Inspect the current code.
5. Then begin implementation.

Do not rely only on conversation memory.

The repository documentation and current codebase are the persistent project memory.

---

# 15. NEVER REIMPLEMENT COMPLETED WORK WITHOUT REASON

Before writing new code, inspect whether the functionality already exists.

Do not create:

crawler_v2.py
crawler_new.py
crawler_final.py

simply because previous implementation context was forgotten.

Modify or extend the established implementation unless there is a documented reason to replace it.

If replacing an existing implementation is necessary, explain:

- why
- what replaces it
- what behavior changes
- what migration impact exists

and document the decision.

---

# 16. CODE CHANGES MUST BE TRACEABLE

Every meaningful feature implementation should be traceable:

PRD requirement
    ↓
implementation.md
    ↓
sessions/<feature>.md
    ↓
actual source files
    ↓
tests

Documentation must reference real file paths.

Do not invent file names or claim files were changed without verifying them.

---

# 17. VERIFY BEFORE CLAIMING COMPLETION

Never state that a feature works solely because code was written.

Before marking COMPLETE:

1. run relevant tests;
2. run lint/type checks where configured;
3. verify imports/build;
4. perform an appropriate functional test;
5. confirm the implementation satisfies the PRD acceptance criteria.

If something cannot be tested, state:

"Implemented but not fully verified because ..."

and use PARTIALLY COMPLETE where appropriate.

---

# 18. DO NOT HIDE FAILURES

If something fails:

- report it;
- identify the likely cause;
- document it if it affects project state;
- do not silently bypass the requirement;
- do not mark the feature complete.

A workaround that violates the PRD requires approval.

---

# 19. DO NOT CHANGE THE STACK WITHOUT APPROVAL

The approved stack is defined by PRD.md.

Do not independently replace technologies.

For example, do not replace:

FastAPI
Celery
Redis
PostgreSQL
pgvector
Playwright
BeautifulSoup/lxml
Next.js
React
Tailwind

with alternatives merely because another library appears easier.

If a change is genuinely necessary, follow the PRD Change Procedure.

---

# 20. PRESERVE CORE ARCHITECTURAL INVARIANTS

The following must never be accidentally violated:

ONE WEBSITE
    ↓
ONE BOT
    ↓
ONE BOT-SCOPED KNOWLEDGE BASE
    ↓
BOT-SCOPED RETRIEVAL
    ↓
RAG
    ↓
EMBEDDABLE WIDGET

In particular:

- every chunk belongs to a bot;
- every vector belongs to a bot;
- retrieval always requires bot_id;
- one customer's knowledge must never leak into another bot;
- crawled text never becomes trusted AI instructions;
- crawling remains asynchronous;
- interactive chat does not run through Celery.

---

# 21. DO NOT DRIFT FROM MVP

Before starting a new feature, determine whether it is:

MVP
PHASE 2
PHASE 3

If the requested work is not required for the current MVP and was not explicitly requested, do not implement it.

Do not spend project time making future systems "ready" unless the current implementation genuinely requires that abstraction.

---

# 22. END-OF-SESSION CHECKLIST

Before ending every development session:

[ ] Current requested task has been implemented as far as possible.

[ ] Relevant tests/checks have been run.

[ ] No known failure has been hidden.

[ ] PRD was not modified without approval.

[ ] No unapproved architecture change was introduced.

[ ] Relevant `sessions/<feature>.md` has been created or updated.

[ ] Files created/modified are documented.

[ ] Important decisions are documented.

[ ] Problems and known issues are documented.

[ ] Remaining work is documented.

[ ] `implementation.md` has been updated.

[ ] implementation.md accurately represents the CURRENT codebase.

[ ] Completed work references the relevant session documentation.

[ ] Remaining MVP work is still visible.

[ ] The recommended next task is stated.

A session is NOT considered complete until this documentation has been updated.

---

# 23. START-OF-SESSION CHECKLIST

At the beginning of a new development session:

1. Read PRD.md.
2. Read implementation.md.
3. Identify the requested feature.
4. Read `sessions/<feature>.md` if it exists.
5. Inspect the relevant source code.
6. Determine what is already implemented.
7. Determine what remains according to the PRD.
8. Ask only genuinely unresolved product questions.
9. Implement the smallest correct solution.
10. Test it.
11. Update project documentation before finishing.

---

# 24. PRIORITY ORDER WHEN INFORMATION CONFLICTS

If instructions appear to conflict, use this order:

1. Explicit current instruction from the project owner
2. Approved PRD.md
3. Approved documented project decisions
4. implementation.md
5. sessions/<feature>.md
6. Existing implementation
7. Assumptions

If #1 conflicts with the locked PRD, explicitly point out the conflict and ask whether the PRD should be changed before treating the new behavior as a permanent project requirement.

Never silently resolve a major contradiction through assumption.

---

# 25. PRIMARY DEVELOPMENT PRINCIPLE

For every task, follow:

UNDERSTAND
    ↓
CHECK PRD
    ↓
CHECK CURRENT IMPLEMENTATION
    ↓
CHECK PREVIOUS FEATURE HISTORY
    ↓
CLARIFY REAL AMBIGUITIES
    ↓
IMPLEMENT THE SMALLEST CORRECT SOLUTION
    ↓
TEST
    ↓
DOCUMENT FEATURE SESSION
    ↓
UPDATE CURRENT IMPLEMENTATION STATE
    ↓
CONTINUE

The objective is not to write the most code.

The objective is to build exactly what the PRD requires, preserve continuity between development sessions, and always leave the repository in a state where another developer or AI agent can understand exactly what has been implemented and what remains.
