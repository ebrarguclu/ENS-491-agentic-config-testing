# Agentic Config Testing

ENS 491/492 Graduation Project, Sabancı University
Project #516: *Agentic AI for Detecting and Testing Configuration Option Interactions*

| | |
|---|---|
| Team | Fethiye Ebrar Güçlü, Rana Keleş, Safiye Nur Narman |
| Advisor | Cemal Yılmaz |
| System we study | [curl](https://github.com/curl/curl), version `curl-8_17_0` ([why curl?](docs/selection.md)) |
| Where we are | D1 to D4 finished (D4 is a draft under review), D5 is next |

New to the project? Start with [Key terms](#key-terms), then read the
[progress report](docs/progress-d1-d4.md). It explains everything we have done so far
step by step.

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
| Interaction coverage | How many option *combinations* the tests actually exercise | "FTP off + cookies on was tested" |
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
| D4 | Configuration model | [models/schema.md](models/schema.md), [models/curl.yaml](models/curl.yaml) | Safiye Nur Narman | Draft, in review |
| D5 | Scripts that build curl and run its tests for a given configuration | [scripts/run_config.sh](scripts/run_config.sh) | Rana Keleş | Done |
| D6 | Coverage numbers for different configurations | [results/coverage_table.md](results/coverage_table.md) | Rana Keleş | Done |
| D7 | Tests written by AI, with before/after coverage | `tests/generated/` | Fethiye Ebrar Güçlü | Planned |
| D8 | Live demo for the advisor | | Fethiye Ebrar Güçlü | Planned |

## Where we are now

We chose curl, built it on Linux and macOS and ran its tests. We then wrote a first model
of curl's configuration: 22 build-time options, 6 rules between them and 3 side effects.
Every rule was confirmed by running curl's build system, and this check can be repeated
with one command ([scripts/verify_curl_constraints.sh](scripts/verify_curl_constraints.sh)).

The full story, including the commands we ran, is in the
[progress report](docs/progress-d1-d4.md).

Next steps:

1. Review the model as a team.
2. Write the D5 script that takes a configuration, builds curl with it and runs the tests.
