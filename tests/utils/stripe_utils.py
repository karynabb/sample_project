import stripe


def create_stripe_event(
    event_type: str | None = None, product_type: str | None = None
) -> stripe.Event:
    event = stripe.Event()
    event["type"] = event_type
    event["data"] = {}
    event["data"]["object"] = {}
    event["data"]["object"]["metadata"] = {}
    event["data"]["object"]["metadata"]["product_type"] = product_type
    return event
