# tests/generated/

New tests written with AI assistance for option combinations that curl's own
~1,890 tests miss (deliverable D7). [tests/existing/stage2-analysis.md](../existing/stage2-analysis.md)
found that none of curl's own tests assert any of the 6 constraints modeled in
[models/curl.yaml](../../models/curl.yaml) as cross-build interactions; these 4
tests fill that gap for the 4 that are silent (C1, C3, C4, C5).

| Test | Constraint | Build it needs | What it asserts |
|---|---|---|---|
| [test9001](test9001) | C1: `ldaps` requires `ldap` | any build without LDAP (`!ldap`) | `curl ldaps://...` fails with errorcode 1 and `Protocol "ldaps" not supported`, even if `ldaps` was requested at configure time |
| [test9002](test9002) | C3: `hsts` requires `tls` | any build without a TLS backend (`!SSL`) | `curl --hsts ...` fails with errorcode 2 and "the installed libcurl version does not support this" |
| [test9003](test9003) | C4: `hsts` requires `http` | any build without HTTP (`!http`) | same as test9002, but for an HTTP-disabled build instead of a TLS-disabled one |
| [test9004](test9004) | C5: `alt-svc` requires `http` | any build without HTTP (`!http`) | `curl --alt-svc ...` fails the same way |

Each file is a normal curl test (`tests/data/testNNNN` format, see
[FILEFORMAT.md](https://github.com/curl/curl/blob/curl-8_17_0/docs/tests/FILEFORMAT.md)),
numbered 9001-9004, clear of curl's own range (currently up to `test4001`) so they
cannot collide with a future curl release. The `<features>` tag means each test
skips itself automatically on a build where it does not apply, the same mechanism
curl's own tests use, so they slot into the existing suite rather than needing
special handling.

## How the expected output was determined

Per the project rule ("nothing is accepted until it has been checked with a
tool"), every `<errorcode>` and `<stderr>` value here was copied from a real run,
not written from memory of how curl "should" behave:

```sh
# C1 - built with --enable-ldaps but LDAP itself unavailable
./configure --without-libpsl --with-openssl --enable-ldaps
make -C lib && make -C src
./src/curl ldaps://example.com/
# -> exit 1, stderr: curl: (1) Protocol "ldaps" not supported

# C3 - built with --without-ssl
./configure --without-libpsl --without-ssl
make -C lib && make -C src
./src/curl --hsts /tmp/x.txt http://example.com/
# -> exit 2, stderr:
#    curl: option --hsts: the installed libcurl version does not support this
#    curl: try 'curl --help' or 'curl --manual' for more information

# C4 / C5 - built with --disable-http
./configure --without-libpsl --with-openssl --disable-http
make -C lib && make -C src
./src/curl --hsts   /tmp/x.txt http://example.com/   # same message as C3, "--hsts"
./src/curl --alt-svc /tmp/y.txt http://example.com/  # same message, "--alt-svc"
```

The exact stderr text comes from one place in curl's own source,
`src/tool_helpers.c:52` (`"the installed libcurl version does not support this"`),
reached through `PARAM_LIBCURL_DOESNT_SUPPORT` in `src/tool_getparam.c` — this is a
generic "this build does not have the feature this flag needs" error, used for any
CLI flag whose backing feature was compiled out. It is not a message specific to
HSTS or alt-svc (we looked for one — `grep -rn "CURL_DISABLE_HSTS" src/*.c src/*.h`
finds nothing — the CLI layer does not special-case them, it just finds the feature
missing from the flags table and uses this one shared message).

## How these were run and verified

Each test was copied into `systems/curl/tests/data/` and run for real with curl's
own test runner, against a curl actually built with the matching configuration (no
result below is assumed):

```sh
cd systems/curl/tests
perl runtests.pl -a -n 9001       # against a --enable-ldaps build (LDAP still absent)   -> OK
perl runtests.pl -a -n 9002       # against a --without-ssl build                        -> OK
perl runtests.pl -a -n 9003 9004  # against a --disable-http build                       -> OK OK
```

We also checked the opposite direction, that the `<features>` tag correctly skips
each test on a build where the constraint does not apply, using the `--enable-ldaps`
build (which still has SSL, http, HSTS and alt-svc all built in):

```
test 9002 SKIPPED: curl has SSL support
test 9003 SKIPPED: curl has http support
test 9004 SKIPPED: curl has http support
test 9001 ... OK
```

This matters because a test that "passes" simply by never running (always skipped)
would be worthless; this run shows all four only run, and only assert something,
exactly when their constraint is actually in play.

`systems/curl/` itself is not tracked in this repository (see
[systems/README.md](../../systems/README.md)), so to re-run these tests: build curl
`curl-8_17_0` with one of the configurations above, copy the relevant `testNNNN`
file(s) from this folder into `systems/curl/tests/data/`, and run
`perl runtests.pl -a -n <number>` from `systems/curl/tests/`.

For the before/after coverage impact of adding these tests, see
[before-after.md](before-after.md).

## Not covered here: C2 and C6

C2 ("a TLS backend is required") and C6 ("`form-api` requires `mime`") are not in
this set. Both are `configure`-time **errors** (`configure` stops before a binary
even exists), not silent runtime behavior — there is nothing for a `curl`-level test
like these to run against. They would need a different kind of test (one that runs
`configure` itself and checks its exit code/output), which is a reasonable next step
but a different shape of test than the other four.
