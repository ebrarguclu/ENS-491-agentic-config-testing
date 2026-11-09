# Agentic Config Testing

**ENS 491/492 Graduation Project — Sabancı University**
**Project #516: Agentic AI for Detecting and Testing Configuration Option Interactions**

## Team
- Fethiye Ebrar Güçlü
- Rana Keleş
- Safiye Nur Narman

**Advisor:** Cemal Yılmaz

## Abstract

Modern software systems are highly configurable, often exposing dozens to
thousands of configuration options (compile-time flags, runtime properties,
CLI arguments, etc.). While individual options are usually well tested in
isolation, the *interactions* between options — cases where a particular
combination of option values produces unexpected or undocumented behavior —
are far harder to detect and are frequently missed by existing test suites.

This project investigates whether an **agentic AI system** (an LLM-driven
agent that verifies its own claims against deterministic tools, rather than
relying on unverified generation) can:

1. Automatically discover the configuration space of a real-world software
   system directly from its source code and documentation.
2. Analyze existing test suites to determine which option interactions are
   already covered.
3. Identify important, currently untested option interactions.
4. Generate new tests that specifically target those interactions.
5. Evaluate the resulting improvement in interaction coverage, code
   coverage, and fault detection.

## Project Flow (5 Stages)

| Stage | Name | Goal |
|---|---|---|
| 1 | Configuration Space Discovery | Given the source code of a system, can GenAI discover its configuration space model (options, values, defaults, constraints)? |
| 2 | Existing Test Suite Analysis | Which option interactions are already exercised by the system's current tests? |
| 3 | Missing Interaction Analysis | Which important interactions are **not** currently tested? |
| 4 | Test Generation | Generate new tests that target the missing interactions. |
| 5 | Evaluation | Measure interaction coverage, code coverage, and failure detection before/after adding the generated tests. |

## Methodology

A core principle of this project: **AI output is never trusted blindly — every
claim is verified with a deterministic tool.** Configuration options and
constraints are only accepted once confirmed against the actual source file
and line number (e.g. via `grep`, static analysis, or the build system
itself), not generated from the model's memory.

## Candidate Systems Explored

As part of Stage 1, we evaluated candidate open-source systems across
different languages to compare how configuration is expressed:

| System | Language | Config mechanism | Example finding |
|---|---|---|---|
| **curl** | C | Compile-time (`configure.ac`, `AC_ARG_ENABLE`/`AC_ARG_WITH`) + runtime (CLI flags, `curl_easy_setopt` API) | 68 compile-time options, 278 CLI options, 312 API options; e.g. enabling `ldaps` without `ldap` silently disables LDAPS with no error |
| **Apache ZooKeeper** | Java | Runtime (`Properties`-based `zoo.cfg`, parsed in `QuorumPeerConfig.java`) | ~40 configuration keys; e.g. `clientPortAddress` requires `clientPort` to also be set, or `tickTime` implicitly determines `minSessionTimeout`/`maxSessionTimeout` defaults |
| **ESLint** | JavaScript | Schema-based (`flat-config-schema.js`, flat config object) | 7 top-level keys with nested schemas; e.g. legacy eslintrc-style keys are explicitly rejected in flat config, and sibling options like `reportUnusedDisableDirectives` vs. `reportUnusedInlineConfigs` behave inconsistently with boolean values |

## Folder Structure

- `systems/`  — Source code / clones of the studied open-source systems
- `models/`   — Configuration space models (JSON/YAML), with options, values, defaults, types (compile-time/runtime), and constraints
- `scripts/`  — Build, configure, test-run, and coverage automation scripts
- `tests/`    — Generated and existing test files
- `results/`  — Coverage tables and experiment results
- `docs/`     — Meeting notes, reports, and additional documentation

## Current Status

🚧 **Stage 1 in progress.** Candidate systems have been identified and an
initial, source-verified configuration model has been extracted for curl,
ZooKeeper, and ESLint. Next steps: select the final system(s) to work with,
formalize the configuration space model format, and begin Stage 2 (existing
test suite analysis).
