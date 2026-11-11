# D8: Live demonstration

A runnable, step-by-step walkthrough of the full pipeline: model → build → silent
behavior → missing test coverage → our new test catching it → coverage before/after.
Every command below has actually been run; the outputs shown are what was
produced, not what is expected.

## 0. Setup

```sh
cd systems/curl
git log -1 --oneline        # confirm we're on curl-8_17_0
```

The `ldaps-no-ldap` configuration can be pre-built in advance so step 2 does not
need to wait on a build during the meeting:

```sh
./configure --without-libpsl --with-openssl --disable-ldap --enable-ldaps
make -j2 && make -C tests
```

## 1. The model

`models/curl.yaml` defines the `ldaps` option and constraint `C1`:

```yaml
- id: C1
  kind: requires
  if: {ldaps: enabled}
  then: {ldap: enabled}
  on_violation: silent
  message: "LDAP needs to be enabled to support LDAPS"
  evidence: configure.ac:788-817
```

curl's own `configure` script allows requesting LDAPS without LDAP. It does not
error — it silently builds a curl without LDAPS support, and the only trace of
this is a line in the configure output that is easy to miss.

## 2. The silent behavior, demonstrated live

```sh
./configure --without-libpsl --with-openssl --disable-ldap --enable-ldaps 2>&1 | grep -i ldap
```

Observed output:

```
configure: WARNING: Cannot find libraries for LDAP support: LDAP disabled
  LDAP:             no      (--enable-ldap / --with-ldap-lib / --with-lber-lib)
  LDAPS:            no      (--enable-ldaps)
```

Exit code is 0 — the build succeeds. The built binary:

```sh
./src/curl ldaps://example.com/; echo "exit=$?"
```

Observed output:

```
curl: (1) Protocol "ldaps" not supported
exit=1
```

LDAPS was explicitly requested; `configure` reported no problem and the build
succeeded, yet the resulting binary cannot use LDAPS at all. Nothing in the normal
build output surfaces this unless it is specifically searched for.

## 3. The gap in curl's own test suite

```sh
grep -lE "^ldap$|^ldaps$" tests/data/test[0-9]* 2>/dev/null
```

Only 2 of curl's ~1,890 tests touch LDAP at all (`test445`, `test1560`), and each
requires `<features>ldap</features>` — they run only when LDAP *is* present, so
neither can observe the silent-drop case demonstrated above. None of curl's own
tests check this: they confirm LDAP works when present, never what happens to
LDAPS specifically when LDAP is absent.

## 4. The generated test catching it

`tests/generated/test9001` mirrors the manual steps above:
`<features>!ldap</features>`, command `ldaps://...`, expecting errorcode 1 and the
exact message observed.

```sh
cp ../../tests/generated/test9001 tests/data/test9001
cd tests && perl runtests.pl -a -n 9001
```

Observed output: `OK (1 out of 1 ...)`.

To confirm this is not a trivially-always-passing test, the same test can be run
against a build that does have LDAP (if pre-built), or the result can be cited
directly from [tests/generated/README.md](../tests/generated/README.md), which
shows the same test correctly printing `SKIPPED: curl has ldap support` on such a
build.

## 5. Coverage before vs. after

[tests/generated/before-after.md](../tests/generated/before-after.md) compares,
on the same machine and platform, the existing test suite alone ("before") against
the existing suite plus the 4 generated tests ("after"), for all three affected
configurations.

| Configuration | Passed (before → after) | Line coverage (before → after) |
|---|---|---|
| ldaps-no-ldap | 1583 → 1584 | 70.0% (33,322 → 33,326 lines) |
| no-tls | 1444 → 1446 | 71.5% → 71.6% (30,409 → 30,430 lines) |
| no-http | 630 → 633 | 58.7% → 58.8% (22,588 → 22,598 lines) |

The percentage barely moves, since these are 4 narrow, targeted tests rather than
a general coverage push, but line coverage increases in every configuration (+4,
+21, +10 lines) from error-handling code that curl's own suite reaches only
partially, never through this exact silent-constraint path. The result that
matters is not the percentage: the number of modeled constraints with at least one
test that actually asserts the documented silent behavior goes from **0 out of 6**
to **4 out of 6** (C1, C3, C4, C5).

A related finding: test9001 (C1, the LDAPS test) runs and passes on all three
configurations here, not only `ldaps-no-ldap`, because this particular machine has
no LDAP libraries installed at all, so curl silently drops LDAP(S) regardless of
which of the three configurations is built. This illustrates that a silent
constraint's effect can depend on the build machine, not only on the requested
configuration.

## 6. Summary and open questions

Four constraints have confirmed, always-silent behavior (C1, C3, C4, C5); two are
configure-time errors (C2, C6). The four silent ones are where generated tests add
the most value, since errors are already hard to miss. Possible next steps include
generated tests for option combinations not yet modeled, and comparing how a
different AI tool's generated tests would differ from these.

Questions for the advisor:
- Is targeting the 4 silent constraints the right scope for D7, or should error
  constraints (C2, C6) also get generated tests, even though those are already
  easy to notice without one?
- For "before/after coverage," is a line/function coverage delta the right metric,
  or should the report also state "number of modeled constraints with at least one
  asserting test" (0/6 → 4/6)?
