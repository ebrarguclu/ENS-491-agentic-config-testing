#!/usr/bin/env python3
"""Turns models/curl.yaml into a 2-way covering array of full configurations (D9/D11).

  covering_array.py model-to-pict <model.yaml> <out.txt>
      Writes a PICT model file: one parameter line per option (all 22 values an
      option can take, "auto" excluded, since a covering array needs full
      configurations -- see "Full configurations" in models/schema.md), followed
      by one IF/THEN line per constraint whose on_violation is "error". Silent
      constraints (C1, C3, C4, C5, and the default case of C6) are deliberately
      NOT turned into PICT constraints, because they are exactly what this
      project studies: PICT must be free to generate rows where they fire, and
      only kept away from rows that would simply waste a build.

  covering_array.py rows-to-configs <model.yaml> <pict-output.tsv> <out-dir> [--prefix ca]
      Reads PICT's tab-separated output (one row per generated test case) and
      writes one full configuration YAML per row to <out-dir>, in the same
      format as the hand-written examples in models/configs/.

  covering_array.py verify <model.yaml> <configs-dir>
      Checks, independently of PICT, that every configuration in <configs-dir>
      is full (gives a real value to all 22 options, never "auto"), that no
      configuration violates an error-type constraint, and that every pair of
      option values that is allowed to appear together actually does appear in
      at least one configuration (2-way coverage). Exits non-zero and prints
      what is missing or wrong if anything fails.

This script only generates and checks configurations. It does not build curl or
run tests -- see scripts/run_config.sh for that.
"""

import argparse
import itertools
import sys
from pathlib import Path

import yaml


