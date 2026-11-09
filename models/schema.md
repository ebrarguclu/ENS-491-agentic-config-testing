# Model Format (D4)

This page explains how we write down a program's configuration space in a file. We call
such a file a **model**. Our curl model is [curl.yaml](curl.yaml).

A model answers four simple questions:

1. Which options does the program have?
2. Which values can each option take, and which value is used if you do not choose one?
3. How do you actually set each value (for example, which `configure` flag)?
4. Which combinations are not allowed, and what happens if you try them anyway?

The same file is also read by our scripts (D5). A **configuration** is one choice of
values, and the script turns it into a real command.

If a term is unfamiliar, see [Key terms](../README.md#key-terms) in the main README.

## The file at a glance

A model is a YAML file with three lists:

```yaml
system: curl                 # which program
version: curl-8_17_0         # exact version (git tag) the model describes
sources: [configure.ac]      # files we read to build the model

options:      [ ... ]        # the settings you can choose
constraints:  [ ... ]        # rules about which combinations are allowed
effects:      [ ... ]        # side effects on parts of the program outside the model
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
the same options.

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

## Our evidence rule

Every option, rule and effect must point to a place in the source code, and every rule
and effect must be confirmed by actually running the build system. This is our project's
main rule in practice: an AI may suggest an entry, but the entry only goes into the model
after it has been checked against the source and confirmed with a tool.

All rules in the curl model can be re-checked with one command:
`bash scripts/verify_curl_constraints.sh`. See [curl_verification.md](curl_verification.md)
for the results.

## Configuration files

A configuration file picks values for some options. Every option you do not mention
keeps its default.

```yaml
name: no-ftp-no-cookies
system: curl
values:
  tls: openssl
  ftp: disabled
  cookies: disabled
```

The D5 script looks up the `flags` of each chosen value in the model and builds the
command:

```sh
./configure --with-openssl --disable-ftp --disable-cookies
```
