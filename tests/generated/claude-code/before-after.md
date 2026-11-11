# Before / after coverage (D7)

This compares, for each affected configuration, the existing test suite alone
("before") against the existing suite plus our 4 generated tests
([test9001](test9001)-[test9004](test9004)) ("after").

## Why these numbers were collected on Linux, not reused from `results/coverage_table.md`

Rana's D6 numbers in [results/coverage_table.md](../../../results/coverage_table.md)
were collected on Darwin arm64. We already found (while writing
[tests/existing/stage2-analysis.md](../../existing/stage2-analysis.md)) that the same
configuration gets noticeably different pass/skip counts on Linux vs. macOS — mostly
because some auxiliary test servers (stunnel, scp, SMB, IPv6 variants) are set up
differently on each machine, which has nothing to do with our generated tests. Mixing
platforms would make the "after minus before" delta partly a platform effect and
partly a generated-tests effect, with no way to tell them apart.

So for this comparison, both "before" and "after" were built and run **on this same
Linux machine**, back to back, with nothing else changed:

- "before": `models/configs/<name>-linux-before.yaml` — same `values:` as the team's
  original config, generated tests absent from `systems/curl/tests/data/`
- "after": `models/configs/<name>-plus-generated.yaml` — same `values:`, with
  `test9001`-`test9004` copied into `systems/curl/tests/data/` first

Both used `scripts/run_config.sh` unchanged, so the only real difference between a
"before" and its matching "after" run is the presence of our 4 new test files.

## Results

| Configuration | | Tests run | Passed | Skipped | Line coverage | Lines covered / total | Function coverage |
|---|---|---|---|---|---|---|---|
| ldaps-no-ldap | before | 1890 | 1583 | 307 | 70.0% | 33,322 / 47,609 | 84.4% |
| ldaps-no-ldap | after  | 1894 | 1584 | 310 | 70.0% | **33,326** / 47,609 | 84.4% |
| no-tls | before | 1890 | 1444 | 446 | 71.5% | 30,409 / 42,503 | 85.3% |
| no-tls | after  | 1894 | 1446 | 448 | **71.6%** | **30,430** / 42,503 | 85.3% |
| no-http | before | 1890 | 630 | 1,260 | 58.7% | 22,588 / 38,448 | 74.8% |
| no-http | after  | 1894 | 633 | 1,261 | **58.8%** | **22,598** / 38,448 | 74.8% |

(Raw data: `results/<name>-linux-before/summary.json` and
`results/<name>-plus-generated/summary.json`.)

## Reading this table

- **Passed +1 to +3 per config, as expected.** Each generated test only runs on the
  configuration(s) where its constraint actually applies — see the table in
  [README.md](README.md). On this machine, LDAP is unavailable by default (no
  system LDAP libraries), so test9001 (C1) happens to run and pass on *all three*
  configs, not just `ldaps-no-ldap`. That is itself a small finding: a "silent"
  constraint's effect can depend on the build *machine*, not only on the requested
  configuration — on a machine that does have LDAP installed, test9001 would
  correctly skip on `no-tls` and `no-http` instead of running.
- **Skipped count goes up too, not down.** Adding 4 tests to the suite adds up to 4
  new rows; a test that does not apply to a given config is a skip, same as any of
  curl's own feature-gated tests. This is correct behavior, not a problem.
- **Line coverage moves a little, function coverage does not.** Every config gains
  a handful of newly-covered lines (+4, +21, +10) with the same number of covered
  *functions* as before. This makes sense: the generated tests exercise an
  already-partially-covered error path (`PARAM_LIBCURL_DOESNT_SUPPORT` handling in
  `src/tool_getparam.c`, and the "protocol not supported" path for `ldaps` in the
  library's URL handling) that other tests already reach through some branches but
  not the exact branch our silent-constraint scenario takes.
- **The percentage point gain is small on purpose.** These are 4 narrow,
  specifically-targeted tests, not a general attempt to raise coverage. The
  headline result for D7 is not the percentage — it is that the number of modeled
  constraints with at least one test that actually *asserts* the documented
  behavior goes from **0 out of 6** (per `tests/existing/stage2-analysis.md`) to
  **4 out of 6** (C1, C3, C4, C5 — the two left over, C2 and C6, are
  `configure`-time errors rather than runtime behavior, see
  [README.md](README.md#not-covered-here-c2-and-c6)).

## How to reproduce

```sh
# "before" (3 runs, no generated tests present)
rm -f systems/curl/tests/data/test900{1,2,3,4}
bash scripts/run_config.sh models/configs/ldaps-no-ldap-linux-before.yaml
bash scripts/run_config.sh models/configs/no-tls-linux-before.yaml
bash scripts/run_config.sh models/configs/no-http-linux-before.yaml

# "after" (3 runs, generated tests added)
cp tests/generated/claude-code/test900{1,2,3,4} systems/curl/tests/data/
bash scripts/run_config.sh models/configs/ldaps-no-ldap-plus-generated.yaml
bash scripts/run_config.sh models/configs/no-tls-plus-generated.yaml
bash scripts/run_config.sh models/configs/no-http-plus-generated.yaml
```
