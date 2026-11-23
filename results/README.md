# results/

The outputs of our runs end up here, so that anyone can look at them later without
running everything again.

| Folder or file | What it contains | Status |
|---|---|---|
| [verification/](verification/) | Results of `scripts/verify_curl_constraints.sh`. Only `summary.md` is uploaded. The long logs stay on your computer | Available |
| `<configuration-name>/` | One folder for each configuration run with `scripts/run_config.sh` (see below). Only `config.yaml` and `summary.json` are uploaded. The rest stays on your computer | Available |
| [coverage_table.md](coverage_table.md) | Coverage for each of the 8 configurations of D6. All of them were run on a Mac | Available |

The folders ending in `-linux-before` and `-plus-generated` are the D7 runs, made on a
Linux machine. They are not in `coverage_table.md`, because numbers from two different
machines should not be compared in one table (the same configuration passed 1602 tests on
the Mac and 1583 on Linux). Their before/after comparison is in
[tests/generated/before-after.md](../tests/generated/before-after.md). Running
`scripts/config_tools.py table results` today would mix both machines into one table, so
check the `machine` field in each `summary.json` before regenerating it.

Each run folder looks like this:

```
results/<configuration-name>/
├── config.yaml       the exact configuration that was used
├── build.log         output of configure and make
├── tests.log         output of curl's test runner
├── curl_version.txt  `curl --version` of the curl that was really built
├── summary.json      did the build work? how many tests passed, failed, were skipped?
└── coverage/         lcov.info (coverage line by line) and lcov.log
```
