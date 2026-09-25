# Coordination Protocol v0.1

## Current semantics

A node registers a stable identity, lineage label, interface fingerprint, optional brain fingerprint, and capability metadata. The fingerprints are treated as identity/compatibility evidence only; the coordinator does not inspect or alter neural parameters.

Events bind source, target, sequence number, kind, interface fingerprint, data, and optional parent event key. For each source-to-target pair, accepted sequence numbers are contiguous from zero.

The current local bus returns explicit outcomes for duplicate events, unavailable or unknown nodes, interface mismatch, sequence gaps, and queue backpressure. Accepted events are kept in order in an in-memory event log. A fresh local bus can be reconstructed by replaying that accepted log against the same node descriptors.

Capability lookup is deterministic by node id. Handler exceptions can be contained and reported without becoming coordinator exceptions.

## Authority boundary

The current transport is in-process only. This repository does not grant itself internet, cloud, shell, tool, or filesystem authority. Future transports must be explicit host-supplied adapters.

## State boundary

Node-local learned state is outside this protocol. No operation here averages, merges, synchronizes, trains, or silently replaces neural weights.

## Open durability work

Full snapshot/restore for partially delivered queues, availability state, retained dead-letter history, richer provenance receipts, and dedicated-brain compatibility fixtures remain open and must be verified before being claimed complete.
