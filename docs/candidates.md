# D2 — Candidate Systems

We compared seven open-source systems before choosing the one we will work on for the
rest of the project. This page explains what each system is, how it can be configured,
what its test suite looks like, and why it did or did not fit our project.

**Result:** we selected **curl**. The full rationale is in [selection.md](selection.md).

## Key terms

- **Compile-time option:** a choice made *when the program is built*. It decides which
  code is included in the binary at all. Example: building curl with `--disable-ftp`
  produces a curl that has no FTP code inside it.
- **Runtime option:** a choice made *when the program is run*, through command-line
  flags or a configuration file. Example: `curl --compressed https://example.com`.
- **Test suite:** the tests that come with the project and are used by its own
  developers.
- **Ground truth:** an official, reliable source (documentation, build files, test
  metadata) that we can compare an AI-generated configuration model against.

## What we looked for

1. **A large configuration space:** many options, ideally both compile-time and runtime.
2. **A usable test suite:** tests we can run once per configuration and measure
   coverage on.
3. **Low build effort:** the system should build from source with standard tools on our
   own machines.
4. **Ground truth:** some official source we can use to check whether an AI got the
   configuration space right.

## At a glance

| System | Language | Compile-time options | Runtime options | Build effort | Decision |
|---|---|---|---|---|---|
| **curl** | C | Yes, ~115 | Yes, 273 CLI + 291 API | Easy (verified) | ✅ Selected |
| SQLite | C | Yes, many | Yes, PRAGMAs | Easy | Runner-up |
| Apache httpd | C | Yes, per module | Yes, `httpd.conf` | Hard | Not selected |
| BusyBox | C | Yes, hundreds | Yes, per-tool flags | Easy on Linux only | Not selected |
| ripgrep | Rust | Very few | Yes, many | Very easy | Not selected |
| Apache ZooKeeper | Java | No | Yes, ~40 | Medium | Not selected |
| ESLint | JavaScript | No | Yes, nested config | Easy | Not selected |

