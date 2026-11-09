# Candidate Systems (D2)

Before starting the real work, we needed one open-source program to study for the rest of
the project. We compared seven candidates. This page explains how we compared them, what
each one is like, and why we ended up with **curl**. The full reasoning behind the final
choice is in [selection.md](selection.md).

If a term is unfamiliar, see [Key terms](../README.md#key-terms) in the main README.

## How we compared them

| Criterion | The question we asked | Why it matters |
|---|---|---|
| Configuration space | Does it have many options, ideally both at build time and at run time? | No options, no interactions to study |
| Test suite | Does it come with tests we can run for each configuration? | We need tests to measure coverage (D6) and to add AI-written tests to (D7) |
| Build effort | Can we build it ourselves with normal tools? | We will build it many times with different options (D5) |
| Ground truth | Is there an official source to check an AI's answers against? | Without it we cannot say whether the AI was right (Stage 1 and 2) |

## Comparison

| System | Language | Build-time options | Run-time options | Build effort | Decision |
|---|---|---|---|---|---|
| **curl** | C | Yes, about 115 | Yes, 273 command-line + 291 library | Easy (we tried it) | **Selected** |
| SQLite | C | Yes, many | Yes, `PRAGMA` commands | Easy | Runner-up |
| Apache httpd | C | Yes, one per module | Yes, `httpd.conf` | Hard | Not selected |
| BusyBox | C | Yes, hundreds | Yes, flags of each tool | Easy, but only on Linux | Not selected |
| ripgrep | Rust | Very few | Yes, many | Very easy | Not selected |
| Apache ZooKeeper | Java | None | Yes, about 40 | Medium | Not selected |
| ESLint | JavaScript | None | Yes, a nested config file | Easy | Not selected |

The curl numbers were counted in the source code of version `curl-8_17_0`.
[selection.md](selection.md#1-it-has-a-big-configuration-space-at-two-levels) shows exactly
where each number comes from.

We studied curl, ZooKeeper and ESLint at source-code level. For the other four we read
their documentation, which was enough to see whether they fit.

## The systems one by one

### curl (selected)

curl is a tool and a library (libcurl) for downloading and uploading data over the
internet. It speaks more than 20 protocols, such as HTTP(S), FTP, SMTP and IMAP, and it is
built into a huge number of devices and applications.

| | Examples |
|---|---|
| Build-time options (about 115) | `--disable-ftp` builds curl without FTP. `--with-openssl` chooses OpenSSL for encryption |
| Run-time options (273 + 291) | `curl --proxy ...`, `curl --compressed ...`, or the same settings through the library API |
| Tests | About 1,890 tests. Each test is a small text file. 859 of them also list the features they need, and a test is skipped automatically if the build does not have them |

> Hidden rule we found: if you ask for LDAPS but turn LDAP off, curl's build does not
> fail. It prints one line, *"LDAP needs to be enabled to support LDAPS"*, and quietly
> builds curl without LDAPS (`configure.ac`, lines 788 to 817).

| Good for our project | Harder for our project |
|---|---|
| Many options, both at build time and at run time | Some tests need extra local servers |
| Tests say which features they need, so we know which configuration affects which test | Running all tests takes a long time, so we run selected ranges while developing |
| Real rules between options, some of them silent | |
| We built it and ran its tests successfully ([see below](#build-check-curl)) | |

### SQLite (runner-up)

SQLite is a small SQL database that lives inside other programs instead of running as a
separate server. It is used in phones, web browsers and many desktop applications.

| | Examples |
|---|---|
| Build-time options | `-DSQLITE_OMIT_ALTERTABLE` removes the `ALTER TABLE` command. `-DSQLITE_ENABLE_FTS5` adds full-text search |
| Run-time options | `PRAGMA` commands, for example `PRAGMA journal_mode=WAL` |
| Tests | A very large test suite written in Tcl. Tests check which features exist with `ifcapable` blocks inside the test code |

| Good for our project | Harder for our project |
|---|---|
| Easy to build, many well-documented build-time options | Feature requirements are hidden inside Tcl code, so they are harder to extract reliably |
| SQLite's own documentation admits that not every combination of options can be tested | Fewer run-time options than curl |

### Apache httpd

The Apache HTTP Server is one of the most widely used web servers.

| | Examples |
|---|---|
| Build-time options | `./configure --enable-ssl` and similar flags choose which modules are built |
| Run-time options | Lines in the `httpd.conf` file, for example `Listen 80` or `LoadModule ...` |
| Tests | A separate Perl-based test framework (Apache::Test), kept apart from the server code |

| Good for our project | Harder for our project |
|---|---|
| Realistic, with options at both levels | Needs extra libraries to build (APR, APR-util, PCRE) |
| | Setting up the separate test framework takes a lot of effort |

### BusyBox

BusyBox packs many standard Unix tools (`ls`, `cp`, `grep` and so on) into one small
program. It is common in small devices such as routers.

| | Examples |
|---|---|
| Build-time options | A menu (`make menuconfig`, the same system the Linux kernel uses) to pick tools and features. Several hundred to over a thousand options, depending on the version |
| Run-time options | The command-line flags of each tool |
| Tests | Shell-script tests in the `testsuite/` folder |

| Good for our project | Harder for our project |
|---|---|
| Very large configuration space with clearly written dependencies | Builds reliably only on Linux, not on macOS |
| | Small test suite compared to the number of options |

### ripgrep

ripgrep is a fast text-search tool written in Rust, similar to `grep`.

| | Examples |
|---|---|
| Build-time options | A few Cargo features, for example `pcre2`, which adds a second regular-expression engine |
| Run-time options | Many flags, for example `--ignore-case` or `--hidden` |
| Tests | Run with `cargo test` |

| Good for our project | Harder for our project |
|---|---|
| Very easy to build, clean and readable code | Only a handful of build-time options, too few for our purposes |

### Apache ZooKeeper

ZooKeeper helps groups of servers (clusters) share settings and stay in sync.

| | Examples |
|---|---|
| Build-time options | None |
| Run-time options | About 40 `key=value` settings in `zoo.cfg`, read at start-up (`QuorumPeerConfig.java`), such as `tickTime`, `clientPort`, `dataDir` |
| Tests | JUnit tests, run with Maven |

> Hidden rule we found: `clientPortAddress` only works if `clientPort` is also set, and
> `tickTime` silently decides the default values of `minSessionTimeout` and
> `maxSessionTimeout`.

| Good for our project | Harder for our project |
|---|---|
| Realistic rules between settings | No build-time options at all |
| | Tests take long, and the Java/Maven setup is heavier |

### ESLint

ESLint checks JavaScript code for mistakes and style problems.

| | Examples |
|---|---|
| Build-time options | None |
| Run-time options | A config file (`eslint.config.js`) holding a JavaScript object with 7 top-level keys and nested settings, checked against a schema (`flat-config-schema.js`) |
| Tests | A large unit test suite, run with `npm test` |

> Hidden rule we found: old-style (eslintrc) keys are rejected in the new config format,
> and two similar options, `reportUnusedDisableDirectives` and
> `reportUnusedInlineConfigs`, treat `true`/`false` values differently.

| Good for our project | Harder for our project |
|---|---|
| Easy to install and run | No build-time options |
| | Its settings are nested data rather than a list of options with values, which is hard to describe as a classic configuration space |

## Build check: curl

Before committing to curl, we built it and ran part of its tests to make sure this is
actually possible on our machines.

| | |
|---|---|
| Version | `curl-8_17_0` (a git tag, so everyone uses exactly the same code) |
| Machine | Ubuntu 24.04.5, gcc 13.3.0, Perl 5.38, 2 CPU cores |
| Needed tools | autoconf, automake, libtool (because we build from a git checkout), OpenSSL and zlib development files, Perl (for the tests) |
| Options used | `./configure --with-openssl --without-libpsl` (libpsl was not installed, so we turned it off) |

| Step | Command | Result | Time |
|---|---|---|---|
| Prepare the build files | `autoreconf -fi` | OK | 7 s |
| Choose the options | `./configure --with-openssl --without-libpsl` | OK | 17 s |
| Compile | `make -j2` | OK | 57 s |
| Build the test tools | `make -C tests` | OK | |
| Run tests 1 to 100 | `cd tests && perl runtests.pl 1 to 100` | 99 passed, 1 skipped | 105 s |

The skipped test (number 96) needs a debugging feature that only exists when curl is
built with `--enable-curldebug`. Our build did not include it, so the test was skipped.
This was our first small example of the main idea of the project: **a build option
decides whether a test runs at all.**

The finished curl lists what it contains (`curl --version`):

```
Protocols: dict file ftp ftps gopher gophers http https imap imaps ipfs ipns mqtt pop3
           pop3s rtsp smb smbs smtp smtps telnet tftp ws wss
Features:  alt-svc AsynchDNS brotli HSTS HTTPS-proxy IPv6 Largefile libz NTLM SSL
           threadsafe TLS-SRP UnixSockets
```

### Tips for building on your own machine

- `configure` will not start until you choose an encryption (TLS) library. Use
  `--with-openssl`, or `--without-ssl` if you want no encryption at all.
- If `libpsl` is not installed, add `--without-libpsl`.
- On macOS, use Homebrew's `openssl@3`, not the default `openssl`. The default is now
  version 4, and curl 8.17.0 does not compile with it:
  `./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl`
- On Windows, use WSL.
- Each test takes about one second. While developing, run a range such as `1 to 100`
  instead of all tests.
