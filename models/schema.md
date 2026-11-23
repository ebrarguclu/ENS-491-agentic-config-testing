# Model Format (D4)

This page explains how we write down a program's configuration space in a file. We call
such a file a **model**. Our curl model is [curl.yaml](curl.yaml).

A model answers five simple questions:

1. Which options does the program have?
2. Which values can each option take, and which value is used if you do not choose one?
3. How do you actually set each value (for example, which `configure` flag)?
4. Which combinations are not allowed, and what happens if you try them anyway?
5. Which values only work if the build machine has something installed?

The same file is also read by our scripts (D5). A **configuration** is one choice of
values, and the script turns it into a real command.

If a term is unfamiliar, see [Key terms](../README.md#key-terms) in the main README.

## The file at a glance

A model is a YAML file with four lists:

```yaml
system: curl                 # which program
version: curl-8_17_0         # exact version (git tag) the model describes
sources: [configure.ac]      # files we read to build the model

options:      [ ... ]        # the settings you can choose
constraints:  [ ... ]        # rules about which combinations are allowed
effects:      [ ... ]        # side effects on parts of the program outside the model
environment:  [ ... ]        # values that need something installed on the build machine
```

## Options

Here is one real option from our curl model:

```yaml
- id: ldap
  kind: compile-time
  category: protocol
  description: LDAP support.
  values: [enabled, disabled]
  default: auto
  auto_rule: Enabled if LDAP libraries are found on the machine, otherwise disabled.
  flags: {enabled: --enable-ldap, disabled: --disable-ldap}
  evidence: configure.ac:768-787, 2521-2547
```

Each field means:

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | A short, unique name, used in configuration files (here `ldap`) |
| `kind` | yes | `compile-time` (chosen when building) or `runtime` (chosen when running) |
| `category` | yes | A group to keep the file readable: `protocol`, `feature` or `library` |
| `description` | yes | One sentence about what the option does |
| `values` | yes | The values you can choose |
| `default` | yes | What happens if you do not choose (see the next table) |
| `flags` | yes | For each value, the exact command-line flag that selects it |
| `evidence` | yes | The file and line numbers where the option is defined in the source code |
| `notes` | no | Anything a tester should know, for example a misleading message |

The `default` field can take three forms:

| `default` | Meaning | Example |
|---|---|---|
| A value, like `enabled` | This value is always used if you do not choose | `ftp` is enabled unless you say otherwise |
| `auto` | The build system decides by looking at the machine. The rule is written in `auto_rule` | `ldap` is on only if the LDAP libraries are installed |
| `null` with `required: true` | There is no default. If you do not choose, the build stops | `tls`, the encryption library |

`auto` is important because the same command can build a different program on a
different machine. Our macOS build had LDAP, our Linux build did not, even though we used
the same options. This is why `auto` may appear in the model, but never in a
configuration file (see [Full configurations](#full-configurations) below).

## Constraints

A constraint is a rule that says some combinations are not allowed. Here is one from our
curl model:

```yaml
- id: C1
  kind: requires
  if: {ldaps: enabled}
  then: {ldap: enabled}
  on_violation: silent
  result: ldaps is turned off; configure continues.
  message: "LDAP needs to be enabled to support LDAPS"
  evidence: configure.ac:799-802, 810-813
  verified: >
    macOS: ./configure ... --disable-ldap --enable-ldaps
    -> exit 0, message printed, summary "LDAPS: no".
```

In words: *"If you turn LDAPS on, LDAP must be on as well. If it is not, the build does
not stop. It quietly turns LDAPS off."*

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `C1`, `C2` and so on |
| `kind` | yes | `requires` (if A, then also B), `excludes` (A and B never together) or `required` (this option must be chosen) |
| `if` | for `requires` and `excludes` | The situation the rule is about |
| `then` | for `requires` | What must also be true |
| `on_violation` | yes | What the build system does when the rule is broken: `error` (the build stops) or `silent` (the build continues and quietly changes something) |
| `result` | for `silent` | What actually happens instead |
| `message` | no | The exact text the build system prints, if any |
| `evidence` | yes | The file and line numbers where the rule is implemented |
| `verified` | yes | The command we ran to test the rule, and what we saw |

### Why we record "error" or "silent"

An `error` rule is easy to notice, because the build stops and tells you. A `silent` rule
is much more dangerous. The build succeeds, so everything looks fine, but the program is
not built the way you asked. A test that depends on the missing feature may then be
skipped, or even pass for the wrong reason. That is why silent rules are the most
interesting ones for our project.

## Effects

Some consequences of an option are not rules between two of our options. They concern
parts of the program we do not model. We list these separately as **effects**. For
example: if you build curl without TLS, then `https`, `ftps` and the other secure
protocols are not built.

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `E1`, `E2` and so on |
| `when` | yes | The option value that causes the effect |
| `result` | yes | What changes |
| `evidence` | yes | The file and line numbers in the source code |
| `verified` | yes | The command we ran, and what we saw |

## Environment requirements

Some option values only work if the build machine has a certain library installed. For
example, `ldap: enabled` needs the LDAP libraries. This is not a rule between two of our
options, so it is not a constraint. It is a rule between one option and the machine. The
same configuration can be fine on a Mac (which has the LDAP libraries) and break on our
Linux machine (which does not).

Here is one from our curl model:

```yaml
- id: R1
  if: {ldap: enabled}
  needs: LDAP libraries (for example OpenLDAP's libldap and liblber) on the build machine.
  on_violation: error
  message: "couldn't detect the LDAP libraries"
  evidence: configure.ac:779, 2521-2524, 2539-2542
  verified: >
    Linux (no LDAP libraries): ./configure --without-libpsl --with-openssl --enable-ldap
    -> exit 1 with this message.
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `R1`, `R2` and so on |
| `if` | yes | The option value that needs something from the machine |
| `needs` | yes | What must be installed |
| `on_violation` | yes | `error` or `silent`, exactly as for constraints |
| `result` | for `silent` | What actually happens instead |
| `message` | no | The exact text the build system prints, if any |
| `evidence` | yes | The file and line numbers in the source code |
| `verified` | yes | The command we ran, on which machine, and what we saw |
| `notes` | no | Anything a tester should know |

Environment requirements matter most when we generate many configurations at once
(for example with a covering array in D9). Before generating, we check which
requirements the build machine meets. A value whose requirement is not met cannot be
used on that machine. We either treat it as forbidden there, like a constraint, or
install what is missing. A silent requirement, like R2 for zlib, is the tricky one: the
build succeeds without what was asked for, so the only way to notice is to compare the
configuration with what was really built.

## Our evidence rule

Every option, rule and effect must point to a place in the source code, and every rule
and effect must be confirmed by actually running the build system. This is our project's
main rule in practice: an AI may suggest an entry, but the entry only goes into the model
after it has been checked against the source and confirmed with a tool.

All constraints, effects and the R1 requirement in the curl model can be re-checked with
one command:
`bash scripts/verify_curl_constraints.sh`. See [curl_verification.md](curl_verification.md)
for the results.

## Configuration files

A configuration file picks a value for options in the model. The script from D5 looks
up the `flags` of each chosen value and builds the `configure` command. There are two
kinds of configuration files.

### Partial configurations (D5 to D7)

The configurations in [configs/](configs/) that we used up to D7 only name the options
they change. Every option they do not mention keeps its default:

```yaml
name: no-ftp
system: curl
values:
  tls: openssl
  ftp: disabled
```

This is short and was enough to compare a few hand-picked builds. But it has a problem:
options left at `auto` are decided by the machine. The same file built curl *with* LDAP
on macOS and *without* LDAP on Linux, so the two runs did not test the same program. We
keep these files as they are, because the results in `results/` were produced with them.
What each of those builds really contained is recorded under `built` in its
`summary.json`.

### Full configurations

From D9 on, every new configuration file must be **full**:

- It gives a value for **every** option in the model. For curl that means all 22.
- Every value is a real value from the option's `values` list. `auto` is not allowed.
  For curl this matters for `ldap`, `ipv6` and `zlib`, the three options whose default is
  `auto`.

A full configuration fixes the program that should be built, whatever machine builds it.
This is also what a covering array needs, because each row of a covering array gives a
value to every option. Here is a full configuration for curl:

```yaml
name: full-default-linux
system: curl
values:
  # protocols (11)
  http: enabled
  ftp: enabled
  smtp: enabled
  imap: enabled
  pop3: enabled
  telnet: enabled
  tftp: enabled
  dict: enabled
  mqtt: enabled
  ldap: disabled       # was auto. Our Linux machine has no LDAP libraries (R1)
  ldaps: disabled      # with ldap off, ldaps would be dropped anyway (C1)
  # features (9)
  proxy: enabled
  cookies: enabled
  http-auth: enabled
  mime: enabled
  form-api: enabled
  alt-svc: enabled
  hsts: enabled
  ipv6: enabled        # was auto
  verbose: enabled
  # libraries (2)
  tls: openssl
  zlib: enabled        # was auto. Silently dropped if zlib is missing (R2)
```

It describes the same curl that a default build on our Linux machine produces, but now
the file says so itself, instead of leaving it to the machine. We checked this on the
Linux machine: `configure` with the flags below finishes with exit 0, and its summary
lists exactly the same protocols and features as a default build. The script turns it
into:

```sh
./configure --enable-http --enable-ftp --enable-smtp --enable-imap --enable-pop3 \
  --enable-telnet --enable-tftp --enable-dict --enable-mqtt --disable-ldap \
  --disable-ldaps --enable-proxy --enable-cookies --enable-http-auth --enable-mime \
  --enable-form-api --enable-alt-svc --enable-hsts --enable-ipv6 --enable-verbose \
  --with-openssl --with-zlib
```

A full configuration says what we *asked for*. The silent constraints (C1, C3, C4, C5)
and silent requirements (R2) can still change what is really built. So after every
build, compare the configuration with `built` in `summary.json`. C6 behaves differently
here: a full configuration always names `form-api` explicitly, so `form-api: enabled`
with `mime: disabled` always stops `configure` with an error.
