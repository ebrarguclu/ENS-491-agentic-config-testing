# scripts/

Automation scripts (deliverables **D5** and **D6**), generated with AI support and
reviewed by the team.

## Available

| Script | Purpose |
|---|---|
| [`verify_curl_constraints.sh`](verify_curl_constraints.sh) | Re-checks every constraint and effect in `models/curl.yaml` by running curl's `configure` (13 checks). Run from the repository root: `bash scripts/verify_curl_constraints.sh` |

## Planned (D5)

Planned interface:

```sh
scripts/run_config.sh <configuration-file>
```

Given one configuration (a set of option values that follows `models/schema.md`), the
script will:

1. configure and build curl with those options,
2. run the curl test suite (or a selected range of tests),
3. collect code coverage (D6),
4. write everything to `results/<configuration-name>/`.
