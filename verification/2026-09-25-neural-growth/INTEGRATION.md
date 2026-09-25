# Neural substrate integration, 2026-09-25

This change preserves main's substrate research direction while retaining the
existing coordination runtime and host-owned state-reference bridge. It adds an
independent small dense neural calculator with inspectable equations, momentum
state, explicit backend switching and controlled learning evidence.

Retained remote histories:

- Main research: `1e2792759260f0f412edaf8a40f02ca62af3d06f`
- Coordination and accepted-history ownership: `d076daceb2e861e1b2c9da953c8be3dd6fd7afc7`
- Host-owned state-reference bridge v2: `06a116b4f7a093ca59729416d7fd0e941d109bea`

The exact bridge parent SHA is checked against Git when preparing publication.
All source heads are retained as commit parents. Research notes and donor
provenance stay present; README and STATUS now describe the executable code.

32 local tests passed, including the real integrated brain bridge, all-parameter
numerical gradient checks, NumPy parity, complete optimizer-state continuation,
held-out learning behavior and atomic rejection of malformed batches. See the
source-hash receipt and network.log for the exact local run. CI independently
checks the bridge against the pinned integrity-tested core commit
`ca750603acefeb5f4bd340d1c08767cd9c18c38a` and installs NumPy 2.3.5 for parity.

The calculator does not automatically become the brain backend or UC substrate.
It has no host execution or persistence authority. Cross-backend numerical
agreement is tolerance-based; only same-backend continuation is compared exactly.
No accelerator, Windows/WALDO or large-model performance claim is made.

The micro-simulation research head `f93ac6ad1958627fe5d1d44f8384ee5c4d6c5989` is also retained as a parent. Four simulator tests and a measured throughput receipt cover the new pure-state and batched execution path.
