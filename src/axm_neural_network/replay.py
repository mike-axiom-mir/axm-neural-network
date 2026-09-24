from .bus import LocalBus


def rebuild(descriptors, accepted_events, queue_limit: int = 32) -> LocalBus:
    bus = LocalBus(queue_limit)
    for descriptor in descriptors:
        status = bus.register(descriptor)
        if status != "REGISTERED":
            raise ValueError(f"node registration failed: {status}")
    for event in accepted_events:
        status = bus.accept(event)
        if status != "ACCEPTED":
            raise ValueError(f"event replay failed: {status}")
    return bus
