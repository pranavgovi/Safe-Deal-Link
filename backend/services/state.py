"""
this defines the available states and also the allowed transitions
"""
CREATED = "CREATED"
SCREENED = "SCREENED"
AUTHORIZED = "AUTHORIZED"
SHIPPED = "SHIPPED"
DELIVERED = "DELIVERED"
VERIFYING = "VERIFYING"
CAPTURED = "CAPTURED"
VOIDED = "VOIDED"
NEEDS_HUMAN = "NEEDS_HUMAN"

ALL_STATES = {
    CREATED,
    SCREENED,
    AUTHORIZED,
    SHIPPED,
    DELIVERED,
    VERIFYING,
    CAPTURED,
    VOIDED,
    NEEDS_HUMAN,
}

# Terminal states have no outgoing transitions.
ALLOWED_TRANSITIONS = {
    CREATED: {SCREENED},
    SCREENED: {AUTHORIZED},
    AUTHORIZED: {SHIPPED, VOIDED, NEEDS_HUMAN},
    SHIPPED: {DELIVERED, VOIDED, NEEDS_HUMAN},
    DELIVERED: {VERIFYING},
    VERIFYING: {CAPTURED, VOIDED, NEEDS_HUMAN},
    NEEDS_HUMAN: {CAPTURED, VOIDED},
    CAPTURED: set(),
    VOIDED: set(),
}


class InvalidTransition(Exception):
    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        super().__init__(f"Cannot move deal from {current} to {target}")


def transition(deal, target: str):
    """Mutates deal.status in place if the transition is legal, else raises.
    Caller is responsible for committing the session and logging an Event."""
    current = deal.status
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(current, target)
    deal.status = target
    return deal
