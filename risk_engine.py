class RiskEngine:
    """
    Risk management engine that enforces position and order size limits.
    
    Tracks positions per symbol and validates orders before execution.
    """
    
    def __init__(self, max_order_size=1000, max_position=2000):
        """
        Initialize the risk engine.
        
        Args:
            max_order_size: Maximum quantity allowed per order
            max_position: Maximum absolute position allowed per symbol
        """
        self.max_order_size = max_order_size
        self.max_position = max_position
        self.positions = {}  # symbol -> net position (positive=long, negative=short)
    
    def check(self, order) -> bool:
        """
        Validate an order against risk limits.
        
        Args:
            order: Order object with symbol, qty, and side attributes
                   side should be 'BUY'/'1' or 'SELL'/'2'
        
        Returns:
            True if order passes all risk checks, False otherwise
        """
        symbol = order.symbol
        qty = order.qty
        side = order.side
        
        # Check 1: Order size limit
        if qty > self.max_order_size:
            print(f"RISK REJECT: Order size {qty} exceeds max order size {self.max_order_size} for {symbol}")
            return False
        
        # Get current position for this symbol (default to 0)
        current_position = self.positions.get(symbol, 0)
        
        # Calculate position change based on side
        # BUY (side='1' or 'BUY') increases position, SELL (side='2' or 'SELL') decreases
        if side in ['1', 'BUY', 'Buy']:
            position_change = qty
        elif side in ['2', 'SELL', 'Sell']:
            position_change = -qty
        else:
            print(f"RISK REJECT: Invalid side '{side}' for {symbol}")
            return False
        
        # Calculate hypothetical new position
        new_position = current_position + position_change
        
        # Check 2: Position limit (absolute value)
        if abs(new_position) > self.max_position:
            print(f"RISK REJECT: New position {new_position} would exceed max position "
                  f"±{self.max_position} for {symbol} (current: {current_position})")
            return False
        
        # All checks passed
        return True
    
    def update_position(self, order):
        """
        Update position after an order fill.
        
        Args:
            order: Filled order with symbol, qty, and side attributes
        """
        symbol = order.symbol
        qty = order.qty
        side = order.side
        
        # Get current position (default to 0)
        current_position = self.positions.get(symbol, 0)
        
        # Calculate position change
        if side in ['1', 'BUY', 'Buy']:
            position_change = qty
        elif side in ['2', 'SELL', 'Sell']:
            position_change = -qty
        else:
            raise ValueError(f"Invalid side '{side}' in update_position")
        
        # Update position
        new_position = current_position + position_change
        self.positions[symbol] = new_position
        
        print(f"POSITION UPDATE: {symbol} {current_position:+d} -> {new_position:+d} "
              f"(filled {qty} {side})")
    
    def get_position(self, symbol):
        """Get current position for a symbol."""
        return self.positions.get(symbol, 0)
    
    def get_all_positions(self):
        """Get all current positions."""
        return self.positions.copy()


if __name__ == "__main__":
    from order import Order, OrderState
    
    print("=" * 60)
    print("Risk Engine Test Suite")
    print("=" * 60)
    
    # Initialize risk engine
    risk = RiskEngine(max_order_size=1000, max_position=2000)
    
    print("\n--- TEST 1: Valid order within limits ---")
    order1 = Order(symbol="AAPL", qty=500, side="1")  # Buy 500
    if risk.check(order1):
        print(f"✓ Order APPROVED: Buy {order1.qty} {order1.symbol}")
        order1.transition(OrderState.ACKED)
        order1.transition(OrderState.FILLED)
        risk.update_position(order1)
    else:
        print(f"✗ Order REJECTED")
    
    print("\n--- TEST 2: Another valid order for same symbol ---")
    order2 = Order(symbol="AAPL", qty=800, side="1")  # Buy 800 more
    if risk.check(order2):
        print(f"✓ Order APPROVED: Buy {order2.qty} {order2.symbol}")
        order2.transition(OrderState.ACKED)
        order2.transition(OrderState.FILLED)
        risk.update_position(order2)
    else:
        print(f"✗ Order REJECTED")
    
    print("\n--- TEST 3: Order exceeds max_order_size ---")
    order3 = Order(symbol="MSFT", qty=1500, side="1")  # Too large
    if risk.check(order3):
        print(f"✓ Order APPROVED: Buy {order3.qty} {order3.symbol}")
        order3.transition(OrderState.ACKED)
    else:
        print(f"✗ Order REJECTED")
        order3.transition(OrderState.REJECTED)
    
    print("\n--- TEST 4: Order would exceed max_position ---")
    order4 = Order(symbol="AAPL", qty=800, side="1")  # Would make position 2100
    if risk.check(order4):
        print(f"✓ Order APPROVED: Buy {order4.qty} {order4.symbol}")
        order4.transition(OrderState.ACKED)
    else:
        print(f"✗ Order REJECTED")
        order4.transition(OrderState.REJECTED)
    
    print("\n--- TEST 5: Valid sell order (reduces position) ---")
    order5 = Order(symbol="AAPL", qty=600, side="2")  # Sell 600
    if risk.check(order5):
        print(f"✓ Order APPROVED: Sell {order5.qty} {order5.symbol}")
        order5.transition(OrderState.ACKED)
        order5.transition(OrderState.FILLED)
        risk.update_position(order5)
    else:
        print(f"✗ Order REJECTED")
    
    print("\n--- TEST 6: Different symbol ---")
    order6 = Order(symbol="GOOGL", qty=300, side="1")  # Buy 300 GOOGL
    if risk.check(order6):
        print(f"✓ Order APPROVED: Buy {order6.qty} {order6.symbol}")
        order6.transition(OrderState.ACKED)
        order6.transition(OrderState.FILLED)
        risk.update_position(order6)
    else:
        print(f"✗ Order REJECTED")
    
    print("\n--- TEST 7: Sell creating short position ---")
    order7 = Order(symbol="TSLA", qty=1000, side="2")  # Sell 1000 (go short)
    if risk.check(order7):
        print(f"✓ Order APPROVED: Sell {order7.qty} {order7.symbol}")
        order7.transition(OrderState.ACKED)
        order7.transition(OrderState.FILLED)
        risk.update_position(order7)
    else:
        print(f"✗ Order REJECTED")
    
    print("\n--- TEST 8: Order would exceed short position limit ---")
    order8 = Order(symbol="TSLA", qty=1500, side="2")  # Would make position -2500
    if risk.check(order8):
        print(f"✓ Order APPROVED: Sell {order8.qty} {order8.symbol}")
        order8.transition(OrderState.ACKED)
    else:
        print(f"✗ Order REJECTED")
        order8.transition(OrderState.REJECTED)
    
    print("\n" + "=" * 60)
    print("Final Positions:")
    print("=" * 60)
    for symbol, position in risk.get_all_positions().items():
        print(f"{symbol}: {position:+d}")

