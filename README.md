# AXM Neural Network

**Status: PRODUCTION / HEAVY EXPERIMENTAL**

AXM Neural Network is the local-first deterministic coordination layer between AXM neural brains or software-bound neural nodes.

It is **not** a neural brain implementation. It does not own or modify neural weights, learned state, training loops, host permissions, shell access, filesystem access, cloud authority, or internet authority.

## v0.1 foundation

- explicit stable node identity;
- brain and interface fingerprints;
- deterministic message/event envelopes;
- strict per source→target sequence ordering;
- duplicate/idempotent replay handling;
- bounded per-node queues with explicit backpressure;
- deterministic capability discovery and routing;
- node availability and failure isolation;
- inspectable delivery receipts and event provenance;
- hashed in-memory snapshots for restart/restore;
- replay into a fresh network without changing node-local learned state;
- compatibility with the AXM Direct Brain `axm-brain-io/v0.1` fingerprint rule.

The network coordinates **messages and contracts**, not weights. Neural state remains node-local.

## Authority boundary

The coordination core has no ambient network, cloud, shell, tool, or filesystem authority. v0.1 provides an in-process transport surface only. A future transport may implement the same explicit contract, but authority must be supplied by the host rather than silently acquired here.

## Truth boundary

Passing these tests establishes deterministic local coordination semantics under the covered cases. It does not prove distributed intelligence, semantic understanding, useful collaboration between learned systems, fault tolerance across machines, or correctness of any future external transport.

## AXM roots

Truth before story. Agency / non-domination. Continuity. Wisdom before speed.

Required Notice: Copyright 2026 Mike - Axiom/Mir.
