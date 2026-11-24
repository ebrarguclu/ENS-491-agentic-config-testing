# Agentic Config Testing

ENS 491/492 Graduation Project, Sabancı University
Project #516: *Agentic AI for Detecting and Testing Configuration Option Interactions*

| | |
|---|---|
| Team | Fethiye Ebrar Güçlü, Rana Keleş, Safiye Nur Narman |
| Advisor | Cemal Yılmaz |
| System we study | [curl](https://github.com/curl/curl), version `curl-8_17_0` ([why curl?](docs/selection.md)) |
| Where we are | D1 to D8 finished. Next: D9 to D13, see the [plan](docs/plan-d9-d13.md) |

New to the project? Start with [Key terms](#key-terms), then read the
[progress report](docs/progress-d1-d4.md). It explains D1 to D4 step by step. For D5 to
D8, see [Where we are now](#where-we-are-now) below.

## The problem in one example

Most real programs can be set up in many different ways. curl, for example, can be
built with or without FTP support, with or without cookies, with or without encryption,
and so on. Each of these choices is called a **configuration option**.

Every option usually works fine on its own. Problems appear when certain options are
combined. Here is a real case we found in curl:

> We asked the build system to include LDAPS (secure LDAP) but turned LDAP off. The
> build finished without any error. The resulting curl simply did not contain LDAPS.

Nobody tests every combination, because there are far too many. Our first model of curl
contains only 22 on/off options, and that already gives 2^22, about **4.2 million**
different ways to build curl. So the important question is: *which* combinations should
we test?

## What we want to find out

We want to see whether an **AI agent** can help with this. An AI agent here means a
language model that can use tools (read files, run commands) and check its own answers.
In five stages, we ask whether it can:

| Stage | Question |
|---|---|
| 1. Discover | Can the AI find a program's options, their possible values, defaults and the rules between them, just from the source code? |
| 2. Analyse existing tests | Which option combinations do the program's own tests already cover? |
| 3. Find gaps | Which *important* combinations are not tested at all? |
| 4. Generate tests | Can the AI write new tests aimed at exactly those gaps? |
| 5. Evaluate | Do the new tests improve coverage and find more bugs? |

## Our main rule

**The AI may suggest, but nothing is accepted until we have checked it with a tool.**

Every option and rule in our model points to the exact lines in curl's source code where
it is defined, and every rule has been confirmed by actually running curl's build
system. This matters because AI models sometimes produce answers that sound right but are
wrong.

## Key terms

| Term | In plain words | Example from curl |
|---|---|---|
| Configuration option | A setting that changes how a program is built or how it behaves | "include FTP or not" |
| Compile-time option | Chosen *before* the program is built. It decides which code goes into the program at all | `--disable-ftp` builds a curl with no FTP code inside |
| Runtime option | Chosen *when the program is run*, for example as a command-line flag | `curl --compressed https://example.com` |
| `configure` | A script that comes with curl. You run it before building and give it your choices as flags | `./configure --with-openssl --disable-ftp` |
| Configuration | One concrete choice for every option | FTP off, cookies on, OpenSSL for encryption |
| Configuration space | All possible configurations together | about 4.2 million combinations of our 22 options, before removing the invalid ones |
| Constraint | A rule that some combinations are not allowed | LDAPS needs LDAP |
| Silent constraint | A constraint that the build system "solves" by quietly changing your choice instead of showing an error | LDAPS is dropped without an error |
| Test suite | The tests that come with the program | curl has about 1,890 tests |
| Code coverage | How much of the program's code the tests actually run | "62% of lines were executed" |
| Branch coverage | How many of the program's decision outcomes the tests run. Every `if` has two outcomes, true and false, and both must happen to count as fully covered | an `if` in curl's proxy code that the tests only ever reach with a proxy set is half covered |
| Interaction coverage | How many option *combinations* the tests actually exercise | "FTP off + cookies on was tested" |
| Covering array | A small set of configurations chosen so that every pair of option values appears together in at least one of them (2-way or "pairwise"). A standard technique from combinatorial interaction testing (CIT) | for 22 on/off options, about 10 to 15 builds instead of 4.2 million |
| Full configuration | A configuration that gives an explicit value to every option, so the machine decides nothing | all 22 curl options, with `ldap`, `ipv6` and `zlib` set by hand instead of `auto` |
| Environment requirement | A value that only works if the build machine has something installed | `ldap: enabled` needs the LDAP libraries |
| Ground truth | An official, trusted source we can check the AI's answers against | curl's build files and test metadata |

## Systems we looked at

Before choosing curl we compared several open-source systems. Three of them were studied
in detail at source-code level. The full comparison of all seven systems is in
[docs/candidates.md](docs/candidates.md).

| System | Language | How it is configured | A hidden rule we found |
|---|---|---|---|
| **curl** (selected) | C | About 115 build-time flags, plus 273 command-line options and 291 library options | Asking for LDAPS without LDAP does not cause an error. LDAPS is silently left out |
| Apache ZooKeeper | Java | About 40 settings in a `zoo.cfg` file, read at start-up | `clientPortAddress` only works if `clientPort` is also set, and `tickTime` silently decides the session timeout defaults |
| ESLint | JavaScript | A nested configuration object checked against a schema | Old-style keys are rejected, and two similar options (`reportUnusedDisableDirectives`, `reportUnusedInlineConfigs`) treat `true`/`false` differently |

## Repository map

| Folder | What you find there |
|---|---|
| [`docs/`](docs/) | Reports: candidate systems, why we chose curl, progress report |
| [`systems/`](systems/) | How to download and build curl (curl's own code is not stored here) |
| [`models/`](models/) | The configuration model of curl and the format we use to write it |
| [`scripts/`](scripts/) | Scripts that build curl, run its tests and check our model |
| [`tests/`](tests/) | Notes on curl's own tests, and later the tests generated by AI |
| [`results/`](results/) | Outputs of our runs, e.g. verification results and coverage tables |

## Deliverables and owners

| # | Deliverable | Output | Owner | Status |
|---|---|---|---|---|
| D1 | Repository setup | This repository | Safiye Nur Narman | Done |
| D2 | List of candidate systems | [docs/candidates.md](docs/candidates.md) | Safiye Nur Narman | Done |
| D3 | Choice of system | [docs/selection.md](docs/selection.md) | Safiye Nur Narman | Done (curl) |
| D4 | Configuration model | [models/schema.md](models/schema.md), [models/curl.yaml](models/curl.yaml) | Safiye Nur Narman | Done |
| D5 | Scripts that build curl and run its tests for a given configuration | [scripts/run_config.sh](scripts/run_config.sh) | Rana Keleş | Done |
| D6 | Coverage numbers for different configurations | [results/coverage_table.md](results/coverage_table.md) | Rana Keleş | Done |
| D7 | Tests written by AI, with before/after coverage | [tests/generated/](tests/generated/), [tests/existing/stage2-analysis.md](tests/existing/stage2-analysis.md) | Fethiye Ebrar Güçlü | Done |
| D8 | Live demo for the advisor | [docs/d8-demo-script.md](docs/d8-demo-script.md) | Fethiye Ebrar Güçlü | Done |
| D9 | Full configurations and a covering array of them | [models/schema.md](models/schema.md#full-configurations), [models/covering-array/](models/covering-array/README.md) | Safiye Nur Narman, Rana Keleş, Fethiye Ebrar Güçlü | In progress (covering array done) |
| D10 | Run every configuration, measure line, function and branch coverage, and the combined coverage of all runs | [results/d10-results.md](results/d10-results.md), [results/coverage_table.md](results/coverage_table.md) | Rana Keleş | Done |
| D11 | A step-by-step loop where an AI writes tests for code that is still not covered | generated tests and a log of every round | Fethiye Ebrar Güçlü, Safiye Nur Narman | Planned |
| D12 | Evaluation: what the AI-written tests added, round by round | evaluation report | Rana Keleş | Planned |
| D13 | Final report and presentation | report and slides | All | Planned |

## Where we are now

We chose curl, built it on Linux and macOS and ran its tests. We wrote a first model of
curl's configuration: 22 build-time options, 6 rules between them (constraints), 3 side
effects and 2 requirements on the build machine. Every rule was confirmed by running
curl's build system, and this check can be repeated with one command
([scripts/verify_curl_constraints.sh](scripts/verify_curl_constraints.sh)).

After that:

- **D5 and D6.** A script builds curl for one configuration, runs all of curl's tests and
  measures code coverage. We compared 8 configurations on a Mac
  ([results/coverage_table.md](results/coverage_table.md)).
- **Stage 2.** None of curl's own tests check any of our 6 rules
  ([tests/existing/stage2-analysis.md](tests/existing/stage2-analysis.md)).
- **D7.** We wrote 4 new tests with AI help, one for each rule that is always silent.
  The number of rules with a test that checks them went from 0 of 6 to 4 of 6
  ([tests/generated/](tests/generated/)).
- **D8.** A live demo of the whole pipeline ([docs/d8-demo-script.md](docs/d8-demo-script.md)).
- **D9 (covering array).** Full configurations are now required (every option gets a
  real value, never `auto`), and a 2-way covering array of 10 full configurations
  replaces the 8 hand-picked ones, generated and independently verified with
  [scripts/covering_array.py](scripts/covering_array.py)
  ([models/covering-array/README.md](models/covering-array/README.md)). Still open in
  D9: a check in `config_tools.py` that rejects a configuration which is not full.

The full story of D1 to D4, including the commands we ran, is in the
[progress report](docs/progress-d1-d4.md).

Next steps (details in [docs/plan-d9-d13.md](docs/plan-d9-d13.md)):

1. D9: add the remaining check to `config_tools.py` that rejects a configuration that
   is not full.
2. D10: run all 10 configurations of the covering array, add branch coverage, and measure
   how much the numbers change between two runs of the same configuration.
3. D11 and D12: let an AI write tests for the branches that are still not covered, one
   round at a time, and evaluate what each round added.
