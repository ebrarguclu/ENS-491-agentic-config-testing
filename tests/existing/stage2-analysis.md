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
| C1 | `ldaps` requires `ldap` | 2 (`test445`, `test1560`) | Neither is an LDAP test as such: `test445` checks that tunneling protocols are refused through an HTTP proxy, and `test1560` tests the URL API. Both simply list `ldap` among many protocols in `<features>`, so neither runs when `ldap` is missing, and neither checks *why* it is missing or what happens when only `ldaps` was requested |
| C2 | a TLS backend is required | 0 | No test exercises "no TLS backend chosen"; this is a `configure`-time error, before any binary exists to test |
| C3 | `hsts` requires `tls` | 11 (e.g. `test440`, `test1900`) | All require `HSTS` (and most also `https`/`proxy`) in `<features>`. None run on a build where `tls=none`, so none observe the silent fallback |
| C4 | `hsts` requires `http` | same 11 as C3 | Same as above: they require `HSTS`, not specifically "HSTS requested but HTTP off" |
| C5 | `alt-svc` requires `http` | 12 (e.g. `test355`, `test1908`) | 10 of them require `alt-svc` in `<features>`; the other 2 (`test1913`, `test1914`) only mention alt-svc elsewhere in the file. None test an HTTP-disabled build |
| C6 | `form-api` requires `mime` | 9 require `form-api` (e.g. `test516`, `test554`) | All 9 need the form API to be present and are skipped without it. No test isolates "form-api requested, mime off" or checks that `--disable-mime` silently removes the form API |

Counted with:

```sh
grep -lE "^ldap$|^ldaps$" tests/data/test[0-9]*          # C1
grep -li "hsts" tests/data/test[0-9]*                     # C3, C4
grep -li "alt-svc" tests/data/test[0-9]*                  # C5
# C6: tests whose <features> block lists form-api
for f in tests/data/test[0-9]*; do
  awk '/<features>/{f=1;next}/<\/features>/{f=0}f' "$f" | grep -qx form-api && echo "$f"
done
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

Four of the six constraints (C1, C3, C4, C5) are **always silent**: the build succeeds
and looks fine, but a requested feature is quietly missing. C6 is silent only when
`form-api` is left at its default (requesting it explicitly is an error), and C2 is
always an error. The four always-silent constraints have zero interaction-level
coverage in the existing suite. They are the priority for
Stage 3/D7: write new, curl-native tests that specifically assert the *consequence*
of each silent constraint on a real binary, something curl's own suite currently
never does.
