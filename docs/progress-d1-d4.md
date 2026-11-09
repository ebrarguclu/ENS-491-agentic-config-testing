# Progress Report: D1 to D4

This report tells the story of the project so far, from setting up the repository to our
first model of curl's configuration. For each step it explains what we did, which commands
we ran and why. The detailed results are in the linked documents.

If a term is unfamiliar, see [Key terms](../README.md#key-terms) in the main README.

So far, D1, D2 and D3 are finished. D4 (the configuration model) is written and checked,
and is waiting for a team review. The next step is D5.

## Overview

| Step | What we did | Why | Read more |
|---|---|---|---|
| D1 | Created the shared repository and its folders | One place for everything, organised by deliverable | [Section 1](#1-setting-up-the-repository-d1) |
| D2 | Compared 7 open-source programs | To find a good program to study | [candidates.md](candidates.md) |
| D3 | Chose **curl** | Many options, useful tests, real rules between options, easy to build | [selection.md](selection.md) |
| Build | Built curl on Linux and macOS and ran its tests | Everything later depends on building curl with different options | [Section 4](#4-building-curl) |
| Experiments | Turned options off by hand and watched what changed | To see the problem with our own eyes before modelling it | [Section 5](#5-two-experiments) |
| D4 | Wrote a model of 22 curl options, 6 rules and 3 side effects | The model is the input for all later steps | [models/](../models/) |
| Checking | Confirmed every rule by running curl's build system, and turned the checks into a script | AI suggestions are only accepted after a tool confirms them | [curl_verification.md](../models/curl_verification.md) |

## 1. Setting up the repository (D1)

We created one shared GitHub repository with a folder for each part of the work:

| Folder | What goes in it | Used for |
|---|---|---|
| `docs/` | Reports, like this one | all deliverables |
| `systems/` | Instructions for downloading and building curl | D2, D3 |
| `models/` | The configuration model | D4 |
| `scripts/` | Scripts that build curl, run tests and check the model | D5, D6 |
| `tests/` | Notes on curl's tests, later the AI-written tests | D7 |
| `results/` | Outputs of our runs and coverage tables | D5 to D7 |

Every folder has a short README that says what belongs there, so everyone in the team
(and our advisor) can find things quickly.

We do **not** store curl's own source code in our repository. It is large and already
has its own repository. Instead, everyone downloads the same fixed version
(`curl-8_17_0`) into `systems/curl`, and a `.gitignore` file makes sure it is never
uploaded by accident. Using one fixed version also means our results can be repeated
later.

## 2. Comparing candidate systems (D2)

We needed one program to study. To choose it fairly, we first agreed on four questions:

1. Does it have many options?
2. Does it have tests we can run?
3. Can we build it ourselves easily?
4. Is there an official source we can use to check an AI's answers?

Then we compared seven programs: curl, SQLite, Apache httpd, BusyBox, ripgrep, Apache
ZooKeeper and ESLint. We studied curl, ZooKeeper and ESLint at source-code level and read
the documentation of the others. Comparing them was useful in itself. Each program stores
its options in a completely different way: build flags in C, a settings file in Java, a
nested object in JavaScript.

We did not build all seven programs, because the documentation was enough to rule most of
them out. We only built the one we chose (Section 4).

The full comparison is in [candidates.md](candidates.md).

## 3. Choosing curl (D3)

We chose curl for four main reasons:

- It has options at two levels: about 115 build-time flags, plus 273 command-line options
  and 291 library options at run time.
- Its tests say what they need. curl has about 1,890 tests. Each test names the server it
  needs, and 859 of them also list the features they require. This tells us which
  configuration affects which tests.
- Its build system contains real rules between options, and some of them are silent.
- It is easy to build: about 80 seconds from source code to a working program.

SQLite came second. The full reasoning is in [selection.md](selection.md).

## 4. Building curl

We built curl before writing any model, because D5 is all about building curl with
different options and running its tests. If that did not work on our machines, we wanted
to find out right away, not weeks later.

### On Linux (Ubuntu 24.04, gcc 13.3)

```sh
git clone --depth 1 --branch curl-8_17_0 https://github.com/curl/curl.git systems/curl
cd systems/curl
autoreconf -fi                                  # prepare the build files (needed for a git download)
./configure --with-openssl --without-libpsl     # choose the options
make -j2                                        # compile
make -C tests                                   # build the test tools
cd tests && perl runtests.pl 1 to 100           # run tests 1 to 100
```

The build took about 80 seconds. Of the first 100 tests, 99 ran and passed, and 1 was
skipped. The skipped test needs a debugging feature that only exists with
`--enable-curldebug`, which our build did not have. That was our first small example of a
build option deciding whether a test runs.

### On macOS (Apple Silicon)

The first attempt on macOS failed with errors like this:

```
vtls/openssl.c:408:23: error: incomplete definition of type 'ASN1_INTEGER' (aka 'struct asn1_string_st')
/opt/homebrew/Cellar/openssl@4/4.1.0/include/openssl/types.h:58:16: note: forward declaration of 'struct asn1_string_st'
```

The reason: `brew install openssl` now installs OpenSSL **version 4**. OpenSSL 4 hides
some internal details that curl 8.17.0 still uses directly, so the two do not work
together. The fix was to use OpenSSL 3 instead:

```sh
brew install openssl@3
make distclean                                                      # clean up the failed build
export PKG_CONFIG_PATH="$(brew --prefix openssl@3)/lib/pkgconfig"   # make configure find OpenSSL 3, not 4
./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl
make -j4
./src/curl --version
```

This time the build worked:

```
curl 8.17.0-DEV (aarch64-apple-darwin24.6.0) libcurl/8.17.0-DEV OpenSSL/3.5.9 zlib/1.2.12
Protocols: dict file ftp ftps gopher gophers http https imap imaps ipfs ipns ldap ldaps mqtt
           pop3 pop3s rtsp smb smbs smtp smtps telnet tftp ws wss
Features: alt-svc AsynchDNS HSTS HTTPS-proxy IPv6 Largefile libz NTLM SSL threadsafe TLS-SRP UnixSockets
```

### What building taught us

Two things came out of this step that matter for the rest of the project.

First, the version of a library can itself be a rule: curl 8.17.0 builds with OpenSSL 3
but not with OpenSSL 4.

Second, the same command builds a different curl on a different machine. Our macOS build
includes LDAP (because the LDAP libraries are installed there) but not brotli. Our Linux
build is the other way round. So some default values are not fixed, they depend on the
machine. In the model we mark these defaults as `auto`.

## 5. Two experiments

Before writing the model, we changed options by hand to see what really happens. These
are the same steps the D5 script will later do automatically.

### Experiment A: turning FTP off

We rebuilt curl without FTP and ran test 100, which is an FTP test.

```sh
./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl --disable-ftp
make -j4 && make -C tests
./src/curl --version
cd tests && perl runtests.pl 100
```

```
Protocols: dict file gopher gophers http https imap imaps ipfs ipns ldap ldaps mqtt pop3
           pop3s rtsp smb smbs smtp smtps telnet tftp ws wss
...
test 0100 SKIPPED: curl lacks ftp server support
TESTINFO: "curl lacks ftp server support" 1 time (100)
TESTFAIL: No tests were performed
```

`ftp` and `ftps` disappeared from the protocol list, and test 100 was skipped
automatically. The last line, `TESTFAIL: No tests were performed`, looks alarming but is
not a curl failure: we asked for one test, it was skipped, so nothing was left to run.

The lesson: **changing one build option changes which tests run at all.** This is the
starting point of our project, and it connects the model (D4) to the coverage
measurements (D6).

### Experiment B: a silent rule

We asked for LDAPS while turning LDAP off.

```sh
./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl --disable-ldap --enable-ldaps | grep -i ldap
```

```
checking whether to support ldap... no
checking whether to support ldaps... LDAP needs to be enabled to support LDAPS
  LDAP:             no      (--enable-ldap / --with-ldap-lib / --with-lber-lib)
  LDAPS:            no      (--enable-ldaps)
```

We clearly asked for LDAPS, but `configure` did not stop. It printed one line and quietly
built curl **without** LDAPS. Someone who assumes "the build succeeded, so I got what I
asked for" would test the wrong program. This kind of silent rule is exactly the kind of
option interaction our project is about.

## 6. Writing the configuration model (D4)

### Which options we picked

curl has about 115 build-time flags. For the first model we picked **22**:

| Group | Options |
|---|---|
| 11 protocols | `http`, `ftp`, `smtp`, `imap`, `pop3`, `telnet`, `tftp`, `dict`, `mqtt`, `ldap`, `ldaps` |
| 9 features | `proxy`, `cookies`, `http-auth`, `mime`, `form-api`, `alt-svc`, `hsts`, `ipv6`, `verbose` |
| 2 libraries | `tls` (encryption), `zlib` (compression) |

Protocols decide which parts of the test suite can run. The features were picked because
several of them depend on each other. The TLS library is required and affects many other
options. We preferred a smaller model where every entry is checked over a large model
nobody has verified. More options, and run-time options, can be added later.

### How a model file looks

The format is described in [schema.md](../models/schema.md). For each option the model
stores its possible values, its default, the `configure` flag for each value, and the
lines in `configure.ac` where it is defined. The most important design choices were:

| Choice | Why |
|---|---|
| Each value comes with its exact `configure` flag | The D5 script can turn any configuration into a `./configure` command without extra knowledge |
| A default can be a fixed value, `auto`, or "must be given" | Some defaults depend on the machine (Section 4), and TLS has no default at all |
| Every rule records whether breaking it causes an **error** or happens **silently** | Silent rules are invisible in a normal build, so they matter most for testing |
| Every entry has `evidence` (file and lines), and every rule has `verified` (command and result) | Nothing is accepted on the AI's word alone |
| Side effects are listed separately from rules | Some consequences (for example "no TLS means no `https`") involve parts of curl outside our 22 options |

A configuration is then just a small file that picks some values. The script fills in
the defaults for everything else and builds the command:

```yaml
name: no-ftp-no-cookies
values: {tls: openssl, ftp: disabled, cookies: disabled}
```

becomes

```sh
./configure --with-openssl --disable-ftp --disable-cookies
```

### How we found the options and rules

For each option we read its block in `configure.ac` (the `AC_ARG_ENABLE` or `AC_ARG_WITH`
part). From there we wrote down the flag name, what happens when the flag is not given,
and whether it depends on other options. We also noted the exact line numbers. To find
the rules, we followed internal variables such as `CURL_DISABLE_HTTP` or `SSL_ENABLED` to
the places where they switch other features off.

### How we checked them

For every rule we ran `configure` with a combination that breaks it, then looked at the
exit code (did it stop?) and the summary (what was really built?). These checks are now
one script:

```sh
bash scripts/verify_curl_constraints.sh
```

It runs 13 checks: the 6 rules, the silent version of one of them, the TLS conflict, the
3 side effects and two checks for the MQTT message. It saves the results in
`results/verification/` and resets curl to its normal setup at the end. **On Linux all 13
checks passed** ([summary](../results/verification/summary.md)). Every teammate can run
it on their own machine.

### What we found

The full table is in [curl_verification.md](../models/curl_verification.md). The main
points:

1. Silent rules are common. For 5 of the 6 rules, the build can succeed without
   containing what was asked for.
2. `configure` sometimes says the opposite of what it does. With
   `--disable-http --enable-hsts` it prints *"HSTS... yes"* and then leaves HSTS out. And
   by default it prints *"mqtt... no"*, although MQTT is built.
3. The same rule can be loud or silent. Asking for the form API without MIME stops the
   build, but leaving the form API at its default drops it quietly.
4. Defaults depend on the machine. LDAP and brotli differ between our macOS and Linux
   builds.
5. Configuration decides which tests run. Turning a protocol off skips every test that
   needs it.

Points 1 and 2 are the most important for our research question. Anyone, human or AI,
who trusts `configure`'s messages instead of checking what was actually built will end up
with a wrong picture of the configuration space.

## How we used AI

Since our project is about AI, we used an AI assistant (Claude) ourselves:

- to read `configure.ac` and suggest options and rules,
- to draft the documentation,
- to write the checking script.

We followed our own main rule: no entry was accepted just because the AI said so. Every
entry points to specific lines in curl's source code and was confirmed by running the
build system, both on a Linux machine and on a teammate's Mac. Finding 2 above shows why
this matters. Trusting a tool's messages without checking the real result would have
produced a wrong model.

## Files in the repository after D4

| File | What it contains |
|---|---|
| [README.md](../README.md) | Project overview, key terms, deliverables and owners |
| [docs/candidates.md](candidates.md) | D2: the seven candidates and the curl build check |
| [docs/selection.md](selection.md) | D3: why we chose curl |
| [docs/progress-d1-d4.md](progress-d1-d4.md) | This report |
| [systems/README.md](../systems/README.md) | How to download and build curl |
| [models/schema.md](../models/schema.md) | D4: how a model file is written |
| [models/curl.yaml](../models/curl.yaml) | D4: the curl model |
| [models/curl_verification.md](../models/curl_verification.md) | D4: how each rule was checked, and what we found |
| [scripts/verify_curl_constraints.sh](../scripts/verify_curl_constraints.sh) | Script that repeats all checks |
| [results/verification/summary.md](../results/verification/summary.md) | Latest results of the checks |

## Next steps

1. Review D4 as a team: agree on the 22 options, and let each teammate run the checking
   script on their own machine.
2. Write the D5 script, `scripts/run_config.sh`. It will take a configuration file,
   turn it into `configure` flags using `models/curl.yaml`, build curl, run the tests (or
   a chosen range) and save everything in `results/<configuration-name>/`.

Questions for our advisor:

- Is it fine to start with build-time options only and add run-time options later?
- How many configurations should we compare in D6?
