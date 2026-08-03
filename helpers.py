def set_to_int(value):
    if value and value.isdigit():
        value = int(value)
    else:
        value = 0
    return value

def sanitize_input(path: str) -> str:
    return path.replace('"', "").replace("\\", "/")
