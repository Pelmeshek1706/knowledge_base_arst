# Documentation Index

## Purpose

This folder contains source-of-truth documentation for the `personal_kb` project.

## Documentation folders

| Domain | Folder | Purpose |
|---|---|---|
| Technical Architecture | [architecture](architecture/index.md) | System architecture, storage design, graph schema, retrieval, Q&A, agent/tool boundaries, and local model strategy. |
| Implementation | [implementation](implementation/index.md) | Repository structure, implementation-facing contracts, Python class/service design, service facades, StructuredTool wrappers, and future MCP adapter boundaries. |
| Implementation Roadmap | [roadmap](roadmap/index.md) | MVP implementation sequence, phase dependencies, release criteria, benchmark gates, risk priorities, and sprint recommendations. |
| Product Requirements | [product-requirements](product-requirements/index.md) | Product goals, scope, functional requirements, validation, risks, release plan, and future requirements. |

## Update rules

- Update the focused documentation file that owns the behavior being changed.
- Update this index when adding or removing a top-level documentation folder.
- Do not use this file for agent behavior instructions.
- Do not create nested `AGENTS.md` files inside documentation folders.
