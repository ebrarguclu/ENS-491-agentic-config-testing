# D3 — System Selection: curl

**Decision:** We use **[curl](https://github.com/curl/curl)** (C, pinned to release tag
`curl-8_17_0`) as the subject system for the rest of the project.

The candidates we considered are listed in [candidates.md](candidates.md).

## Summary

We chose curl because it is a widely used C project that can be configured both when it
is built (`configure` flags that turn protocols and features on or off and select
libraries) and when it runs (hundreds of command-line and API options). Its test suite
of almost 1,900 test cases declares, test by test, which build features each test
needs. This gives us a ready-made way to check which configurations affect which
tests. It builds with standard tools, already supports code-coverage builds, and
contains real option constraints we can use to validate our configuration space model.

## Rationale

### 1. A large, two-level configuration space

curl exposes both kinds of options our project studies. Counted on the source of
`curl-8_17_0`:

| Level | Mechanism | Count | Where |
|---|---|---|---|
| Compile-time | `--enable-*` / `--disable-*` flags | 69 | `configure.ac`, `acinclude.m4`, `m4/*.m4` (`AC_ARG_ENABLE`) |
| Compile-time | `--with-*` / `--without-*` flags | 46 | same files (`AC_ARG_WITH`) |
| Runtime | `curl` command-line options | 273 | `docs/cmdline-opts/*.md` |
| Runtime | libcurl `curl_easy_setopt` options | 291 | `include/curl/curl.h` (`CURLOPT(...)`) |

Compile-time flags change which code is compiled into the binary. A protocol or feature
that is disabled at build time is not just "off", it does not exist in that build. This
is the setting where option interactions are hardest to test, because every combination
is a different binary.

### 2. The test suite tells us what each test needs

Each curl test is a data file (`tests/data/testNNNN`). It states the server it needs
(e.g. `http`, `ftp`) and, in 859 of 1,890 tests, an explicit `<features>` list
(e.g. `proxy`, `SSL`, `cookies`, `IPv6`; 80 distinct keywords). When a build lacks a
required feature, the test runner skips that test automatically.

This matters for every later stage:

- **Stage 2 (existing test analysis):** the test-to-feature mapping is written down in
  the tests themselves, so we can check an LLM's answer to "which tests exercise which
  options?" against ground truth.
- **D6 (coverage):** disabling a feature removes both its code and the tests that need
  it. Coverage differences between configurations will be visible and explainable.
- **Demo:** "change the configuration → different tests run → coverage changes" is easy
  to show live.

### 3. Real constraints are already in the build system

`configure.ac` encodes constraints between options. Some fail loudly, some are silent:

| Constraint | Behaviour | Source |
|---|---|---|
| A TLS backend must be chosen, or TLS explicitly disabled | `configure` stops with *"select TLS backend(s) or disable TLS with --without-ssl"* | `configure.ac` line 433 |
| `--without-ssl` cannot be combined with an explicit TLS library | `configure` stops with an error | `configure.ac` line 2027 |
| LDAPS requires LDAP | `--enable-ldaps` with LDAP disabled **silently** turns LDAPS off; `configure` only prints *"LDAP needs to be enabled to support LDAPS"* and continues | `configure.ac` lines 788–817 |
| HTTP/2 requires nghttp2 | without `--with-nghttp2`, HTTP/2 is reported as unavailable | `configure` summary |

Silent constraints like the LDAPS case are exactly what we want an AI agent to discover
and a tester to cover. They are also easy to verify against the source, which matches
our methodology of only accepting claims that are confirmed by a deterministic tool.

### 4. It builds easily and supports coverage

We built `curl-8_17_0` from a git checkout on Ubuntu 24.04 (gcc 13.3, 2 CPU cores)
with only standard packages. Timings and test results are in
[candidates.md](candidates.md#build-check-curl). The steps were:

```sh
autoreconf -fi
./configure --with-openssl --without-libpsl
make -j2
make -C tests
cd tests && perl runtests.pl 1 to 100
```

curl also ships a `--enable-code-coverage` configure flag (`m4/curl-functions.m4`), and
its test documentation describes gcov-based coverage. This means D6 does not need any
custom tooling to start.

### 5. A realistic subject

curl is mature, actively maintained and one of the most widely deployed software
components in use. Results on curl are meaningful beyond a toy example. Its configuration also changes the attack surface,
because disabling protocols is a common hardening practice.

## Why not the others

| System | Main reason it was not selected |
|---|---|
| SQLite | Closest runner-up. Its tests express option checks inside Tcl scripts (`ifcapable` blocks) rather than as declarative per-test metadata, which is harder to extract reliably; it also has fewer runtime options, and the team had already started source-level analysis of curl. |
| Apache ZooKeeper | Runtime options only (no compile-time variability); long-running JUnit suite. |
| ESLint | Runtime / schema-based options only; no compile-time variability. |
| BusyBox | Large Kconfig space, but builds reliably only on Linux and its test suite is limited. |
| ripgrep | Very few compile-time options (Cargo features). |
| Apache httpd | Heavier build (APR, PCRE) and a separate Perl test framework. |

## Scope for the next step (D4)

We will not model all ~115 configure flags at once. The first configuration space model
(`models/curl.yaml`) will cover a focused subset of compile-time options:

- a few protocols (e.g. `ftp`, `smtp`, `imap`, `ldap`/`ldaps`),
- feature switches (e.g. `cookies`, `ipv6`, `proxy`, `verbose`),
- the TLS backend choice,

together with the constraints above. Runtime options will be added once the build and
test scripts (D5) work.
