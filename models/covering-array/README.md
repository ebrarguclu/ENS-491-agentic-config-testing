# 2-way covering array for curl (D9/D11)

10 full configurations ([models/configs/covering-array/](../configs/covering-array/))
generated so that every pair of option values in [models/curl.yaml](../curl.yaml)
appears together in at least one of them, instead of the 8 hand-picked
configurations used up to D7/D8.

## Tool choice: PICT, not ACTS

[docs/plan-d9-d13.md](../../docs/plan-d9-d13.md) left "which CIT tool" open: NIST
ACTS or Microsoft PICT. The constraint-aware version of ACTS has to be requested
from NIST by email and waited for; PICT is open source, builds from source in
under a minute, and already supports the `IF ... THEN ...` constraints we need.
We used PICT and did not wait on an ACTS request. (If ACTS is still wanted later
for comparison, the request to NIST is a separate, manual step — nothing here
depends on it.)

PICT (v3.7.4) was built from [microsoft/pict](https://github.com/microsoft/pict)
with `cmake -B build -DCMAKE_BUILD_TYPE=Release . && cmake --build build`. It is a
build tool here, like `lcov`, not part of curl or of this repository.

## `ldap` on Linux: installed the library, did not forbid the value

The other open decision was what to do about `ldap: enabled` on a Linux machine
with no LDAP development libraries (environment requirement R1). We installed
`libldap-dev` (`apt-get install libldap-dev`) instead of forbidding the value.
Confirmed on this machine:

```sh
./configure --without-libpsl --with-openssl --enable-ldap ...
# checking whether to support ldap... yes
# LDAP: enabled (OpenLDAP)
```

This means `ldap` could be treated as a free parameter in the covering array,
the same as any other option, and both of its values are now actually buildable
here — which matters, because forbidding `ldap: enabled` would have also made it
impossible to generate rows that combine `ldap: enabled` with other options.

## Silent constraints were not excluded

The covering array must not avoid the four silent constraints (C1, C3, C4, C5):
they are what this project studies, so a covering array that steers around them
would hide exactly the interactions we want in the test set. Only the two
**error**-type rules were turned into PICT exclusion constraints, because a
combination that violates one of them does not build at all and only wastes a
run:

- **C6** (`form-api` requires `mime`, error when `form-api` is requested
  explicitly): `IF [form-api] = "enabled" THEN [mime] = "enabled";`
- **C2** (a TLS backend is mandatory) needed no PICT constraint: `tls` has only
  its two real values (`openssl`, `none`) as a PICT parameter, so PICT always
  assigns one; there is no "unset" value to exclude.

C1, C3, C4 and C5 were left completely unconstrained in the PICT model. The
result: 6 of the 10 generated rows hit one of them --

| Row | Silent constraint hit | Why |
|---|---|---|
| ca-01 | C1 | `ldaps: enabled`, `ldap: disabled` |
| ca-02 | C4 | `hsts: enabled`, `http: disabled` |
| ca-05 | C4 | `hsts: enabled`, `http: disabled` |
| ca-06 | C3 | `hsts: enabled`, `tls: none` |
| ca-08 | C5 | `alt-svc: enabled`, `http: disabled` |
| ca-10 | C4 | `hsts: enabled`, `http: disabled` |

ca-02's configure output was checked by hand to confirm this is real, not just a
property of the YAML: `checking whether to support HSTS... yes`, yet the final
summary says `HSTS: no` -- the same misleading-message pattern already recorded
for C4 in [models/curl.yaml](../curl.yaml), now reproduced in a covering-array row
rather than a hand-picked one.

## How the 10 rows were produced

```sh
# model -> PICT input (22 parameters, 1 constraint from the 2 error-type rules)
python3 scripts/covering_array.py model-to-pict models/curl.yaml models/covering-array/curl.pict.txt

# PICT -> one row per test case (tab-separated)
pict models/covering-array/curl.pict.txt > models/covering-array/pict-output.tsv

# each row -> a full configuration YAML, same format as models/configs/*.yaml
python3 scripts/covering_array.py rows-to-configs models/curl.yaml \
  models/covering-array/pict-output.tsv models/configs/covering-array --prefix ca
```

[scripts/covering_array.py](../../scripts/covering_array.py) has the full
reasoning in its module docstring.

## Verification

Per the project's rule (nothing is accepted before it is checked with a tool),
the array was not just trusted to be correct because PICT produced it:
`python3 scripts/covering_array.py verify models/curl.yaml models/configs/covering-array`
independently re-derives, from the model alone, every pair of option values that
is allowed to appear together, and checks each one is present in at least one of
the 10 configurations -- without relying on PICT's own accounting.

```
10 of 10 configuration(s) are full and respect every error-type constraint.
All 923 required option-value pairs are covered by at least one configuration.
```

923 matches by hand: 22 options give C(22,2) = 231 pairs of options; almost all
pairs have 2 values each, so 2x2 = 4 value-combinations per pair, 231 x 4 = 924,
minus the 1 combination C6 forbids (`form-api: enabled` with `mime: disabled`) =
923.

## What this hands to D10

[models/configs/covering-array/ca-01.yaml](covering-array/ca-01.yaml) through
`ca-10.yaml` are ordinary full configurations in the same format
`scripts/run_config.sh` already reads (see "Full configurations" in
[models/schema.md](../schema.md)) -- nothing about the run script needs to change
to build and test them. Building and measuring branch coverage for all 10,
and combining the coverage of all runs into one number, is D10 (Rana Keleş).
