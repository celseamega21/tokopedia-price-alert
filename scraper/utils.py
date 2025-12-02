def clean_price(price):
    """"Clean price string from non-numeric characters"""  
    if isinstance(price, int):
        return price
    if isinstance(price, str):
        cleaned = ''.join(c for c in price if c.isdigit())
        return int(cleaned) if cleaned else 0
    else:
        return 0