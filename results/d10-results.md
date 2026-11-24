# D10 results: running the covering array

What we ran, what the combined coverage is, how much the numbers move between two
identical runs, and which tests failed. Per-run numbers are in
[coverage_table.md](coverage_table.md).

## What was run

- Machine: macOS, Apple Silicon (`Darwin arm64`), lcov 2.6. curl `curl-8_17_0`.
- All runs used the full test suite and measured line, function and branch coverage.
- The 10 configurations of the covering array (`models/configs/covering-array/ca-01.yaml`
  to `ca-10.yaml`), on 24-25 November 2026.
- The 8 hand-picked configurations of D6 again, because branch coverage can only be
  measured during the run. Their earlier numbers are in the history of
  `results/<name>/summary.json`.
- `ca-03` a second time, as `ca-03-repeat`, to see how much identical runs differ.

Every configuration was built. For each run, `summary.json` lists both the flags we asked
for (`configure_flags`) and what was really built (`built`).

## Combined coverage

`scripts/config_tools.py merge` combines several runs: a line or branch counts as covered
if any run covered it.

| Set of configurations | Runs | Lines covered | Line coverage | Function coverage | Branch coverage |
|---|---|---|---|---|---|
| Default only | 1 | 37,186 / 55,069 | 67.5% | 80.9% | 46.5% |
| Hand-picked (D6) | 8 | 37,500 / 55,469 | 67.6% | 81.0% | 48.0% |
| Covering array | 10 | 36,441 / 55,980 | 65.1% | 79.0% | 46.7% |
| All of the above together | 18 | 37,741 | | | |

The covering array covers **fewer** lines in total than the default configuration alone.
Each hand-picked configuration is the default with one option changed, so it runs almost
all tests. In a covering-array row about half of the options are off, and every option
that is off also skips the tests that need it. A 2-way covering array guarantees that
every pair of option values is built at least once; it does not try to maximise code
coverage.

The covering array still reaches code the default never runs:

| | Lines | Branches |
|---|---|---|
| Covered by the covering array, not by the default | 550 | 1,894 |
| Covered by the default, not by the covering array | 1,295 | 996 |

Most of the 550 lines are in `lib/md5.c` (150) and `lib/curl_sha512_256.c` (87). These
look like curl's own hash code, which is probably only used when curl is built without
OpenSSL; we have not checked this in the source yet.

**Branch numbers across different builds are approximate.** lcov numbers the branches of
a line by how the compiler built it, so the same `if` can get different numbers in two
builds. 1,570 of the 1,894 extra branches above are in `lib/setopt.c`, which has many
`#ifdef` blocks, so many of them may be renumbered branches rather than new ones. Line
numbers do not have this problem, so compare lines across builds.

## Run-to-run difference

`ca-03` was run twice with nothing changed. Both runs passed, failed and skipped exactly
the same tests.

| | First run | Second run | Difference |
|---|---|---|---|
| Lines covered | 27,492 | 27,490 | 2 |
| Branches covered | 13,067 | 13,063 | 4 |

Looked at line by line, 10 lines and 12 branches changed state between the two runs,
mostly in `lib/url.c`, `lib/cf-socket.c` and `lib/multi.c` (connection handling). A gain
in D12 should be larger than this before we call it real. This is a single repeat of a
single configuration, so it is a first estimate, not a bound.

## What was asked for and what was built

The covering array does not avoid our silent constraints, and six rows hit one. The real
builds show exactly the effect the model predicts:

| Row | Asked for | Not built | Constraint |
|---|---|---|---|
| ca-01 | `ldaps: enabled`, `ldap: disabled` | LDAPS | C1 |
| ca-02, ca-05, ca-10 | `hsts: enabled`, `http: disabled` | HSTS | C4 |
| ca-06 | `hsts: enabled`, `tls: none` | HSTS | C3 |
| ca-08 | `alt-svc: enabled`, `http: disabled` | alt-svc | C5 |

In the other four rows, the protocols and features we checked match what was asked for.

## Failed tests

**HTTP on, HTTP authentication off.** Three rows have both `http: enabled` and
`http-auth: disabled`: ca-01 (78 failed tests), ca-03 (97) and ca-06 (37). Most of the
failed tests send a user name and password: the names of 63 of the 78, 86 of the 97 and
29 of the 37 mention authentication, a user, a password or `.netrc`. We have not checked
the remaining ones one by one. In tests 2, 3, 16, 63, 80 and 82 to 85 (ca-01), curl did not send
the expected `Authorization` or `Proxy-Authorization` header. Their `<features>` do not
ask for HTTP authentication, so they run and fail instead of being skipped. The rows with
`http-auth: disabled` but `http: disabled` (ca-05, ca-10) have no failures, because the
HTTP tests are skipped there anyway. This is an interaction between two options that none
of the 8 hand-picked configurations could show, since none of them turns `http-auth` off.

**Other failures:**

- Tests 20 and 507 expect a connection to a host name that does not exist to fail. On the
  network used for these runs, such names resolve to the router (`192.168.1.1`), so the
  connection works and the tests fail. They failed in every run with HTTP on, including
  `default`, and passed in D6 on another network.
- Test 1510 failed in ca-03 (both runs), ca-07 and ca-09, and nowhere else. We have not
  looked into why, so it may or may not depend on the configuration.

## Limits

- Mac only. The same configurations on Linux would give different numbers.
- One repeat of one configuration for the run-to-run difference.
- The network problem above lowers coverage a little in every run with HTTP on, for
  example `default` covers 37,186 lines now and covered 37,199 in D6.
