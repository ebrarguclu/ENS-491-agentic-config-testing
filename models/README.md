# models/

This folder holds our **configuration model** of curl (deliverable D4): a file that lists
curl's options, their possible values, and the rules between them.

| File | What it is |
|---|---|
| [schema.md](schema.md) | Explains how a model file is written, with real examples. Start here |
| [curl.yaml](curl.yaml) | The curl model itself: 22 build-time options (11 protocols, 9 features, 2 libraries), 6 rules and 3 side effects |
| [curl_verification.md](curl_verification.md) | How we proved each rule by running curl's build system, and what we discovered |
| [configs/](configs/) | Configuration files to use with `scripts/run_config.sh` |

The model covers 22 of curl's roughly 115 build-time options. We started small on
purpose, so that every entry could be checked. Why we picked these 22 is explained in
[docs/selection.md](../docs/selection.md#what-we-model-first). Run-time options will be
added after the D5 scripts work.
