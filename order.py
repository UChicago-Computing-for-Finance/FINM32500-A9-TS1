# order.py
from enum import Enum, auto

class OrderState(Enum):
    NEW = auto()
    ACKED = auto()
    FILLED = auto()
    CANCELED = auto()
    REJECTED = auto()

class Order:
    def __init__(self, symbol, qty, side):
        self.symbol = symbol
        self.qty = qty
        self.side = side

        self.state = OrderState.NEW

    def transition(self, new_state):
        allowed = {
            OrderState.NEW: {OrderState.ACKED, OrderState.REJECTED},
            OrderState.ACKED: {OrderState.FILLED, OrderState.CANCELED},

            # since no outgoing transitions
            OrderState.FILLED: set(),
            OrderState.CANCELED: set(),
            OrderState.REJECTED: set(),
        }

        if new_state in allowed[self.state]:
            self.state = new_state
        else:
            raise ValueError(f"Bad transition: {self.state} -> {new_state}")