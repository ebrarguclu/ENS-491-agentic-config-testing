# scripts/

Scripts that do the repetitive work for us: building curl, running its tests and
checking our model. They are written with AI help and reviewed by the team.

## Ready to use

| Script | What it does |
|---|---|
| [verify_curl_constraints.sh](verify_curl_constraints.sh) | Re-checks every rule and side effect in `models/curl.yaml` by running curl's `configure` with combinations that break them (13 checks). Takes a few minutes and saves the results in `results/verification/` |

How to run it, from the repository root (curl must be downloaded into `systems/curl`
first, see [systems/README.md](../systems/README.md)):

```sh
bash scripts/verify_curl_constraints.sh
```

It works on Linux and macOS. On macOS it automatically uses Homebrew's `openssl@3`.

## Coming next (D5)

```sh
scripts/run_config.sh <configuration-file>
```

You give it a configuration file (see [models/schema.md](../models/schema.md#configuration-files)),
and it will:

1. turn the configuration into `configure` flags and build curl,
2. run curl's tests (all of them, or a chosen range),
3. measure code coverage (D6),
4. save everything in `results/<configuration-name>/`.
