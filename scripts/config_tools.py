#!/usr/bin/env python3
"""Helpers for run_config.sh. Bash cannot read YAML or write JSON reliably, so these
two small jobs live here.

  config_tools.py flags <model.yaml> <config.yaml>
      Prints "name=<name>", then one configure flag per line.

  config_tools.py summary <results-dir> --flags ... --test-args ... (see main)
      Reads the logs in <results-dir> and writes summary.json. Exits 0 only if the build
      worked and no test failed.

  config_tools.py table <results-dir> [--machine "Darwin arm64"]
      Writes coverage_table.md from all the summary.json files in <results-dir>, or only
      from the runs made on one machine.

  config_tools.py merge <name> <run-dir> <run-dir> ...
      Combines the coverage of several runs into results/<name>/: a line or branch counts
      as covered if any of the runs covered it.

This file does not check the rules between options. A combination that breaks a rule is
passed to configure on purpose, because seeing what configure does with it is the point.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def die(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


def load_yaml(path):
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        die(f"cannot read {path}: {e}")


def cmd_flags(model_path, config_path):
    model = load_yaml(model_path)
    config = load_yaml(config_path)

    # The name becomes a folder under results/, so it must be a plain folder name.
    name = str(config.get("name", ""))
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        die(f"{config_path}: 'name' must use only letters, digits, '.', '_', '-' (got '{name}')")

    options = {option["id"]: option for option in model["options"]}
    print(f"name={name}")
    # Options not mentioned keep their default, so they get no flag.
    for option_id, value in (config.get("values") or {}).items():
        if option_id not in options:
            die(f"{config_path}: unknown option '{option_id}'")
        flags = options[option_id]["flags"]
        if value not in flags:
            die(f"{config_path}: '{option_id}' cannot be '{value}' (allowed: {', '.join(flags)})")
        print(flags[value])


def parse_tests(log_path):
    """Reads the summary lines that curl's runtests.pl prints at the end."""
    text = Path(log_path).read_text(errors="replace")

    done = re.search(r"TESTDONE: (\d+) tests out of (\d+) reported OK", text)
    passed, total = (int(done.group(1)), int(done.group(2))) if done else (0, 0)

    skipped = re.search(r"TESTINFO: (\d+) tests were skipped", text)
    reasons = {
        reason: int(count)
        for reason, count in re.findall(r'TESTINFO: "(.*?)" (\d+) times? \(', text)
    }
    failed_ids = re.search(r"TESTFAIL: These test cases failed: (.*)", text)

    return {
        "ran": total,
        "passed": passed,
        "failed": total - passed,
        "skipped": int(skipped.group(1)) if skipped else 0,
        "failed_tests": failed_ids.group(1).split() if failed_ids else [],
        "skip_reasons": reasons,
    }


def parse_version(path):
    """Reads `curl --version`: what was really built, not what we asked for."""
    version = Path(path)
    if not version.exists():
        return None
    lines = version.read_text(errors="replace").splitlines()

    def words_after(prefix):
        for line in lines:
            if line.startswith(prefix):
                return line[len(prefix):].split()
        return []

    return {
        "version": lines[0] if lines else "",
        "protocols": words_after("Protocols:"),
        "features": words_after("Features:"),
    }


def parse_coverage(path):
    """Adds up the per-file totals in an lcov.info file."""
    info = Path(path)
    if not info.exists():
        return None
    # LF/LH: lines found/hit, FNF/FNH: functions, BRF/BRH: branches (one per direction of
    # each if/switch decision).
    totals = {"LF": 0, "LH": 0, "FNF": 0, "FNH": 0, "BRF": 0, "BRH": 0}
    for line in info.read_text(errors="replace").splitlines():
        key, _, value = line.partition(":")
        if key in totals:
            totals[key] += int(value)
    if totals["LF"] == 0:
        return None

    def percent(covered, total):
        return round(100 * covered / total, 1) if total else 0.0

    return {
        "lines_covered": totals["LH"],
        "lines_total": totals["LF"],
        "lines_percent": percent(totals["LH"], totals["LF"]),
        "functions_covered": totals["FNH"],
        "functions_total": totals["FNF"],
        "functions_percent": percent(totals["FNH"], totals["FNF"]),
        "branches_covered": totals["BRH"],
        "branches_total": totals["BRF"],
        "branches_percent": percent(totals["BRH"], totals["BRF"]),
    }


