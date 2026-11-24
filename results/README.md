# results/

The outputs of our runs end up here, so that anyone can look at them later without
running everything again.

| Folder or file | What it contains | Status |
|---|---|---|
| [verification/](verification/) | Results of `scripts/verify_curl_constraints.sh`. Only `summary.md` is uploaded. The long logs stay on your computer | Available |
| `<configuration-name>/` | One folder for each configuration run with `scripts/run_config.sh` (see below). Only `config.yaml` and `summary.json` are uploaded. The rest stays on your computer | Available |
| [coverage_table.md](coverage_table.md) | Line, function and branch coverage for each Mac run: the 8 configurations of D6 and the 10 of the covering array, plus their combined coverage (D10) | Available |
| `combined-<name>/` | The combined coverage of several runs, written by `scripts/config_tools.py merge`. Only `summary.json` is uploaded | Available |
| [d10-results.md](d10-results.md) | What the D10 runs showed: combined coverage, run-to-run difference, failed tests | Available |

The folders ending in `-linux-before` and `-plus-generated` are the D7 runs, made on a
Linux machine. They are not in `coverage_table.md`, because numbers from two different
machines should not be compared in one table (the same configuration passed 1602 tests on
the Mac and 1583 on Linux). Their before/after comparison is in
[tests/generated/before-after.md](../tests/generated/before-after.md). To keep the
machines apart, regenerate the table for one machine only:

```sh
.venv/bin/python scripts/config_tools.py table results --machine "Darwin arm64"
```

Each run folder looks like this:

```
results/<configuration-name>/
├── config.yaml       the exact configuration that was used
├── build.log         output of configure and make
├── tests.log         output of curl's test runner
├── curl_version.txt  `curl --version` of the curl that was really built
├── summary.json      did the build work? how many tests passed, failed, were skipped?
└── coverage/         lcov.info (line, function and branch coverage) and lcov.log
```