curl numbers are counted on the `curl-8_17_0` source tree. See
[selection.md](selection.md#1-a-large-two-level-configuration-space) for exactly where
each number comes from.

## Candidate details

### curl ✅ selected

**What it is.** A command-line tool and library (libcurl) for transferring data over the
internet. It supports more than 20 protocols, including HTTP(S), FTP, SMTP and IMAP, and
is built into a very large number of devices and applications.

**How it is configured.**
- *Compile-time:* before building, `./configure` flags decide which protocols and
  features are compiled in and which libraries are used. Examples: `--disable-ftp`,
  `--disable-cookies`, `--with-openssl`. There are about 115 such flags.
- *Runtime:* 273 command-line options (e.g. `--proxy`, `--compressed`) and 291 options
  in the libcurl API (`curl_easy_setopt`).

**Test suite.** About 1,890 test cases. Each test is a small text file that describes
the command to run, the server response and the expected result. 859 of them also list
the build features they need (e.g. `proxy`, `SSL`, `cookies`). If a build does not have
a required feature, the test runner skips that test automatically.

**Example from the source.** Enabling LDAPS while LDAP is disabled does not cause an
error. `configure` only prints *"LDAP needs to be enabled to support LDAPS"*, silently
turns LDAPS off and continues (`configure.ac`, lines 788–817). This is exactly the kind
of hidden interaction between options that our project is about.

**Fit for our project.**
- ➕ Both compile-time and runtime options, at a large scale.
- ➕ The tests themselves state which features they need, which gives us ground truth
  for analysing the existing test suite (Stage 2).
- ➕ Real constraints between options are written in the build system.
- ➕ We built it and ran its tests successfully ([build check](#build-check-curl)).
- ➖ Some tests need extra local servers, and the full suite takes a long time, so we
  will run selected ranges of tests during development.

### SQLite (runner-up)

**What it is.** A small SQL database engine that is compiled directly into applications
instead of running as a separate server. It is used in phones, browsers and many
desktop programs.

**How it is configured.**
- *Compile-time:* C macros passed to the compiler. Examples:
  `-DSQLITE_OMIT_ALTERTABLE` removes the `ALTER TABLE` command, and
  `-DSQLITE_ENABLE_FTS5` adds full-text search.
- *Runtime:* `PRAGMA` statements, e.g. `PRAGMA journal_mode=WAL`.

**Test suite.** A very large test suite written in Tcl. Tests check which features are
available with `ifcapable` blocks inside the test scripts.

**Fit for our project.**
- ➕ Easy to build, with many well-documented compile-time options.
- ➕ SQLite's own documentation says that not every combination of options can be
  tested, which matches our motivation.
- ➖ Feature requirements are written inside Tcl code rather than as separate test
  metadata, so they are harder to extract reliably.
- ➖ Fewer runtime options than curl.

### Apache httpd

**What it is.** The Apache HTTP Server, one of the most widely used web servers.

**How it is configured.**
- *Compile-time:* `./configure --enable-<module>` chooses which modules are built, e.g.
  `--enable-ssl`.
- *Runtime:* directives in the `httpd.conf` file, e.g. `Listen 80` or `LoadModule`.

**Test suite.** A separate Perl-based framework (Apache::Test), maintained apart from
the server source code.

**Fit for our project.**
- ➕ Realistic system with both compile-time and runtime options.
- ➖ Harder to build: needs the APR, APR-util and PCRE libraries.
- ➖ Setting up the separate test framework adds significant effort.

### BusyBox

**What it is.** A single small program that bundles many standard Unix tools (`ls`,
`cp`, `grep`, …). It is widely used in embedded Linux systems such as routers.

**How it is configured.**
- *Compile-time:* a Kconfig menu (the same system the Linux kernel uses, opened with
  `make menuconfig`) to choose which tools and features to include. Depending on the
  version, there are several hundred to over a thousand options.
- *Runtime:* the command-line flags of each tool.

**Test suite.** Shell-script tests in the `testsuite/` folder.

**Fit for our project.**
- ➕ A large, formally described configuration space with explicit dependencies.
- ➖ Builds reliably mainly on Linux; building on macOS is problematic.
- ➖ The test suite is fairly limited compared to the size of the configuration space.

### ripgrep

**What it is.** A fast text-search tool written in Rust, similar to `grep`.

**How it is configured.**
- *Compile-time:* a few Cargo features, e.g. `pcre2`, which adds a second regular
  expression engine.
- *Runtime:* many command-line flags, e.g. `--ignore-case` or `--hidden`.

**Test suite.** Run with `cargo test`.

**Fit for our project.**
- ➕ Very easy to build, with clean and readable code.
- ➖ Only a handful of compile-time options, so the compile-time space is too small
  for our purposes.

### Apache ZooKeeper

**What it is.** A coordination service for distributed systems. Clusters use it to
share configuration, naming and synchronisation information.

**How it is configured.**
- *Compile-time:* none.
- *Runtime:* about 40 `key=value` settings in the `zoo.cfg` file, read at startup
  (`QuorumPeerConfig.java`). Examples: `tickTime`, `clientPort`, `dataDir`.

**Test suite.** JUnit tests, run with Maven.

**Example from the source.** `clientPortAddress` only works if `clientPort` is also set,
and `tickTime` silently determines the default values of `minSessionTimeout` and
`maxSessionTimeout`.

**Fit for our project.**
- ➕ Realistic constraints between runtime settings.
- ➖ No compile-time options.
- ➖ Long-running test suite and a heavier Java/Maven setup.

### ESLint

**What it is.** A tool that checks JavaScript code for problems and style issues.

**How it is configured.**
- *Compile-time:* none.
- *Runtime:* a configuration file (`eslint.config.js`, the "flat config") that is a
  JavaScript object with 7 top-level keys and nested sub-settings, validated against a
  schema (`flat-config-schema.js`).

**Test suite.** A large unit test suite, run with `npm test`.

**Example from the source.** Legacy (eslintrc-style) keys are explicitly rejected in the
flat config, and similar sibling options such as `reportUnusedDisableDirectives` and
`reportUnusedInlineConfigs` treat boolean values inconsistently.

**Fit for our project.**
- ➕ Easy to install and run.
- ➖ No compile-time options.
- ➖ Its configuration is nested data rather than a set of options with values, which
  is harder to model as a classic configuration space.

## Build check: curl

Before committing to curl, we built it from source and ran part of its test suite.

| | |
|---|---|
| Version | git tag `curl-8_17_0` |
| Environment | Ubuntu 24.04.5, gcc 13.3.0, Perl 5.38, 2 CPU cores |
| Dependencies | autoconf, automake, libtool (needed for a git checkout), OpenSSL and zlib development headers, Perl (for tests) |
| Configuration | `./configure --with-openssl --without-libpsl` (libpsl was not installed, so it was disabled explicitly) |

| Step | Command | Result | Time |
|---|---|---|---|
| Generate build files | `autoreconf -fi` | OK | 7 s |
| Configure | `./configure --with-openssl --without-libpsl` | OK | 17 s |
| Compile | `make -j2` | OK | 57 s |
| Build test tools | `make -C tests` | OK | — |
| Run tests | `cd tests && perl runtests.pl 1 to 100` | 99 of 99 run tests passed, 1 skipped | 105 s |

The skipped test (96) needs memory tracking, which is only compiled in with
`--enable-curldebug`. Our default build did not include it, so the runner skipped the
test. This is a first, concrete example of what the project is about: **a build option
decides which tests run at all.**

The build reports which protocols and features it contains (`curl --version`):

```
Protocols: dict file ftp ftps gopher gophers http https imap imaps ipfs ipns mqtt pop3
           pop3s rtsp smb smbs smtp smtps telnet tftp ws wss
Features:  alt-svc AsynchDNS brotli HSTS HTTPS-proxy IPv6 Largefile libz NTLM SSL
           threadsafe TLS-SRP UnixSockets
```

### Notes for building on your own machine

- `configure` refuses to run until a TLS library is chosen. Use `--with-openssl`, or
  `--without-ssl` for a build without TLS.
- If `libpsl` is not installed, add `--without-libpsl`.
- On macOS, use Homebrew's `openssl@3`, not the default `openssl` (now 4.x, which curl
  8.17.0 does not compile against):
  `./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl`
- On Windows, use WSL.
- Each test takes about one second. While developing, run a range of tests (e.g.
  `1 to 100`) instead of the full suite.
