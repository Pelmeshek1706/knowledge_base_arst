# Implementation Index

## Purpose

This folder contains implementation-facing documentation for the `personal_kb` project, including repository structure, tool contracts, and Python class/service design.

## Documentation folders

| Domain | Folder | Purpose |
|---|---|---|
| Repository Structure | [repository-structure](repository-structure/index.md) | Repository layout, root files, runtime data, package boundaries, module responsibilities, implementation order, and future extension locations. |
| Tool Contracts | [tool-contracts](tool-contracts/index.md) | Tool contracts, service facade behavior, StructuredTool wrappers, retrieval/Q&A tools, and future MCP adapter boundaries. |
| Python Class Design | [class-design](class-design/index.md) | Python package boundaries, schemas, service classes, adapter boundaries, testing strategy, and implementation order. |

## Reading order

1. Read the focused folder index for the implementation domain you are changing.
2. Open only the file that owns the current behavior.
3. Follow related links from that focused file when cross-cutting context is needed.

## Update rules

- Update the focused documentation file that owns the behavior being changed.
- Update this index when adding or removing implementation documentation folders.
- Do not use this file for agent behavior instructions.
- Do not create nested `AGENTS.md` files inside documentation folders.
