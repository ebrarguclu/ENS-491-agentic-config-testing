# Plan for D9 to D13

After the third meeting with our advisor, the next part of the project becomes more
systematic. Until D8 we picked configurations by hand and wrote a few targeted tests.
From now on:

1. the configurations to test are chosen by a **covering array** instead of by hand,
2. coverage is measured per run **and** for all runs together, including **branch
   coverage**,
3. the AI writes tests in a **loop**: find code that is still not covered, ask for tests,
   run them, measure again, and stop when a stopping rule says so. Every round is logged.

If a term is unfamiliar, see [Key terms](../README.md#key-terms).

## Phase 0: clean-up before starting (done)

Before D9 we fixed what was left over from D1 to D8, so that the new work starts from
correct documents:

- The D8 demo script showed the wrong `configure` output for the LDAPS step. It now shows
  the real output, and it explains how to build on macOS with OpenSSL 3.
- Different files described the silent rules in different ways ("5 of 6", "4 of 6").
  They now all say the same thing: C1, C3, C4 and C5 are always silent, C6 is silent only
  when the form API is left at its default, and C2 is always an error.
- The Stage 2 analysis now describes the existing tests for C1, C5 and C6 correctly.
- The READMEs now show D1 to D8 as done and list D9 to D13.

## Who does what

| # | Deliverable | Main tasks | Owner | Needs first |
|---|---|---|---|---|
| D9 | Full configurations and a covering array | Full-configuration rule, `auto` options made explicit, LDAP and zlib requirements in the model (done). Write the model as input for a CIT tool. Generate a 2-way covering array and turn every row into a full configuration file. Add a check to `config_tools.py` that rejects a configuration that is not full | Safiye Nur Narman, Rana Keleş | nothing |
| D10 | Running and measuring | Add branch coverage to the run script. Run every configuration of the covering array. Combine the coverage of all runs into one number. Run one configuration twice to see how much the numbers change between identical runs | Rana Keleş | D9 (the branch coverage part can start now, with the D6 configurations) |
| D11 | The AI test-writing loop | List the branches that are still not covered after D10. Ask the AI for curl tests aimed at them. Run the tests and keep the ones that work. Measure again. Stop when the stopping rule is met or a round adds nothing new. Log every round: what was asked, what came back, what was kept, and the coverage before and after | Fethiye Ebrar Güçlü, Safiye Nur Narman | D10 |
| D12 | Evaluation | Coverage gained per round, compared with the covering array alone. How many AI-written tests worked. Which gains are larger than the run-to-run difference measured in D10 | Rana Keleş | D11 |
| D13 | Final report and presentation | Write up D1 to D12 and prepare the presentation | All, led by Fethiye Ebrar Güçlü | D12 |

## Decisions we still have to make

- **Which CIT tool.** NIST ACTS and Microsoft PICT both generate covering arrays. PICT is
  open source and supports constraints. The basic version of ACTS can be downloaded
  directly, while the version with constraint support has to be requested from NIST by
  email.
- **What to do with `ldap` on Linux.** Our Linux machine has no LDAP libraries, so
  `ldap: enabled` stops the build there (R1 in [models/curl.yaml](../models/curl.yaml)).
  We can either forbid that value on Linux, like a constraint, or install the LDAP
  development libraries so both values can be tested.
- **Whether the covering array may break our constraints.** The silent constraints are
  the interesting part of our project, so excluding them would hide exactly what we want
  to see. But a combination that is an error (C2, or C6 with `form-api` given
  explicitly) only wastes a build.
- **The stopping rule for D11.** For example: stop after a fixed number of rounds, or
  when one round adds less coverage than the run-to-run difference from D10.

## Questions for our advisor

- Is 2-way (pairwise) strength enough, or should we also try 3-way?
- Should the covering array contain combinations that break silent constraints on
  purpose?
- Is branch coverage, for each run and for all runs together, the right main measure
  for D10 to D12?
