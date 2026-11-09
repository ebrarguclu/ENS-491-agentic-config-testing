# Why We Chose curl (D3)

We chose **[curl](https://github.com/curl/curl)**, version `curl-8_17_0`, as the one
system we study for the rest of the project. A fixed version (a git tag) means everyone in
the team works on exactly the same code.

In short: curl has many options both when it is built and when it is run, its tests say
which features they need, its build system contains real (and sometimes silent) rules
between options, and it is easy to build. The sections below explain each reason. The
other candidates are described in [candidates.md](candidates.md).

## Five reasons

### 1. It has a big configuration space at two levels

Our project is about option combinations, so we need a program with many options. curl
has options both when you build it and when you run it. We counted them in the source
code of `curl-8_17_0`:

| When | How you set it | How many | Where we counted |
|---|---|---|---|
| Build time | `--enable-...` / `--disable-...` flags | 69 | `configure.ac`, `acinclude.m4`, `m4/*.m4` (`AC_ARG_ENABLE`) |
| Build time | `--with-...` / `--without-...` flags | 46 | the same files (`AC_ARG_WITH`) |
| Run time | `curl` command-line options | 273 | `docs/cmdline-opts/*.md` |
| Run time | libcurl library options (`curl_easy_setopt`) | 291 | `include/curl/curl.h` (`CURLOPT(...)`) |

Build-time options are the most interesting ones for us. When a protocol is turned off
at build time, it is not just switched off. Its code is not in the program at all. Every
combination of build-time options is therefore a different program, which is exactly why
these combinations are so hard to test.

### 2. Its tests tell us what they need

Each curl test is a small text file (`tests/data/testNNNN`). It says which kind of server
it needs (for example `http` or `ftp`), and 859 of the 1,890 tests also contain a
`<features>` list, such as `proxy`, `SSL`, `cookies` or `IPv6` (80 different keywords in
total). If curl was built without one of these, the test runner skips the test
automatically.

This helps us in several later steps:

| Step | How it helps |
|---|---|
| Stage 2, analysing existing tests | The link between tests and features is already written down. When we ask an AI "which tests use which options?", we can check its answer against these files |
| D6, coverage | Turning a feature off removes both its code and the tests that need it, so coverage differences between configurations can be explained |
| Demo | "Change the configuration, see different tests run, see coverage change" is easy to show live |

### 3. It already contains real rules between options

curl's build script (`configure.ac`) contains rules about which options can be combined.
Some of them stop the build with an error. Others are silent: the build succeeds, but
without what you asked for.

| Rule | What happens | Where |
|---|---|---|
| You must choose an encryption (TLS) library, or say you want none | `configure` stops: *"select TLS backend(s) or disable TLS with --without-ssl"* | `configure.ac`, line 433 |
| "No TLS" and "use OpenSSL" cannot be given together | `configure` stops with an error | `configure.ac`, line 2027 |
| LDAPS needs LDAP | If LDAP is off, `--enable-ldaps` is ignored without an error. `configure` only prints *"LDAP needs to be enabled to support LDAPS"* | `configure.ac`, lines 788 to 817 |
| HTTP/2 needs the nghttp2 library | Without `--with-nghttp2`, HTTP/2 is simply not available | `configure` summary |

Silent rules like the LDAPS one are exactly what we want an AI agent to discover and a
tester to cover. They are also easy to check against the source code, which fits our main
rule: nothing is accepted until it has been checked with a tool.

### 4. It is easy to build and supports coverage

We built `curl-8_17_0` on Ubuntu 24.04 using only standard packages. From source code to
a working program took about 80 seconds, and 99 of 99 tests in our sample passed. The
details are in [candidates.md](candidates.md#build-check-curl). The commands were:

```sh
autoreconf -fi                                 # prepare the build files
./configure --with-openssl --without-libpsl    # choose the options
make -j2                                       # compile
make -C tests                                  # build the test tools
cd tests && perl runtests.pl 1 to 100          # run tests 1 to 100
```

curl also has a ready-made `--enable-code-coverage` flag (`m4/curl-functions.m4`), and its
test documentation explains how to measure coverage with gcov. So D6 can start without
building our own coverage tooling.

### 5. It is a real, widely used program

curl is mature, actively maintained and one of the most widely used pieces of software in
the world. Results on curl mean something beyond a toy example. Its configuration also
matters for security: turning off unused protocols is a common way to make software
safer, so knowing what each combination really contains is useful in practice.

## Why not the others

| System | Main reason |
|---|---|
| SQLite | Closest runner-up. Its tests check for features inside Tcl code (`ifcapable` blocks) instead of in separate metadata, which is harder to extract reliably. It also has fewer run-time options, and we had already started analysing curl's source |
| Apache ZooKeeper | Only run-time options, no build-time options. Its JUnit tests take long |
| ESLint | Only run-time, schema-based options. No build-time options |
| BusyBox | Large configuration space, but builds reliably only on Linux, and its test suite is small |
| ripgrep | Very few build-time options (Cargo features) |
| Apache httpd | Harder to build (needs APR and PCRE), and its tests live in a separate Perl framework |

## What we model first

curl has about 115 build-time flags. We did not try to model all of them at once. The
first model ([models/curl.yaml](../models/curl.yaml)) covers 22 of them:

- 11 protocols, such as `ftp`, `smtp`, `imap`, `ldap` and `ldaps`,
- 9 features, such as `cookies`, `ipv6`, `proxy` and `verbose`,
- 2 libraries: the TLS (encryption) library and zlib (compression).

It also contains the rules between them. Run-time options will be added once the D5
build-and-test script works.
