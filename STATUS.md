# Current implementation status

The integrated experimental branch contains the local coordination runtime,
accepted-history ownership fixes, the host-owned state-reference bridge, and the
minimal neural substrate described in SUBSTRATE.md.

Verified local coordination includes node identity, ordering, exact retry/conflict
handling, bounded queues, routing, availability, isolated handler failures,
accepted-history replay, and hashed pending-queue snapshots/restoration.

The host bridge is tested with the real dedicated neural brain; it carries no
embedded learned state and grants no host execution authority. The calculator
is an independent library experiment and is not automatically used by the bus,
bridge or UC. Backend and learning claims are scoped in SUBSTRATE.md.

Still outside the verified scope: distributed transport, retained dead-letter
history as a durable bus subsystem, arbitrary architecture migration, accelerators,
native Windows/WALDO training, and general intelligence.
