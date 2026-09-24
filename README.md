# AXM Neural Network

**Status: PRODUCTION / HEAVY EXPERIMENTAL**

This repository is the local coordination layer between AXM neural brains or software-bound neural nodes. It is not a second brain implementation and it does not modify node-local learned state.

## Current foundation

The specialist branch currently provides explicit node identity and lineage, brain/interface fingerprint fields, local event envelopes, strict per source-to-target ordering, duplicate handling, bounded queues with backpressure, unavailable-node and interface-mismatch rejection, stable capability lookup/routing, an accepted-event log, restart-by-replay helpers, and isolated handler-failure results.

The implementation is in-process only. It has no internet, cloud, shell, tool, or ambient filesystem authority.

## Verification

Repository tests cover queue ordering/bounds, event ordering, duplicate handling, unavailable nodes, incompatible interfaces, deterministic capability selection, handler failure isolation, and accepted-log replay after reconstruction.

Still open before this becomes a complete durable coordination substrate: retained dead-letter history inside the bus, full snapshot/restore of partially delivered queues and availability state, stronger provenance receipts, and a verified compatibility fixture tied to the dedicated neural-brain contract once that contract is canonical there.

## Boundary

Messages and contracts may move between nodes. Neural parameters do not. The network must not silently average, merge, synchronize, or replace learned weights.

Truth before story. Agency / non-domination. Continuity. Wisdom before speed.

Required Notice: Copyright 2026 Mike - Axiom/Mir.
