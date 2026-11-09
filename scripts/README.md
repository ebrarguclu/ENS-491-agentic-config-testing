# scripts/

Automation scripts (deliverables **D5** and **D6**), generated with AI support and
reviewed by the team.

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
