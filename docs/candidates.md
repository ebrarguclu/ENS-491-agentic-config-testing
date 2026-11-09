# D2 — Candidate Systems

We looked for open-source systems that are **highly configurable**, have a **usable test
suite**, and **build without much effort**, across different languages and configuration
mechanisms. The selected system and the full rationale are in
[selection.md](selection.md).

## Selection criteria

1. **Configuration space:** many options, ideally at both compile time and runtime.
2. **Test suite:** an existing suite we can run per configuration and measure coverage on.
3. **Build effort:** builds from source with standard tools on our machines.
4. **Ground truth:** some official source (documentation, build system, test metadata)
   we can use to verify a configuration space model produced by AI.

## Candidates

| System | Language | Compile-time options | Runtime options | Test suite | Build effort | How we evaluated it |
|---|---|---|---|---|---|---|
| **[curl](https://github.com/curl/curl)** ✅ | C | ~115 `configure` flags (69 `--enable/--disable`, 46 `--with/--without`) | 273 CLI options, 291 libcurl `CURLOPT_*` options | ~1,890 data-driven tests; 859 declare required build features | Easy: autotools + OpenSSL headers; ~80 s from source to binary | Source analysis + **built and tested** ([below](#build-check-curl)) |
| [Apache ZooKeeper](https://github.com/apache/zookeeper) | Java | None | ~40 `zoo.cfg` keys (`QuorumPeerConfig.java`) | JUnit (Maven) | Medium: JDK + Maven | Source analysis |
| [ESLint](https://github.com/eslint/eslint) | JavaScript | None | Flat config: 7 top-level keys with nested schemas (`flat-config-schema.js`) | Large unit test suite (`npm test`) | Easy: `npm install` | Source analysis |
| [SQLite](https://github.com/sqlite/sqlite) | C | Many `SQLITE_*` macros (`OMIT`, `ENABLE`, `DEFAULT`, `MAX`) | PRAGMAs | Large Tcl suite; option checks via `ifcapable` | Easy: C compiler + Tcl | Documentation review |
| [BusyBox](https://git.busybox.net/busybox) | C | Kconfig; several hundred to over a thousand options depending on version | Applet CLI flags | `testsuite/` shell tests | Easy on Linux, problematic on macOS | Documentation review |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Rust | A few Cargo features (e.g. `pcre2`) | Many CLI flags | `cargo test` | Very easy | Documentation review |
| [Apache httpd](https://github.com/apache/httpd) | C | `configure --enable-<module>` | `httpd.conf` directives | Separate Perl framework (Apache::Test) | Harder: APR, APR-util, PCRE | Documentation review |

curl counts are taken from the `curl-8_17_0` source tree (see
[selection.md](selection.md#1-a-large-two-level-configuration-space) for where each number
comes from).

## Example findings from source analysis

Each finding was confirmed in the source code, not taken from model output alone.

- **curl:** enabling LDAPS while LDAP is disabled does not fail. `configure` prints
  *"LDAP needs to be enabled to support LDAPS"*, silently turns LDAPS off, and continues
  (`configure.ac`, lines 788–817).
- **ZooKeeper:** `clientPortAddress` requires `clientPort` to also be set, and `tickTime`
  implicitly determines the default `minSessionTimeout` / `maxSessionTimeout`.
- **ESLint:** legacy eslintrc-style keys are explicitly rejected in flat config, and
  sibling options such as `reportUnusedDisableDirectives` and `reportUnusedInlineConfigs`
  treat boolean values inconsistently.

## Build check: curl

We built and tested the selected system before committing to it.

| | |
|---|---|
| Version | git tag `curl-8_17_0` |
| Environment | Ubuntu 24.04.5, gcc 13.3.0, Perl 5.38, 2 CPU cores |
| Dependencies | autoconf, automake, libtool (needed for a git checkout), OpenSSL and zlib dev headers, Perl (tests) |
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

The build reports its enabled protocols and features (`curl --version`):

```
Protocols: dict file ftp ftps gopher gophers http https imap imaps ipfs ipns mqtt pop3
           pop3s rtsp smb smbs smtp smtps telnet tftp ws wss
Features:  alt-svc AsynchDNS brotli HSTS HTTPS-proxy IPv6 Largefile libz NTLM SSL
           threadsafe TLS-SRP UnixSockets
```

Notes for teammates building on their own machines:

- `configure` refuses to run until a TLS backend is chosen. Use `--with-openssl`, or
  `--without-ssl` for a build without TLS.
- If `libpsl` is not installed, add `--without-libpsl`.
- On Windows, use WSL.
- Each test takes about one second. Run a range (e.g. `1 to 100`) while developing
  instead of the full suite.
