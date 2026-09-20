# v0.1.0 release checks

QA date: 2026-09-20. This records executed checks, not intended checks.

- Full suite: **61 passed, 0 failed, 0 skipped**, with warnings treated as errors.
- Ruff lint and formatting: passed, including the README Python example.
- `python -m build`: sdist and wheel both built successfully.
- Distribution inspection: eight package modules and license in the wheel; source, tests, examples, data, figures and documentation in the sdist; no environment/cache/credential files.
- A new Python 3.12 environment installed the built wheel with its dependencies. Its import path and installation metadata confirmed a regular wheel installation, not an editable source import.
- The public README Python example, CLI help, equilibrium CSV export and diode JSON fit ran outside the checkout.
- The complete suite also passed against that installed wheel: **61 passed**.
- The installed package reproduced the nine-case numerical report and all scientific figures. Committed synthetic CSV/metadata and the three PNG figures matched the regenerated files byte for byte in this environment.
- A fresh GitHub clone also passed the README installation, CLI, reproduction, test, lint, formatting and build commands.
- All local Markdown image/document links resolved.
- All three scientific figures were visually inspected for labels, units, scaling, legends, captions and interpretation. SVG and PNG versions represent the same Matplotlib figures.

Scientific gates and measured discrepancies are in [VALIDATION.md](VALIDATION.md) and [validation_report.json](validation_report.json). These verify the stated mathematical models; there are no measured-device validation claims.

The expanded workflow passed on Linux Python 3.11–3.13 and Windows Python 3.12 at commit `8b1f9936927aa2955499342dc9400fe78adbf878` ([verified run](https://github.com/Atabrahim/pn-junction-diagnostics/actions/runs/35481869943)). The final release-record commit and tag are checked again during publication. See [the workflow](https://github.com/Atabrahim/pn-junction-diagnostics/actions/workflows/ci.yml) and [releases](https://github.com/Atabrahim/pn-junction-diagnostics/releases). A successful older run does not substitute for the release commit's checks.
