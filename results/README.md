# results/

Outputs of experiment runs.

Planned layout:

```
results/
├── <configuration-name>/     # one folder per run of scripts/run_config.sh
│   ├── config.yaml           # the exact configuration used
│   ├── build.log             # configure + make output
│   ├── tests.log             # test runner output
│   ├── summary.json          # build ok?, tests passed / failed / skipped
│   └── coverage/             # coverage report (D6)
└── coverage_table.md         # coverage per configuration, before/after generated tests (D6, D7)
```
