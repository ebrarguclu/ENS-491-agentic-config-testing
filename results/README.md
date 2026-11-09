# results/

The outputs of our runs end up here, so that anyone can look at them later without
running everything again.

| Folder or file | What it contains | Status |
|---|---|---|
| [verification/](verification/) | Results of `scripts/verify_curl_constraints.sh`. Only `summary.md` is uploaded; the long logs stay on your computer | Available |
| `<configuration-name>/` | One folder for each configuration run with `scripts/run_config.sh` (see below). Only `config.yaml` and `summary.json` are uploaded; the rest stays on your computer | Available |
| `coverage_table.md` | Coverage for each configuration, before and after adding AI-written tests | Coming with D6 and D7 |

Each run folder looks like this:

```
results/<configuration-name>/
├── config.yaml       the exact configuration that was used
├── build.log         output of configure and make
├── tests.log         output of curl's test runner
├── curl_version.txt  `curl --version` of the curl that was really built
├── summary.json      did the build work? how many tests passed, failed, were skipped?
└── coverage/         coverage report (coming with D6)
```
