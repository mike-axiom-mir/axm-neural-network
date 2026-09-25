def attempt(event, handler):
    try:
        handler(event)
    except Exception as exc:
        return {
            "status": "HANDLER_FAILED",
            "event": event,
            "error_type": type(exc).__name__,
        }
    return {"status": "DELIVERED", "event": event, "error_type": ""}
