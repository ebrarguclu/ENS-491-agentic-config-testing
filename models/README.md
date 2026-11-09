# models/

Configuration space models (deliverable **D4**).

| File | Content |
|---|---|
| [`schema.md`](schema.md) | The model format: options (values, defaults, flags), constraints between options, and effects, each with source evidence |
| [`curl.yaml`](curl.yaml) | The curl model: 22 compile-time options (11 protocols, 9 features, 2 libraries), 6 constraints, 3 effects |
| [`curl_verification.md`](curl_verification.md) | How each constraint and effect was confirmed by running `configure`, and what we found |

Scope: the first version covers a focused subset of curl's ~115 compile-time options
(see [docs/selection.md](../docs/selection.md#scope-for-the-next-step-d4)). Runtime
options will be added once the build-and-test scripts (D5) work.
