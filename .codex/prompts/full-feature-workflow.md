# Full Approval-Gated Feature Workflow

## Step 1 — Tech Lead Planning

Use the `tech-lead-planning` skill.
Act as `ai_ml_tech_lead`.
Plan the task only. Mark all tasks as PENDING_USER_APPROVAL. Ask for approval.

## Step 2 — User Approval

The user must explicitly approve the plan.

## Step 3 — Single Task Handoff

Tech Lead prepares exactly one task handoff with Status: APPROVED_FOR_IMPLEMENTATION.

## Step 4 — Python Engineer Implementation

Use the `implement-personal-kb-roadmap` skill.
Act as `ai_ml_python_engineer`.
Execute exactly one approved task and stop with QA handoff.

## Step 5 — QA

Use the `ai-ml-quality-assurance` skill.
Act as `ai_ml_qa_engineer`.
Review exactly one completed task and return QA result.

## Step 6 — Fix Loop

If QA fails, Python Engineer fixes one QA bug report at a time. QA verifies.

## Step 7 — Continue Gate

Do not start next task until QA passes and the user or Tech Lead explicitly authorizes continuation.
