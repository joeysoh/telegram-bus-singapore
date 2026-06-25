def sanitize_number(val,whole_number_only = True):
    # Quick guard check for None or empty values
    if val is None or str(val).strip() == "":
        return None
    
    try:
        # Convert to float first to handle decimals
        num = float(val)
        # If it's a whole number (like 12.0), convert to int
        if num.is_integer() and whole_number_only:
            return int(num)
        return num        
    except (ValueError, TypeError):
        return None