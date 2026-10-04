class InputError(ValueError):
    pass


WINDOW = 4


def forecast(series):
    if not isinstance(series, list) or len(series) < WINDOW:
        raise InputError(f"series must have at least {WINDOW} numbers")
    numbers = []
    for value in series:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InputError("series must be numbers")
        numbers.append(float(value))
    last = numbers[-WINDOW:]
    next_value = sum(last) / WINDOW
    return {"next": round(next_value, 4), "window": WINDOW, "used": last}
