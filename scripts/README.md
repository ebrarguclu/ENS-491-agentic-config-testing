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

## run_config.sh (D5)

Builds curl with one configuration, runs its tests and saves the results.

### First-time setup

Run these once, from the repository root:

```sh
# 1. Download curl (see systems/README.md for the packages it needs)
git clone --depth 1 --branch curl-8_17_0 https://github.com/curl/curl.git systems/curl

# 2. Install the YAML reader, inside the repository only
python3 -m venv .venv
.venv/bin/pip install pyyaml
```

### Running it

```sh
scripts/run_config.sh models/configs/no-ftp.yaml 1 to 100    # tests 1 to 100
scripts/run_config.sh models/configs/no-ftp.yaml             # all tests
```

A configuration file picks values for some options (see
[models/schema.md](../models/schema.md#configuration-files)). Examples are in
[models/configs/](../models/configs/).

The script:

1. turns the configuration into `configure` flags, using `models/curl.yaml`,
2. removes the previous build, then runs `configure` and `make`,
3. runs curl's tests (`runtests.pl -a -n`, so a failed test does not stop the run),
4. saves everything in `results/<configuration-name>/`, replacing an earlier run with that
   name. See [results/README.md](../results/README.md).

| Exit code | Meaning |
|---|---|
| 0 | curl was built and no test failed |
| 1 | The build failed or a test failed. The reason is in the results folder |
| 2 | It could not start, for example a wrong value in the configuration file |

### Good to know

- A combination that breaks a rule is **not** rejected. It goes to `configure` as it is,
  because seeing what happens is the point. Compare `configure_flags` and `built` in
  `summary.json` to see what was really built.
- Two things are added to every build because they depend on the machine, not on the
  configuration: `--without-libpsl`, and on macOS the path of Homebrew's `openssl@3`.
- If XAMPP is installed, its `pkg-config` breaks the build, so the script hides XAMPP from
  its own `PATH`. Nothing outside the script changes.
- Only one build can exist at a time, because all runs share `systems/curl`. Do not run
  two copies of the script at once.

Tested on macOS (Apple Silicon). Not yet tried on Linux.
