# Progress Report: D1–D4

This report explains what we have done so far, from setting up the repository to the
first configuration space model of curl: **what** we did, **which commands** we ran, and
**why**. The detailed results live in the linked documents; this page connects them into
one story.

**Status:** D1–D3 are done. D4 (configuration space model) is drafted and verified, and
is waiting for team review. Next is D5 (build-and-test automation).

## Overview

| Step | What we did | Why | Output |
|---|---|---|---|
| D1 | Set up the shared repository and folder structure | One place for code, models, scripts and results, organised by deliverable | This repository |
| D2 | Compared 7 open-source systems | To pick a subject system that fits the project | [candidates.md](candidates.md) |
| D3 | Selected **curl** | Large two-level configuration space, test metadata we can use as ground truth, easy to build | [selection.md](selection.md) |
| Build | Built curl and ran its tests on Linux and macOS | The rest of the project depends on building curl in different configurations | [Section 4](#4-building-curl) |
| Experiments | Turned options off and observed what changed | To see the configuration space and a silent constraint with our own eyes | [Section 5](#5-experiments-seeing-the-configuration-space) |
| D4 | Defined a model format and modelled 22 curl options, 6 constraints and 3 effects | The model is the input for the automation scripts and for all later stages | [models/](../models/) |
| Verification | Confirmed every constraint by running the build system; automated the checks | Our methodology: AI output is only accepted after it is checked with a tool | [curl_verification.md](../models/curl_verification.md), [verify script](../scripts/verify_curl_constraints.sh) |

## 1. Repository setup (D1)

**What we did**

- Created the repository with six folders, each tied to a deliverable:

  | Folder | Purpose | Deliverable |
  |---|---|---|
  | `systems/` | Instructions to fetch and build the studied system | D2–D3 |
  | `models/` | Configuration space models | D4 |
  | `scripts/` | Build, test and verification scripts | D5–D6 |
  | `tests/` | Analysis of existing tests and LLM-generated tests | D7 |
  | `results/` | Outputs of runs and coverage tables | D5–D7 |
  | `docs/` | Candidate list, selection, reports | all |

- Added a short README to every folder that says what will go in it.
- Added a `.gitignore` so curl's source code is not committed.

**Why**

- A fixed structure means everyone knows where to put their work, and the advisor can
  find each deliverable quickly.
- curl's source is large and has its own repository. We do not copy it. Instead, every
  teammate clones the same pinned version (`curl-8_17_0`), so everyone works on
  identical code and results stay reproducible.

## 2. Candidate systems (D2)

**What we did**

- Defined four selection criteria:
  1. a large configuration space,
  2. a usable test suite,
  3. low build effort,
  4. some ground truth to check an AI-generated model against.
- Compared seven systems: curl, SQLite, Apache httpd, BusyBox, ripgrep, Apache ZooKeeper
  and ESLint.
- Analysed curl, ZooKeeper and ESLint at source level. Reviewed the others from their
  documentation.

**Why**

- Different systems express configuration very differently: `configure` flags in C,
  `zoo.cfg` keys in Java, a schema-validated object in JavaScript. Comparing them showed
  what kind of configuration space fits our questions best.
- We did not build all seven. Documentation was enough to rule systems out. We built
  only the system we selected (Section 4).

Full comparison: [candidates.md](candidates.md).

## 3. System selection (D3)

We selected **curl** (C). In short:

- **Two levels of configuration:** about 115 compile-time `configure` flags, plus 273
  command-line options and 291 library options at runtime.
- **Ground truth in the test suite:** curl has about 1,890 tests. Each test states which
  server it needs, and 859 tests also list the build features they require. This tells us
  which configuration affects which tests.
- **Real constraints:** the build system contains rules between options, some of which
  fail silently.
- **Easy to build:** standard tools, about 80 seconds from source to binary.

SQLite was the closest runner-up. Full rationale: [selection.md](selection.md).

## 4. Building curl

**Why we built it before modelling it.** D5 is entirely about building curl in different
configurations and running its tests. If curl did not build on our machines, we wanted to
know immediately, not two weeks later.

### Linux (Ubuntu 24.04, gcc 13.3)

```sh
git clone --depth 1 --branch curl-8_17_0 https://github.com/curl/curl.git systems/curl
cd systems/curl
autoreconf -fi                                  # generate ./configure (needed for a git checkout)
./configure --with-openssl --without-libpsl     # choose options
make -j2                                        # compile
make -C tests                                   # build the test tools
cd tests && perl runtests.pl 1 to 100           # run tests 1-100
```

- Build: about 80 seconds in total.
- Tests: 99 of 99 run tests passed and 1 was skipped. The skipped test needs a debug
  feature (`--enable-curldebug`) that our build did not include. This was our first
  example of a build option deciding whether a test runs.

### macOS (Apple Silicon)

The first attempt failed:

```
vtls/openssl.c:408:23: error: incomplete definition of type 'ASN1_INTEGER' (aka 'struct asn1_string_st')
/opt/homebrew/Cellar/openssl@4/4.1.0/include/openssl/types.h:58:16: note: forward declaration of 'struct asn1_string_st'
```

**Cause.** `brew install openssl` now installs OpenSSL **4.x**. OpenSSL 4 hides some
internal structures that curl 8.17.0 still accesses directly, so curl does not compile
against it.

**Fix.** Use OpenSSL 3 explicitly:

```sh
brew install openssl@3
make distclean
export PKG_CONFIG_PATH="$(brew --prefix openssl@3)/lib/pkgconfig"   # make configure find OpenSSL 3, not 4
./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl
make -j4
./src/curl --version
```

Result:

```
curl 8.17.0-DEV (aarch64-apple-darwin24.6.0) libcurl/8.17.0-DEV OpenSSL/3.5.9 zlib/1.2.12
Protocols: dict file ftp ftps gopher gophers http https imap imaps ipfs ipns ldap ldaps mqtt
           pop3 pop3s rtsp smb smbs smtp smtps telnet tftp ws wss
Features: alt-svc AsynchDNS HSTS HTTPS-proxy IPv6 Largefile libz NTLM SSL threadsafe TLS-SRP UnixSockets
```

**What we learned.**

- The version of a library can itself be a configuration constraint: curl 8.17.0 works
  with OpenSSL 3, not 4.
- The **same command builds a different curl on different machines.** The macOS build
  has LDAP (the LDAP libraries are installed) but no brotli. The Linux build has brotli
  but no LDAP. Some defaults are therefore not fixed values but depend on the machine.
  The model marks them `auto`.

## 5. Experiments: seeing the configuration space

Before writing the model, we changed options by hand to see their effect. These are the
same steps the D5 script will later automate.

### Experiment A: disable a protocol (macOS)

```sh
./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl --disable-ftp
make -j4 && make -C tests
./src/curl --version
cd tests && perl runtests.pl 100
```

Output:

```
Protocols: dict file gopher gophers http https imap imaps ipfs ipns ldap ldaps mqtt pop3
           pop3s rtsp smb smbs smtp smtps telnet tftp ws wss
...
test 0100 SKIPPED: curl lacks ftp server support
TESTINFO: "curl lacks ftp server support" 1 time (100)
TESTFAIL: No tests were performed
```

**What it shows.**

- `ftp` and `ftps` disappeared from the build.
- Test 100 (an FTP test) was skipped automatically. `TESTFAIL: No tests were performed`
  is not a failure of curl. We asked for one test, it was skipped, so nothing ran.
- **Changing one build option changes which tests run at all.** This is the starting
  point of our project and connects the model (D4) to coverage (D6).

### Experiment B: a silent constraint (macOS)

```sh
./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl --disable-ldap --enable-ldaps | grep -i ldap
```

Output:

```
checking whether to support ldap... no
checking whether to support ldaps... LDAP needs to be enabled to support LDAPS
  LDAP:             no      (--enable-ldap / --with-ldap-lib / --with-lber-lib)
  LDAPS:            no      (--enable-ldaps)
```

**What it shows.** We explicitly asked for LDAPS. configure did not stop. It printed one
line and quietly built curl **without** LDAPS. A tester who assumes the build matches the
requested options would test the wrong binary. This is a **silent constraint**, the kind
of option interaction our project is about.

## 6. Configuration space model (D4)

### 6.1 Scope

curl has about 115 compile-time flags. We modelled **22** for the first version:

- **11 protocols:** `http`, `ftp`, `smtp`, `imap`, `pop3`, `telnet`, `tftp`, `dict`,
  `mqtt`, `ldap`, `ldaps`.
- **9 features:** `proxy`, `cookies`, `http-auth`, `mime`, `form-api`, `alt-svc`,
  `hsts`, `ipv6`, `verbose`.
- **2 libraries:** `tls`, `zlib`.

**Why these.** Protocols decide which parts of the test suite can run. The features were
chosen because several of them depend on each other. TLS is mandatory and affects many
other options. A smaller, fully verified model is more useful than a large unchecked
one. More options, and runtime options, can be added later.

### 6.2 Format ([schema.md](../models/schema.md))

Each option records its values, its default, the `configure` flag for each value, and
where in `configure.ac` it is implemented. The main design decisions:

| Decision | Reason |
|---|---|
| A `flags` field maps each value to a command-line argument | The D5 script can turn any configuration into a `./configure` command without extra knowledge |
| `default` can be a value, `auto` or required | Some defaults depend on the machine (Section 4), and TLS has no default at all |
| Constraints record `on_violation: error` or `silent` | Silent constraints are invisible in a normal build and are the most important for testing |
| Every entry has `evidence` (file and lines) and every rule has `verified` (command and result) | Follows our methodology: nothing is accepted on the AI's word alone |
| `effects` are listed separately from constraints | Some consequences (e.g. no TLS means no `https`) concern parts of curl outside the 22 options |

A configuration is just a small YAML file that picks values. The script turns it into
flags:

```yaml
name: no-ftp-no-cookies
values: {tls: openssl, ftp: disabled, cookies: disabled}
```
→ `./configure --with-openssl --disable-ftp --disable-cookies`

### 6.3 Extraction

For each option we read its `AC_ARG_ENABLE` / `AC_ARG_WITH` block in `configure.ac`,
noted the flag name, the default branch and any dependency on other options, and recorded
the exact line range. Constraints were found by following variables such as
`CURL_DISABLE_HTTP` or `SSL_ENABLED` to the places that switch other features off.

### 6.4 Verification

Every constraint and effect was confirmed by running `configure` with a combination that
breaks the rule and checking the exit code and summary. These checks are now a script:

```sh
bash scripts/verify_curl_constraints.sh
```

It runs 13 checks: the 6 constraints, the silent variant of C6, the TLS conflict, the 3
effects and two checks for the MQTT finding. It writes logs and a summary to `results/verification/`, and restores the default
configuration at the end. **Result on Linux: 13 of 13 passed**
([summary](../results/verification/summary.md)). Teammates can run the same script on
their own machines.

### 6.5 Findings

Full table: [curl_verification.md](../models/curl_verification.md).

1. **Silent constraints are common.** 5 of the 6 constraints let the build succeed
   without what was requested.
2. **configure sometimes reports the opposite of what it does.**
   - With `--disable-http --enable-hsts`, it prints *"HSTS... yes"* and then disables
     HSTS.
   - By default it prints *"mqtt... no"*, yet MQTT is built.
3. **The same rule can fail loudly or silently.** Requesting the form API without MIME
   stops the build. Leaving the form API at its default drops it quietly.
4. **Defaults depend on the machine.** LDAP and brotli differ between our macOS and
   Linux builds.
5. **Configuration decides which tests run.** Disabling a protocol skips every test that
   needs it.

Findings 1 and 2 matter most for our research question. An AI, or a person, that reads
configure's messages instead of checking the actual result will build a wrong model of
the configuration space.

## How AI was used

In line with the project's topic, we used an AI assistant (Claude) throughout:

- reading `configure.ac` and proposing option and constraint entries,
- drafting the documentation,
- writing the verification script.

Following our methodology, no entry was accepted on the AI's word. Each one points to
specific source lines and was confirmed by running the build system, on a Linux machine
and on a teammate's Mac. The two silent behaviours in finding 2 are examples where trusting
tool output (configure's messages) without checking the actual result would have produced
a wrong model.

## Repository after D4

| File | Content |
|---|---|
| [README.md](../README.md) | Project overview, deliverables and owners, status |
| [docs/candidates.md](candidates.md) | D2: candidates, criteria, build check |
| [docs/selection.md](selection.md) | D3: why curl |
| [docs/progress-d1-d4.md](progress-d1-d4.md) | This report |
| [systems/README.md](../systems/README.md) | How to fetch and build curl |
| [models/schema.md](../models/schema.md) | D4: model format |
| [models/curl.yaml](../models/curl.yaml) | D4: curl model |
| [models/curl_verification.md](../models/curl_verification.md) | D4: verification results and findings |
| [scripts/verify_curl_constraints.sh](../scripts/verify_curl_constraints.sh) | Automated constraint checks |
| [results/verification/summary.md](../results/verification/summary.md) | Latest check results |

## Next steps

- **Team review of D4:** confirm the 22 options, and run the verification script on each
  teammate's machine.
- **D5:** `scripts/run_config.sh <configuration.yaml>`. It reads a configuration, turns it
  into `configure` flags using `models/curl.yaml`, builds curl, runs the tests (or a
  selected range) and writes the results to `results/<configuration-name>/`.

**Questions for the advisor:**

- Is a compile-time-only first model acceptable, with runtime options added later?
- How many configurations should D6 compare?
