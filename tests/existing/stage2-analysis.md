# Existing test suite vs. our 6 constraints (Stage 2)

Main question for this stage: *do any of curl's own ~1,890 tests already check the
6 constraints (C1-C6) in [models/curl.yaml](../../models/curl.yaml)?*

Short answer: **no.** curl's own tests check whether a *feature is present*, and skip
themselves automatically if it is not. None of them check that a constraint-violating
*combination* produces the documented result, because a single run of the test suite
only ever exercises one build.

## Why this is structurally impossible for the existing suite

Every curl test (`tests/data/testNNNN`) runs against one already-compiled `curl`
binary. It can only ask "is feature X present in *this* binary?" through the
`<features>` tag (`docs/tests/FILEFORMAT.md`, "`<features>`" section): if a listed
feature is missing, the test is skipped; nothing in the format lets one test build
curl twice with different flags and compare the two. Our constraints are exactly
about what happens *across two different builds* (for example: build A asks for
`ldaps` with `ldap` off; does the resulting binary silently drop `ldaps`, same as
build B which asks for neither?). That question cannot be asked from inside a single
test run.

## What we checked, constraint by constraint

We searched `tests/data/*` for every test connected to each constraint's options,
using curl `curl-8_17_0`.

| Constraint | Options involved | Existing tests found | What they actually check |
|---|---|---|---|
| C1 | `ldaps` requires `ldap` | 2 (`test445`, `test1560`) | Each needs `ldap`/`ldaps` in `<features>`. They test that LDAP(S) *works* when built in. Neither runs when `ldap` is missing, and neither checks *why* it is missing or what happens when only `ldaps` was requested |
| C2 | a TLS backend is required | 0 | No test exercises "no TLS backend chosen"; this is a `configure`-time error, before any binary exists to test |
| C3 | `hsts` requires `tls` | 11 (e.g. `test440`, `test1900`) | All require `HSTS` (and most also `https`/`proxy`) in `<features>`. None run on a build where `tls=none`, so none observe the silent fallback |
| C4 | `hsts` requires `http` | same 11 as C3 | Same as above: they require `HSTS`, not specifically "HSTS requested but HTTP off" |
| C5 | `alt-svc` requires `http` | 12 (e.g. `test355`, `test1908`) | All require `alt-svc` in `<features>`. None test an HTTP-disabled build |
| C6 | `form-api` requires `mime` | 0 found tagged `form-api`/`Mime` for this combination | No test isolates "form-api requested, mime off" |

Counted with:

```sh
grep -lE "^ldap$|^ldaps$" tests/data/test[0-9]*          # C1
grep -li "hsts" tests/data/test[0-9]*                     # C3, C4
grep -li "alt-svc" tests/data/test[0-9]*                  # C5
```

Also confirmed from real build data our teammate Rana already collected
(`results/*/summary.json`, before we added any new test):

| Config | What it violates | `built.protocols` / `built.features` confirms |
|---|---|---|
| `ldaps-no-ldap` | C1 | Neither `ldap` nor `ldaps` appear — LDAPS was silently dropped |
| `no-http` | C4, C5 | `HSTS` and `alt-svc` are both absent from `built.features` |
| `no-tls` | C3 | `HSTS` is absent from `built.features` (while `alt-svc` is still present, since C5 only needs `http`, not `tls` — a useful cross-check that the two constraints are independent) |

skip_reasons in those same summaries show the 2 LDAP tests being skipped
("curl lacks ldap support") instead of being *used* to check the constraint.

## What this means for D7

Four of the six constraints (C1, C3, C4, C5) are **silent**: the build succeeds and
looks fine, but a requested feature is quietly missing. These are also the four with
zero interaction-level coverage in the existing suite. They are the priority for
Stage 3/D7: write new, curl-native tests that specifically assert the *consequence*
of each silent constraint on a real binary, something curl's own suite currently
never does.
