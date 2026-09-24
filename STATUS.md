# Current implementation status

Implemented on `codex/neural-network-coordination-v1`:

- node identity and lineage fields;
- brain/interface fingerprint fields;
- local event envelopes;
- per-pair sequence ordering;
- duplicate handling;
- bounded local queues and backpressure;
- unavailable-node and interface-mismatch rejection;
- accepted-event log.

Still open:

- repository test files and CI;
- capability lookup/routing helpers;
- handler failure/dead-letter handling;
- restart snapshot/restore;
- replay verification after restart.

The README protocol describes the intended v0.1 direction. Items listed as open here are not yet verified implementation claims.
