# models/

Configuration space models (deliverable **D4**).

Planned contents:

| File | Content |
|---|---|
| `schema.md` | The shared model format: for each option its name, type (compile-time / runtime), possible values and default, plus a list of constraints between options |
| `curl.yaml` | The configuration space model of curl in that format, extracted with AI support and checked against the source (`configure.ac`) and official documentation |

The first version of `curl.yaml` covers a focused subset of compile-time options (see
[docs/selection.md](../docs/selection.md#scope-for-the-next-step-d4)).
