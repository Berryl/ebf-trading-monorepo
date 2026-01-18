# ebf-core

Low-level utilities that are shared across projects.  
Designed to be stable, dependency-free, and usable in any CLI, service, or GUI application.

---

## Purpose
Provide a small set of common building blocks:
- File handling
- Configuration loading/merging
- Guard clauses
- Simple primitives (time, ids, utilities)

---

## In Scope
- **File** – atomic writes, temp paths, safe replace.
- **Config** – YAML/JSON/TOML loaders, layered merge.
- **Guards** – `ensure_*` functions for argument validation.
- **Reflection** – cross-cutting reflection utilities.
- **Time** – timezone-safe helpers.
- **Ids** – UUID/slug helpers.
- **Util** – cross-cutting helpers.

## Out of Scope
- Domain-specific logic (finance, securities, trading).
- GUI, networking, or persistence libraries.
- Heavy external dependencies.

---

## Design Principles
- **Minimal**: no heavy third-party deps.
- **Composable**: small, predictable functions.
- **Stable**: SemVer with clear deprecation windows.
- **Portable**: usable by CLI, services, or GUIs.

---

## Installation
```bash
pip install ebf-core
