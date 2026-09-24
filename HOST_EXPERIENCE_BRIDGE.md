# AXM host ↔ brain experience bridge v1.1

Status: **bounded integration proof**, not a general host nervous system.

This branch defines the smallest portable contract currently justified by the
AXM direct-learning donor in `mike-axiom-mir/axm-uc-neural` PR #3 at
`163410ce05a42879dca478d8ea0de7f6d17c4820`, and by the exact dedicated neural
core extraction at `mike-axiom-mir/axm-neural-brain`
`a0f5de4b19bf515e145caf50b12130ab740869b5`.

The host remains authoritative for permissions, persistence, observations and
execution. Neural outputs are named advisory values. Every event carries the
exact bridge-contract SHA-256 fingerprint; incompatible contracts fail before
experience is accepted.

## Root contract boundary

v1.1 removes the bridge-local lowercase root serialization. The bridge now
carries an exact reference to the canonical neural root contract
`axm-roots/v0.1` with SHA-256
`7d1eaeb05ce9353bccb5783a045ce9be91bf327c17bd93b47fdb68fd6bc46ed2`.
The owner/source pin is the dedicated neural-core extraction commit above.
This avoids canonizing a second representation of Truth, Agency,
Continuity and Wisdom Before Speed.

The first bounded UC reference uses documented UC routing facts only:
`COMPATIBLE_AND_SUFFICIENT`, artifact verification, candidate reuse and
`UNKNOWN_HOLD`. The neural outputs are experimental reuse/explore
preferences. They do not mutate UC, install candidates or execute routes.

Checkpoint export returns an in-memory payload. Storage location and restore
policy remain host decisions.

Evidence boundary:
- TESTED by the included integration suite: event → neural experience → named
  output.
- TESTED: retained response change under bounded teaching.
- TESTED: checkpoint restore produces equivalent next output.
- TESTED: contract mismatch and checkpoint tamper fail closed.
- TESTED: the bridge root-contract reference matches the loaded neural core.
- CI exercises both the pinned UC donor and the pinned dedicated-core
  extraction with the same bridge tests.
- NOT TESTED: general UC usefulness, cross-host transfer, or long-horizon
  continual-learning quality.

Source boundary: neural implementation code is not copied into this repository.
Integration tests import exact pinned checkouts so provenance remains explicit.
