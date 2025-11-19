from utils.fix_class import FixClass

class FixParser:
    """
    Parse FIX protocol messages into structured dictionaries.
    
    FIX tags reference:
    - 8: BeginString (FIX version)
    - 35: MsgType (D=NewOrderSingle, S=Quote, etc.)
    - 55: Symbol
    - 54: Side (1=Buy, 2=Sell)
    - 38: OrderQty
    - 40: OrdType (1=Market, 2=Limit)
    - 44: Price
    - 10: CheckSum
    """
    
    # Common FIX tag names
    TAG_NAMES = {
        '8': 'BeginString',
        '9': 'BodyLength',
        '35': 'MsgType',
        '49': 'SenderCompID',
        '56': 'TargetCompID',
        '34': 'MsgSeqNum',
        '52': 'SendingTime',
        '55': 'Symbol',
        '54': 'Side',
        '38': 'OrderQty',
        '40': 'OrdType',
        '44': 'Price',
        '132': 'BidPx',
        '133': 'OfferPx',
        '134': 'BidSize',
        '135': 'OfferSize',
        '10': 'CheckSum'
    }
    
    # Message type codes
    MSG_TYPES = {
        'D': 'NewOrderSingle',
        'S': 'Quote',
        '8': 'ExecutionReport',
        '0': 'Heartbeat',
        'A': 'Logon'
    }
    
    # Required tags for different message types
    REQUIRED_TAGS = {
        'D': ['35', '55', '54', '38', '40'],  # NewOrderSingle: MsgType, Symbol, Side, Qty, OrdType
        'S': ['35', '55', '132', '133']        # Quote: MsgType, Symbol, BidPx, OfferPx
    }
    
    def parse(self, raw_message: str, delimiter='|', validate=True) -> dict:
        """
        Parse a FIX message string into a dictionary.
        
        Args:
            raw_message: Raw FIX message (fields separated by delimiter)
            delimiter: Field separator (default '|', use '\x01' for SOH)
            validate: Whether to validate required tags
            
        Returns:
            Dictionary with tag numbers as keys and values as strings
            
        Raises:
            ValueError: If message is invalid or required tags are missing
        """
        if not raw_message:
            raise ValueError("Empty FIX message")
        
        # Split message into tag=value pairs
        fields = [f.strip() for f in raw_message.split(delimiter) if f.strip()]
        
        if not fields:
            raise ValueError("No valid fields in FIX message")
        
        parsed = {}
        
        for field in fields:
            if '=' not in field:
                raise ValueError(f"Invalid FIX field format: '{field}' (missing '=')")
            
            tag, value = field.split('=', 1)
            tag = tag.strip()
            value = value.strip()
            
            if not tag:
                raise ValueError("Empty tag in FIX field")
            
            parsed[tag] = value
        
        # Validate message has MsgType (tag 35)
        if '35' not in parsed:
            raise ValueError("Missing required tag 35 (MsgType)")
        
        # Perform validation if requested
        if validate:
            self._validate_message(parsed)
        
        return parsed

    def parse_to_object(self, raw_message: str, delimiter='|', validate=True) -> FixClass:
        """
        Parse a FIX message string into a dictionary.
        
        Args:
            raw_message: Raw FIX message (fields separated by delimiter)
            delimiter: Field separator (default '|', use '\x01' for SOH)
            validate: Whether to validate required tags
            
        Returns:
            Dictionary with tag numbers as keys and values as strings
            
        Raises:
            ValueError: If message is invalid or required tags are missing
        """
        if not raw_message:
            raise ValueError("Empty FIX message")
        
        # Split message into tag=value pairs
        fields = [f.strip() for f in raw_message.split(delimiter) if f.strip()]
        
        if not fields:
            raise ValueError("No valid fields in FIX message")
        
        parsed = {}
        
        for field in fields:
            if '=' not in field:
                raise ValueError(f"Invalid FIX field format: '{field}' (missing '=')")
            
            tag, value = field.split('=', 1)
            tag = tag.strip()
            value = value.strip()
            
            if not tag:
                raise ValueError("Empty tag in FIX field")
            
            parsed[tag] = value
        
        # Validate message has MsgType (tag 35)
        if '35' not in parsed:
            raise ValueError("Missing required tag 35 (MsgType)")
        
        # Perform validation if requested
        if validate:
            self._validate_message(parsed)

        fix_obj = FixClass(parsed)
        
        return fix_obj
    
    def _validate_message(self, parsed: dict):
        """
        Validate that required tags are present based on message type.
        
        Args:
            parsed: Parsed FIX message dictionary
            
        Raises:
            ValueError: If required tags are missing
        """
        msg_type = parsed.get('35')
        
        if msg_type in self.REQUIRED_TAGS:
            required = self.REQUIRED_TAGS[msg_type]
            missing = [tag for tag in required if tag not in parsed]
            
            if missing:
                missing_names = [f"{tag} ({self.TAG_NAMES.get(tag, 'Unknown')})" 
                               for tag in missing]
                raise ValueError(
                    f"Missing required tags for {self.MSG_TYPES.get(msg_type, msg_type)}: "
                    f"{', '.join(missing_names)}"
                )
        
        # Additional validation for price-related tags
        if msg_type == 'D' and parsed.get('40') == '2':  # Limit order
            if '44' not in parsed:
                raise ValueError("Limit orders (OrdType=2) require tag 44 (Price)")
        
        # Validate Side values (must be 1 or 2)
        if '54' in parsed and parsed['54'] not in ['1', '2']:
            raise ValueError(f"Invalid Side value: {parsed['54']} (must be 1=Buy or 2=Sell)")
    
    def format_message(self, parsed: dict) -> str:
        """
        Format a parsed message with human-readable field names.
        
        Args:
            parsed: Parsed FIX message dictionary
            
        Returns:
            Formatted string representation
        """
        lines = []
        msg_type = parsed.get('35', 'Unknown')
        msg_type_name = self.MSG_TYPES.get(msg_type, msg_type)
        
        lines.append(f"Message Type: {msg_type_name} ({msg_type})")
        lines.append("-" * 50)
        
        for tag, value in parsed.items():
            if tag == '35':  # Skip MsgType as we already showed it
                continue
            name = self.TAG_NAMES.get(tag, f'Tag{tag}')
            
            # Add human-readable interpretation for some fields
            if tag == '54':  # Side
                side_name = 'Buy' if value == '1' else 'Sell' if value == '2' else 'Unknown'
                lines.append(f"{name} ({tag}): {value} ({side_name})")
            elif tag == '40':  # OrdType
                ord_type = 'Market' if value == '1' else 'Limit' if value == '2' else 'Other'
                lines.append(f"{name} ({tag}): {value} ({ord_type})")
            else:
                lines.append(f"{name} ({tag}): {value}")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    parser = FixParser()
    
    print("=" * 60)
    print("TEST 1: Valid NewOrderSingle (Limit Order)")
    print("=" * 60)
    try:
        msg1 = "8=FIX.4.2|35=D|55=AAPL|54=1|38=100|40=2|44=150.50|10=128"
        parsed1 = parser.parse(msg1)
        print(parser.format_message(parsed1))
        print("\n✓ Parsing successful\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
    
    print("=" * 60)
    print("TEST 2: Valid NewOrderSingle (Market Order)")
    print("=" * 60)
    try:
        msg2 = "8=FIX.4.2|35=D|55=MSFT|54=2|38=50|40=1|10=100"
        parsed2 = parser.parse(msg2)
        print(parser.format_message(parsed2))
        print("\n✓ Parsing successful\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
    
    print("=" * 60)
    print("TEST 3: Valid Quote Message")
    print("=" * 60)
    try:
        msg3 = "8=FIX.4.2|35=S|55=GOOGL|132=2800.25|133=2801.50|134=100|135=100|10=200"
        parsed3 = parser.parse(msg3)
        print(parser.format_message(parsed3))
        print("\n✓ Parsing successful\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
    
    print("=" * 60)
    print("TEST 4: Invalid - Missing Side (tag 54)")
    print("=" * 60)
    try:
        msg4 = "8=FIX.4.2|35=D|55=AAPL|38=100|40=2|10=128"
        parsed4 = parser.parse(msg4)
        print(parser.format_message(parsed4))
        print("\n✓ Parsing successful\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
    
    print("=" * 60)
    print("TEST 5: Invalid - Limit Order Missing Price")
    print("=" * 60)
    try:
        msg5 = "8=FIX.4.2|35=D|55=AAPL|54=1|38=100|40=2|10=128"
        parsed5 = parser.parse(msg5)
        print(parser.format_message(parsed5))
        print("\n✓ Parsing successful\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
    
    print("=" * 60)
    print("TEST 6: Invalid - Quote Missing BidPx")
    print("=" * 60)
    try:
        msg6 = "8=FIX.4.2|35=S|55=GOOGL|133=2801.50|10=200"
        parsed6 = parser.parse(msg6)
        print(parser.format_message(parsed6))
        print("\n✓ Parsing successful\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
    
    print("=" * 60)
    print("TEST 7: Invalid - Bad Side Value")
    print("=" * 60)
    try:
        msg7 = "8=FIX.4.2|35=D|55=AAPL|54=9|38=100|40=1|10=128"
        parsed7 = parser.parse(msg7)
        print(parser.format_message(parsed7))
        print("\n✓ Parsing successful\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
