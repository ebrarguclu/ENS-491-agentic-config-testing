# Configuration Space Model Format

This document defines the format we use to describe the configuration space of a
system (deliverable **D4**). A model is a single YAML file, for example
[`curl.yaml`](curl.yaml).

A model answers four questions:

1. **Which options exist?**
2. **Which values can each option take, and what is the default?**
3. **How is each value passed to the system?** (e.g. which `configure` flag)
4. **Which combinations of values are not allowed, and what happens if we try them anyway?**

The same file is used by the automation scripts (D5). A *configuration* is simply a
choice of one value per option, and the script turns that choice into a command line.

## File structure

```yaml
system: curl                 # name of the system
version: curl-8_17_0         # exact version (git tag) the model was built from
sources: [configure.ac]      # files the model was extracted from

options:      [ ... ]        # see "Option"
constraints:  [ ... ]        # see "Constraint"
effects:      [ ... ]        # see "Effect"
```

## Option

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Short, unique name used in configurations (e.g. `ftp`) |
| `kind` | yes | `compile-time` (decided when building) or `runtime` (decided when running) |
| `category` | yes | Grouping for readability, e.g. `protocol`, `feature`, `library` |
| `description` | yes | One sentence on what the option controls |
| `values` | yes | The allowed values, e.g. `[enabled, disabled]` |
| `default` | yes | The value used when the option is not given. See "Default values" |
| `flags` | yes | For each value, the command-line argument that selects it |
| `evidence` | yes | Where the option is defined in the source, as `file:line-line` |
| `notes` | no | Anything a tester should know, e.g. a misleading message |

### Default values

| `default` | Meaning |
|---|---|
| a value, e.g. `enabled` | Always used when the option is not given |
| `auto` | Decided by the build system based on the machine (e.g. whether a library is installed). The rule is described in `auto_rule`. |
| `null` + `required: true` | There is no default: the option must be given, otherwise the build stops |

`auto` matters because the same command can produce different builds on different
machines. For example, LDAP is enabled on a Mac where the LDAP libraries are present and
disabled on a Linux machine where they are not.

## Constraint

A constraint is a rule about which combinations of values are valid.

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `C1`, `C2`, … |
| `kind` | yes | `requires` (if A then B), `excludes` (A and B not together), `required` (option must be set) |
| `if` | for `requires` / `excludes` | The condition, as `{option: value}` |
| `then` | for `requires` | What must also hold, as `{option: value}` |
| `on_violation` | yes | What the build system does when the rule is broken: `error` (it stops) or `silent` (it continues and quietly changes a value) |
| `result` | for `silent` | What actually happens instead, e.g. "ldaps is turned off" |
| `message` | no | The exact message printed, if any |
| `evidence` | yes | Where the rule is implemented, as `file:line-line` |
| `verified` | yes | The command we ran to confirm the rule, and what we observed |

**Why `on_violation` matters.** An `error` constraint is visible: the build stops. A
`silent` constraint is invisible: the build succeeds, but the system is not configured
the way it was asked to be. A test that relies on the requested setting may then be
skipped or pass for the wrong reason. Silent constraints are therefore the most
important ones for our project.

## Effect

An effect is a consequence of an option value that is not a constraint between two
modelled options. It usually concerns parts of the system that are outside the model,
for example protocols that disappear when TLS is turned off.

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `E1`, `E2`, … |
| `when` | yes | The triggering value, as `{option: value}` |
| `result` | yes | What changes |
| `evidence` | yes | Source location |
| `verified` | yes | Command and observation |

## Evidence rule

Every option, constraint and effect must point to a location in the source code, and
every constraint and effect must be confirmed by actually running the build system.
This follows the project's methodology: AI may propose entries, but an entry is only
accepted after it has been checked against the source and confirmed with a tool.

## Configurations

A configuration is a YAML file that picks values for some options. Options that are not
listed keep their default. Example:

```yaml
name: no-ftp-no-cookies
system: curl
values:
  tls: openssl
  ftp: disabled
  cookies: disabled
```

The automation script (D5) translates it using the `flags` field of each option:

```sh
./configure --with-openssl --disable-ftp --disable-cookies
```
