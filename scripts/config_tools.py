#!/usr/bin/env python3
"""Helpers for run_config.sh. Bash cannot read YAML or write JSON reliably, so these
two small jobs live here.

  config_tools.py flags <model.yaml> <config.yaml>
      Prints "name=<name>", then one configure flag per line.

  config_tools.py summary <results-dir> --flags ... --test-args ... (see main)
      Reads the logs in <results-dir> and writes summary.json. Exits 0 only if the build
      worked and no test failed.

This file does not check the rules between options. A combination that breaks a rule is
passed to configure on purpose, because seeing what configure does with it is the point.
"""

import argparse
import json
import re
import sys
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


def cmd_summary(args):
    results = Path(args.results_dir)
    build_ok = args.configure_exit == 0 and args.make_exit == 0 and args.tests_build_exit == 0
    tests = parse_tests(results / "tests.log") if args.runtests_exit is not None else None

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
    }
    (results / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print()
    print(f"Configuration: {args.name}")
    print(f"Flags:         {args.flags}")
    print(f"Build:         {'ok' if build_ok else 'FAILED'}")
    if tests:
        print(f"Tests:         {tests['passed']} passed, {tests['failed']} failed, "
              f"{tests['skipped']} skipped")
    print(f"Results:       {results}")

    all_good = build_ok and tests is not None and tests["failed"] == 0
    sys.exit(0 if all_good else 1)


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

    args = parser.parse_args()
    if args.command == "flags":
        cmd_flags(args.model, args.config)
    else:
        cmd_summary(args)


if __name__ == "__main__":
    main()