def die(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


def load_model(path):
    with open(path, encoding="utf-8") as f:
        model = yaml.safe_load(f)
    options = {o["id"]: o for o in model["options"]}
    constraints = model.get("constraints", [])
    return model, options, constraints


def full_values(option):
    """The values a *full* configuration may use for this option: never "auto"."""
    return [v for v in option["values"]]


# --------------------------------------------------------------------- model-to-pict

def cmd_model_to_pict(model_path, out_path):
    model, options, constraints = load_model(model_path)

    lines = [
        f"# PICT model generated from {model_path} ({model['system']} {model['version']}).",
        "# Do not edit by hand -- regenerate with:",
        f"#   python3 scripts/covering_array.py model-to-pict {model_path} {out_path}",
        "#",
        "# One parameter per option (22 for curl). Values match the model's `values`",
        '# list exactly; "auto" is never a parameter value here, because every row of',
        "# a covering array must be a full configuration (models/schema.md).",
        "",
    ]
    for option in model["options"]:
        values = ", ".join(full_values(option))
        lines.append(f"{option['id']}: {values}")

    error_constraints = [c for c in constraints if c.get("on_violation") == "error"]
    if error_constraints:
        lines += [
            "",
            "# Constraints below come only from rules whose on_violation is \"error\" --",
            "# a combination PICT must avoid because it simply fails to build, not",
            "# because it is uninteresting. Silent constraints (on_violation: silent)",
            "# are intentionally left unconstrained: a row that triggers one of them is",
            "# exactly the kind of row this project wants in the covering array.",
        ]
    for c in error_constraints:
        if c["kind"] == "requires":
            (if_id, if_val), = c["if"].items()
            (then_id, then_val), = c["then"].items()
            lines.append(f"# {c['id']}")
            lines.append(f'IF [{if_id}] = "{if_val}" THEN [{then_id}] = "{then_val}";')
        elif c["kind"] == "required":
            # A single mandatory option (e.g. C2: tls). Already guaranteed because
            # every PICT parameter is always assigned a value -- nothing to add.
            lines.append(
                f"# {c['id']}: \"{c['option']}\" is mandatory; already guaranteed, "
                "every PICT parameter always gets a value"
            )
        else:
            die(f"{c['id']}: don't know how to translate constraint kind '{c['kind']}'")

    Path(out_path).write_text("\n".join(lines) + "\n")
    print(f"Wrote {out_path}: {len(options)} parameters, "
          f"{sum(1 for c in error_constraints if c['kind'] == 'requires')} PICT constraint(s) "
          f"from {len(error_constraints)} error-type rule(s).")


# --------------------------------------------------------------------- rows-to-configs

def read_pict_tsv(path):
    lines = Path(path).read_text().splitlines()
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split("\t")
        if len(values) != len(header):
            die(f"{path}: row has {len(values)} fields, expected {len(header)}: {line!r}")
        rows.append(dict(zip(header, values)))
    return rows


def cmd_rows_to_configs(model_path, tsv_path, out_dir, prefix):
    model, options, _ = load_model(model_path)
    rows = read_pict_tsv(tsv_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    missing_params = set(options) - set(rows[0].keys()) if rows else set()
    if missing_params:
        die(f"{tsv_path}: PICT output is missing option(s) {sorted(missing_params)}")

    category_labels = {"protocol": "protocols", "feature": "features", "library": "libraries"}
    width = len(str(len(rows)))
    written = []
    for i, row in enumerate(rows, start=1):
        name = f"{prefix}-{i:0{width}d}"
        lines = [f"name: {name}", f"system: {model['system']}", "values:"]
        for category in ("protocol", "feature", "library"):
            cat_options = [o for o in model["options"] if o["category"] == category]
            if not cat_options:
                continue
            lines.append(f"  # {category_labels[category]} ({len(cat_options)})")
            for option in cat_options:
                value = row[option["id"]]
                if value not in option["values"]:
                    die(f"{tsv_path} row {i}: '{option['id']}' = '{value}' is not one of "
                        f"{option['values']}")
                lines.append(f"  {option['id']}: {value}")
        path = out / f"{name}.yaml"
        path.write_text("\n".join(lines) + "\n")
        written.append(path)

    print(f"Wrote {len(written)} full configuration(s) to {out_dir}/ "
          f"({prefix}-{'1':0>{width}}.yaml .. {prefix}-{len(rows):0{width}d}.yaml)")


# --------------------------------------------------------------------- verify

def is_full(config_values, options):
    problems = []
    for option_id, option in options.items():
        if option_id not in config_values:
            problems.append(f"missing option '{option_id}'")
            continue
        value = config_values[option_id]
        if value == "auto":
            problems.append(f"'{option_id}' is 'auto', not a real value")
        elif value not in option["values"]:
            problems.append(f"'{option_id}' = '{value}' is not one of {option['values']}")
    extra = set(config_values) - set(options)
    if extra:
        problems.append(f"unknown option(s) {sorted(extra)}")
    return problems


def violates_error_constraint(config_values, constraints):
    violations = []
    for c in constraints:
        if c.get("on_violation") != "error" or c["kind"] != "requires":
            continue
        (if_id, if_val), = c["if"].items()
        (then_id, then_val), = c["then"].items()
        if config_values.get(if_id) == if_val and config_values.get(then_id) != then_val:
            violations.append(c["id"])
    return violations


def cmd_verify(model_path, configs_dir):
    model, options, constraints = load_model(model_path)
    option_ids = list(options)
    paths = sorted(Path(configs_dir).glob("*.yaml"))
    if not paths:
        die(f"no .yaml files found in {configs_dir}")

    configs = {}
    ok = True

    for path in paths:
        data = yaml.safe_load(path.read_text())
        values = data.get("values") or {}
        problems = is_full(values, options)
        if problems:
            ok = False
            print(f"NOT FULL: {path.name}: {'; '.join(problems)}")
            continue
        violations = violates_error_constraint(values, constraints)
        if violations:
            ok = False
            print(f"VIOLATES ERROR CONSTRAINT: {path.name}: {', '.join(violations)}")
            continue
        configs[path.name] = values

    print(f"{len(configs)} of {len(paths)} configuration(s) are full and respect every "
          f"error-type constraint.")

    # 2-way coverage: for every pair of options, every pair of their allowed values
    # that is not excluded by an error constraint must appear together in at least
    # one configuration.
    def pair_is_excluded(a_id, a_val, b_id, b_val):
        for c in constraints:
            if c.get("on_violation") != "error" or c["kind"] != "requires":
                continue
            (if_id, if_val), = c["if"].items()
            (then_id, then_val), = c["then"].items()
            # (if_id=if_val) requires (then_id=then_val); a pair that sets if_id to
            # if_val and then_id to something other than then_val is impossible.
            if a_id == if_id and a_val == if_val and b_id == then_id and b_val != then_val:
                return True
            if b_id == if_id and b_val == if_val and a_id == then_id and a_val != then_val:
                return True
        return False

    seen_pairs = set()
    for values in configs.values():
        for a_id, b_id in itertools.combinations(option_ids, 2):
            seen_pairs.add((a_id, values[a_id], b_id, values[b_id]))

    missing = []
    required_pairs = 0
    for a_id, b_id in itertools.combinations(option_ids, 2):
        for a_val, b_val in itertools.product(options[a_id]["values"], options[b_id]["values"]):
            if pair_is_excluded(a_id, a_val, b_id, b_val):
                continue
            required_pairs += 1
            if (a_id, a_val, b_id, b_val) not in seen_pairs:
                missing.append(f"{a_id}={a_val} & {b_id}={b_val}")

    if missing:
        ok = False
        print(f"MISSING {len(missing)} of {required_pairs} required pairs:")
        for m in missing[:40]:
            print(f"  {m}")
        if len(missing) > 40:
            print(f"  ... and {len(missing) - 40} more")
    else:
        print(f"All {required_pairs} required option-value pairs are covered "
              f"by at least one configuration.")

    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    m2p = commands.add_parser("model-to-pict")
    m2p.add_argument("model")
    m2p.add_argument("out")

    r2c = commands.add_parser("rows-to-configs")
    r2c.add_argument("model")
    r2c.add_argument("tsv")
    r2c.add_argument("out_dir")
    r2c.add_argument("--prefix", default="ca")

    verify = commands.add_parser("verify")
    verify.add_argument("model")
    verify.add_argument("configs_dir")

    args = parser.parse_args()
    if args.command == "model-to-pict":
        cmd_model_to_pict(args.model, args.out)
    elif args.command == "rows-to-configs":
        cmd_rows_to_configs(args.model, args.tsv, args.out_dir, args.prefix)
    else:
        cmd_verify(args.model, args.configs_dir)


if __name__ == "__main__":
    main()
