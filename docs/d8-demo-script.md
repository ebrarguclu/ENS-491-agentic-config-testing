# D8: live demo script

Purpose: a runnable, step-by-step script for showing the whole pipeline to our
advisor live — model → build → silent behavior → missing test coverage → our new
test catching it → coverage before/after. Every command below is one we have
actually run; the exact outputs shown are what we got, not what we expect.

Total time: about 10-12 minutes if run live (`./configure` + `make` takes about a
minute each time; two of the three builds can be pre-built right before the meeting
so the demo only waits once).

## 0. Setup (do this a few minutes before the meeting)

```sh
cd systems/curl
git log -1 --oneline        # confirm we're on curl-8_17_0
```

Pre-build the `ldaps-no-ldap` configuration so step 2 doesn't need to wait on a
build live:

```sh
./configure --without-libpsl --with-openssl --disable-ldap --enable-ldaps
make -j2 && make -C tests
```

## 1. The model (1 min)

Open `models/curl.yaml` and point at the `ldaps` option and constraint `C1`:

```yaml
- id: C1
  kind: requires
  if: {ldaps: enabled}
  then: {ldap: enabled}
  on_violation: silent
  message: "LDAP needs to be enabled to support LDAPS"
  evidence: configure.ac:788-817
```

Say: "curl's own `configure` lets you ask for LDAPS without LDAP. It doesn't error —
it just quietly builds a curl that doesn't have LDAPS, and only says so if you
specifically look for it."

## 2. Show the silent behavior live (2 min)

```sh
./configure --without-libpsl --with-openssl --disable-ldap --enable-ldaps 2>&1 | grep -i ldap
```

Expected (real) output:

```
configure: WARNING: Cannot find libraries for LDAP support: LDAP disabled
  LDAP:             no      (--enable-ldap / --with-ldap-lib / --with-lber-lib)
  LDAPS:            no      (--enable-ldaps)
```

Exit code is 0 — the build succeeds. Then show the built binary:

```sh
./src/curl ldaps://example.com/; echo "exit=$?"
```

Real output:

```
curl: (1) Protocol "ldaps" not supported
exit=1
```

Say: "We asked for LDAPS, configure said nothing was wrong, the build succeeded —
and the resulting curl can't do LDAPS at all. Nothing in the normal build output
told us that in a way you'd actually notice unless you grepped for it."

## 3. The gap in curl's own test suite (2 min)

```sh
grep -lE "^ldap$|^ldaps$" tests/data/test[0-9]* 2>/dev/null
```

Only 2 of curl's ~1,890 tests touch LDAP at all (`test445`, `test1560`), and open
one of them to show it requires `<features>ldap</features>` — it only runs when
LDAP *is* present, so it can never see the silent-drop case we just demonstrated.

Say: "None of curl's own tests check this. They check that LDAP works when it's
there, never what happens to LDAPS specifically when LDAP isn't."

## 4. Our generated test catching it (2 min)

Open `tests/generated/claude-code/test9001` and show it is the mirror image of what
we just did by hand: `<features>!ldap</features>`, command `ldaps://...`, expects
errorcode 1 and the exact message above.

```sh
cp ../../tests/generated/claude-code/test9001 tests/data/test9001
cd tests && perl runtests.pl -a -n 9001
```

Real output: `OK (1 out of 1 ...)`.

To show it isn't a trivial always-pass test, also run it against a build that
*does* have LDAP (if pre-built) or point at the write-up in
`tests/generated/claude-code/README.md`, which shows the same test correctly
printing `SKIPPED: curl has ldap support` on such a build.

## 5. Coverage before vs. after (2-3 min)

Open `tests/generated/claude-code/before-after.md` (numbers filled in after the
comparison run) and walk through the table: existing-tests-only coverage for each
of the three affected configurations (`ldaps-no-ldap`, `no-tls`, `no-http`) versus
the same configuration with our 4 generated tests added.

Say what the table shows: the new tests add [N] newly-passing assertions that
specifically exercise the silent-drop behavior, and [describe coverage delta, if
any — a handful of new lines in `tool_getparam.c`/`url.c` get exercised that
weren't hit by the existing suite]. The headline point is not a big percentage
jump — these are 4 narrow, targeted tests — it's that curl's coverage number can
look identical before and after while something curl's own suite never checked is
now actually checked.

## 6. Wrap-up and open questions (1 min)

- We have 4 constraints with real, tool-verified, always-silent behavior (C1, C3,
  C4, C5) and 2 that are configure-time errors (C2, C6) — the 4 silent ones are
  where generated tests add the most value, since errors are already hard to miss.
- Next: more generated tests for the option combinations we haven't modeled yet,
  and comparing how a different AI tool's generated tests differ from ours (the
  `tests/generated/<tool>/` layout is designed for exactly that comparison).

Questions for the advisor:
- Is 4 targeted tests (one per silent constraint) the right granularity for D7, or
  should we also generate tests for non-silent (error) constraints like C2/C6, even
  though those are easy to notice without a test?
- For "before/after coverage," is a line/function coverage delta the right metric,
  or should we also report something like "number of modeled constraints with at
  least one asserting test" (which goes from 0/6 to 4/6)?
