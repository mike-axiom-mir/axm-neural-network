# AXM host ↔ brain experience bridge v1

Status: **bounded integration proof**, not a general host nervous system.

This branch defines the smallest portable contract currently justified by the
AXM direct-learning donor in `mike-axiom-mir/axm-uc-neural` PR #3 at
`163410ce05a42879dca478d8ea0de7f6d17c4820`.

The host remains authoritative for permissions, persistence, observations and
execution. Neural outputs are named advisory values. Every event carries the
exact bridge-contract SHA-256 fingerprint; incompatible contracts fail before
experience is accepted.

The first bounded UC reference uses documented UC routing facts only:
`COMPATIBLE_AND_SUFFICIENT`, artifact verification, candidate reuse and
`UNKNOWN_HOLD`. The neural outputs are experimental reuse/explore
preferences. They do not mutate UC, install candidates or execute routes.

Checkpoint export returns an in-memory payload. Storage location and restore
policy remain host decisions.

Evidence boundary:
- TESTED by the included donor integration suite: event → neural experience →
  named output.
- TESTED: retained response change under bounded teaching.
- TESTED: checkpoint restore produces equivalent next output.
- TESTED: contract mismatch and checkpoint tamper fail closed.
- NOT TESTED: general UC usefulness, cross-host transfer, or long-horizon
  continual-learning quality.

Source boundary: the donor code is not copied into this repository. Integration
tests import the pinned donor checkout so provenance remains explicit.