def cmd_summary(args):
    results = Path(args.results_dir)
    build_ok = args.configure_exit == 0 and args.make_exit == 0 and args.tests_build_exit == 0
    tests = parse_tests(results / "tests.log") if args.runtests_exit is not None else None
    coverage = parse_coverage(results / "coverage" / "lcov.info")

    summary = {
        "name": args.name,
        "machine": args.machine,
        "curl_source": args.curl_source,
        "date": args.date,
        "configure_flags": args.flags,
        "build": {
            "ok": build_ok,
            "configure_exit": args.configure_exit,
            "make_exit": args.make_exit,
            "tests_build_exit": args.tests_build_exit,
            "seconds": args.build_seconds,
        },
        "tests": None
        if tests is None
        else {
            "selection": args.test_args or "all",
            "runtests_exit": args.runtests_exit,
            "seconds": args.test_seconds,
            **tests,
        },
        "built": parse_version(results / "curl_version.txt"),
        "coverage": coverage,
    }
    (results / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print()
    print(f"Configuration: {args.name}")
    print(f"Flags:         {args.flags}")
    print(f"Build:         {'ok' if build_ok else 'FAILED'}")
    if tests:
        print(f"Tests:         {tests['passed']} passed, {tests['failed']} failed, "
              f"{tests['skipped']} skipped")
    if coverage:
        print(f"Coverage:      {coverage['lines_percent']}% of lines "
              f"({coverage['lines_covered']} of {coverage['lines_total']})")
        print(f"               {coverage['branches_percent']}% of branches "
              f"({coverage['branches_covered']} of {coverage['branches_total']})")
    elif tests:
        print(f"Coverage:      NOT AVAILABLE, see {results / 'coverage' / 'lcov.log'}")
    print(f"Results:       {results}")

    all_good = build_ok and tests is not None and tests["failed"] == 0
    sys.exit(0 if all_good else 1)


def lcov_options():
    """The same branch settings run_config.sh uses (the name changed in lcov 2.0)."""
    version = subprocess.run(["lcov", "--version"], capture_output=True, text=True).stdout
    major = re.search(r"version (\d+)", version)
    if major and int(major.group(1)) >= 2:
        return ["--rc", "branch_coverage=1", "--ignore-errors", "inconsistent,inconsistent"]
    return ["--rc", "lcov_branch_coverage=1"]


def cmd_merge(name, run_dirs, results_dir):
    """Combines the lcov.info of several runs into results/<name>/.

    A line, function or branch counts as covered if any of the runs covered it. The total
    is all the code compiled in at least one of the runs.
    """
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        die(f"name must use only letters, digits, '.', '_', '-' (got '{name}')")
    if len(run_dirs) < 2:
        die("give at least two run folders to merge")

    runs = []
    for run_dir in run_dirs:
        run = Path(run_dir)
        info, summary = run / "coverage" / "lcov.info", run / "summary.json"
        if not info.exists() or not summary.exists():
            die(f"{run} has no coverage/lcov.info or summary.json")
        s = json.loads(summary.read_text())
        runs.append({"dir": run, "info": info, "summary": s})

    # Coverage from different machines or curl versions would mix two different things.
    for key in ("machine", "curl_source"):
        found = sorted({r["summary"][key] for r in runs})
        if len(found) > 1:
            die(f"the runs differ in {key}: {', '.join(found)}")

    out = Path(results_dir) / name
    coverage_dir = out / "coverage"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    command = ["lcov", *lcov_options()]
    for r in runs:
        command += ["--add-tracefile", str(r["info"].resolve())]
    command += ["--output-file", str((coverage_dir / "lcov.info").resolve())]
    with open(coverage_dir / "lcov.log", "w") as log:
        if subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode != 0:
            die(f"lcov could not merge the runs, see {coverage_dir / 'lcov.log'}")

    coverage = parse_coverage(coverage_dir / "lcov.info")
    if coverage is None:
        die(f"the merged file is empty, see {coverage_dir / 'lcov.log'}")
    # If one run has no branch data, the merged branch numbers would be too low.
    missing = [r["summary"]["name"] for r in runs
               if not (r["summary"].get("coverage") or {}).get("branches_total")]
    if missing:
        for key in ("branches_covered", "branches_total", "branches_percent"):
            coverage[key] = None

    first = runs[0]["summary"]
    summary = {
        "kind": "combined",
        "name": name,
        "machine": first["machine"],
        "curl_source": first["curl_source"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "runs": [r["summary"]["name"] for r in runs],
        "runs_without_branch_data": missing,
        "coverage": coverage,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"Combined:      {name} ({len(runs)} runs: {', '.join(summary['runs'])})")
    print(f"Coverage:      {coverage['lines_percent']}% of lines "
          f"({coverage['lines_covered']} of {coverage['lines_total']})")
    print(f"               {coverage['functions_percent']}% of functions "
          f"({coverage['functions_covered']} of {coverage['functions_total']})")
    if missing:
        print(f"               branches: not available, no branch data in {', '.join(missing)}")
    else:
        print(f"               {coverage['branches_percent']}% of branches "
              f"({coverage['branches_covered']} of {coverage['branches_total']})")
    print(f"Results:       {out}")


def cmd_table(results_dir, machine=None):
    """Writes results/coverage_table.md from every results/<name>/summary.json.

    With a machine, only runs from that machine are listed, so that numbers from two
    machines do not end up in one table.
    """
    results = Path(results_dir)
    everything = [json.loads(p.read_text()) for p in sorted(results.glob("*/summary.json"))]
    if machine:
        everything = [s for s in everything if s.get("machine") == machine]
    if not everything:
        die(f"no summary.json found under {results}" + (f" for machine '{machine}'" if machine else ""))
    summaries = [s for s in everything if s.get("kind") != "combined"]
    combined = sorted((s for s in everything if s.get("kind") == "combined"),
                      key=lambda s: s["name"])
    summaries.sort(key=lambda s: (s["name"] != "default", s["name"]))

    combined_rows = []
    for s in combined:
        c = s["coverage"]
        branches = f"{c['branches_percent']}%" if c.get("branches_total") else "-"
        combined_rows.append(
            f"| {s['name']} | {len(s['runs'])}: {', '.join(s['runs'])} | {s['machine']} "
            f"| {c['lines_percent']}% | {c['lines_covered']:,} / {c['lines_total']:,} "
            f"| {c['functions_percent']}% | {branches} |"
        )

    rows = []
    for s in summaries:
        config = load_yaml(results / s["name"] / "config.yaml")
        chosen = config.get("values") or {}
        if len(chosen) > 5:
            # A full configuration is too long for one cell; link to it instead.
            values = f"[{len(chosen)} options]({s['name']}/config.yaml)"
        else:
            values = "`" + (", ".join(f"{k}={v}" for k, v in chosen.items()) or "(none)") + "`"
        t, c = s["tests"], s["coverage"]
        if t and c:
            # Runs from before branch coverage was added have no branch numbers.
            branches = f"{c['branches_percent']}%" if c.get("branches_total") else "-"
            rows.append(
                f"| {s['name']} | {values} | {s['machine']} | {s['date']} | {t['selection']} "
                f"| {t['passed']} | {t['failed']} | {t['skipped']} | {c['lines_percent']}% "
                f"| {c['lines_covered']:,} / {c['lines_total']:,} | {c['functions_percent']}% "
                f"| {branches} |"
            )
        else:
            rows.append(f"| {s['name']} | {values} | {s['machine']} | {s['date']} "
                        f"| - | build failed | - | - | - | - | - | - |")

    first = summaries[0]
    combined_section = [] if not combined_rows else [
        "## Combined coverage of several runs (D10)",
        "",
        "Written by `scripts/config_tools.py merge`. A line, function or branch counts as",
        "covered if **any** of the runs covered it. The total is all the code compiled in at",
        "least one of the runs.",
        "",
        "| Name | Runs | Machine | Line coverage | Lines covered / total | Function coverage | Branch coverage |",
        "|---|---|---|---|---|---|---|",
        *combined_rows,
        "",
    ]
    text = "\n".join([
        "# Coverage per configuration (D6, D10)",
        "",
        "Generated by `scripts/config_tools.py table results`. Do not edit by hand.",
        "",
        f"- curl: {first['curl_source']}",
        "- Compare runs only from the same machine: test servers and libraries differ between",
        "  machines, so the same configuration gives different numbers.",
        "",
        "| Configuration | Values | Machine | Date | Tests run | Passed | Failed | Skipped | Line coverage | Lines covered / total | Function coverage | Branch coverage |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        *combined_section,
        "## How to read this table",
        "",
        "Each percentage is measured against the code of **that** build. Turning an option off",
        "removes code, so the total changes too. A higher percentage does not always mean more",
        "code was tested: compare the \"Lines covered / total\" column as well.",
        "",
        "Branch coverage counts both directions of every `if`/`switch` decision. A \"-\" means",
        "the run was made before branch coverage was measured.",
        "",
        "A test is skipped when this build or this machine lacks something it needs. The reasons",
        "for each run are in `skip_reasons` in `results/<configuration>/summary.json`.",
        "",
    ])
    (results / "coverage_table.md").write_text(text)
    print(f"Wrote {results / 'coverage_table.md'} ({len(rows)} configurations)")


def optional_int(value):
    return None if value == "" else int(value)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    flags = commands.add_parser("flags")
    flags.add_argument("model")
    flags.add_argument("config")

    summary = commands.add_parser("summary")
    summary.add_argument("results_dir")
    for name in ("name", "machine", "curl-source", "date", "flags", "test-args"):
        summary.add_argument(f"--{name}", default="")
    for name in ("configure-exit", "make-exit", "tests-build-exit", "runtests-exit",
                 "build-seconds", "test-seconds"):
        summary.add_argument(f"--{name}", type=optional_int, default=None)

    table = commands.add_parser("table")
    table.add_argument("results_dir")
    table.add_argument("--machine", help='only list runs from this machine, e.g. "Darwin arm64"')

    merge = commands.add_parser("merge")
    merge.add_argument("name")
    merge.add_argument("run_dirs", nargs="+")
    merge.add_argument("--results-dir", default=str(Path(__file__).resolve().parent.parent / "results"))

    args = parser.parse_args()
    if args.command == "flags":
        cmd_flags(args.model, args.config)
    elif args.command == "table":
        cmd_table(args.results_dir, args.machine)
    elif args.command == "merge":
        cmd_merge(args.name, args.run_dirs, args.results_dir)
    else:
        cmd_summary(args)


if __name__ == "__main__":
    main()
