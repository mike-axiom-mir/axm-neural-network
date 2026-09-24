# Coordination Protocol v0.1

## Separation of concerns

`axm-neural-network` coordinates node-to-node events. A node may wrap an AXM neural brain, a software-bound neural instance, a deterministic software agent, or a test double. The network never interprets, averages, merges, synchronizes, trains, or rewrites neural weights.

## Identity and compatibility

Each node registers a stable node identity, the exact SHA-256 fingerprint of the interface contract it accepts, an optional fingerprint identifying its brain snapshot or brain identity, and a sorted set of advertised capabilities.

The interface fingerprint intentionally uses the same canonical JSON rule as the donor AXM Direct Brain `BrainIOContract.fingerprint`: UTF-8 JSON, sorted keys, compact separators, SHA-256.

## Event envelope

Accepted events bind source, target, source→target sequence number, event kind, target interface fingerprint, JSON payload, and optional parent event id. The complete immutable body is SHA-256 addressed as the `event_id`.

## Delivery rules

For every source→target pair, accepted sequence numbers start at zero and are contiguous. An event with a gap or stale unknown sequence is rejected as `OUT_OF_ORDER`. Re-sending the exact accepted event is `DUPLICATE` and does not enqueue a second copy.

A target queue is bounded. When full, the event is rejected as `BACKPRESSURE`; its sequence is not consumed, so the sender can retry the exact event later. Unavailable nodes and incompatible contracts are explicit rejections and do not consume sequence.

## Failure isolation

A node handler failure does not crash the coordinator or alter another node's queue. The failed event becomes an inspectable dead letter and later queued events remain available.

## Replay and restart

The coordinator emits a complete canonical snapshot containing node descriptors, availability, queues, event log, duplicate index, sequence cursors, dead letters and deterministic receipts. The snapshot is SHA-256 protected and restored only after integrity and structural checks.

Accepted event history can also be replayed into a fresh in-process coordinator. Replay reproduces event order and ids. This is coordination replay only; it does not replay or modify node-local neural learning state.

## Authority boundary

v0.1 is in-process only. It contains no socket client/server, cloud connector, shell invocation, tool executor, or filesystem persistence. Any future transport or persistence adapter must be supplied explicitly by the host and preserve these protocol semantics.
