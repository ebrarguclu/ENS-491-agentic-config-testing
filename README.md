# Agentic Config Testing

**ENS 491/492 Graduation Project — Sabancı University**
**Project #516: Agentic AI for Detecting and Testing Configuration Option Interactions**

## Team
- Fethiye Ebrar Güçlü
- Rana Keleş
- Safiye Nur Narman

**Advisor:** Cemal Yılmaz

**Subject system:** [curl](https://github.com/curl/curl) (`curl-8_17_0`) — see
[docs/selection.md](docs/selection.md) for why.

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
different languages to compare how configuration is expressed. The three
systems below were analysed at source level; the full candidate list
(including SQLite, BusyBox, ripgrep and Apache httpd), the selection criteria
and a build check of curl are in [docs/candidates.md](docs/candidates.md).

| System | Language | Config mechanism | Example finding |
|---|---|---|---|
| **curl** ✅ selected | C | Compile-time (`configure.ac`, `AC_ARG_ENABLE`/`AC_ARG_WITH`) + runtime (CLI flags, `curl_easy_setopt` API) | ~115 configure flags, 273 CLI options, 291 API options (counted on `curl-8_17_0`); e.g. enabling `ldaps` without `ldap` silently disables LDAPS with no error |
| **Apache ZooKeeper** | Java | Runtime (`Properties`-based `zoo.cfg`, parsed in `QuorumPeerConfig.java`) | ~40 configuration keys; e.g. `clientPortAddress` requires `clientPort` to also be set, or `tickTime` implicitly determines `minSessionTimeout`/`maxSessionTimeout` defaults |
| **ESLint** | JavaScript | Schema-based (`flat-config-schema.js`, flat config object) | 7 top-level keys with nested schemas; e.g. legacy eslintrc-style keys are explicitly rejected in flat config, and sibling options like `reportUnusedDisableDirectives` vs. `reportUnusedInlineConfigs` behave inconsistently with boolean values |

## Folder Structure

| Folder | Content |
|---|---|
| [`systems/`](systems/) | How to fetch and build the studied system (curl source is cloned locally, not committed) |
| [`models/`](models/) | Configuration space models (YAML): options, values, defaults, types (compile-time/runtime), constraints |
| [`scripts/`](scripts/) | Build, configure, test-run and coverage automation scripts |
| [`tests/`](tests/) | Analysis of existing tests (`existing/`) and LLM-generated tests (`generated/`) |
| [`results/`](results/) | Per-configuration run outputs and coverage tables |
| [`docs/`](docs/) | Candidate list, system selection, meeting notes and reports |

## Deliverables and Responsibilities

| # | Deliverable | Output | Owner | Status |
|---|---|---|---|---|
| D1 | Repository setup | This repository + README | Fethiye Ebrar Güçlü, Safiye Nur Narman | ✅ Done |
| D2 | Candidate systems | [docs/candidates.md](docs/candidates.md) | All | ✅ Done |
| D3 | System selection | [docs/selection.md](docs/selection.md) | Safiye Nur Narman | ✅ Done (curl) |
| D4 | Configuration space model | `models/schema.md`, `models/curl.yaml` | Rana Keleş | ⏳ Next |
| D5 | Build & test automation scripts | `scripts/run_config.sh` + usage | Fethiye Ebrar Güçlü | ⏳ Next |
| D6 | Coverage statistics | `results/coverage_table.md` | Safiye Nur Narman | Planned |
| D7 | LLM test generation | `tests/generated/` + before/after coverage | All (one LLM tool each) | Planned |
| D8 | End-to-end demo | Live demo for the advisor | Rana Keleş | Planned |

## Current Status

🚧 **Stage 1 in progress.** Candidate systems were evaluated and **curl** was
selected as the subject system. It builds from source in about 80 seconds,
and its test suite runs on our setup ([build check](docs/candidates.md#build-check-curl)).
Next steps: define the configuration space model format and extract the
curl model (D4), and write the build-and-test automation script (D5).
