import logging

def place_market_order(kite, symbol, exchange, transaction_type, quantity):
    """
    Places a market order using the KiteConnect client.
    """
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange,
            tradingsymbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=kite.PRODUCT_CNC,
            order_type=kite.ORDER_TYPE_MARKET
        )
        logging.info(f"Order placed successfully. ID: {order_id}")
        return order_id
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        return None
