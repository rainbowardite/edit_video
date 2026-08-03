from datetime import datetime

def set_timecode_hour(timecode: str) -> str:
    colon_num = timecode.count(":")
    new_timecode = "00:00:00"

    if colon_num == 1:
        new_timecode = f"00:{timecode}"
    elif colon_num == 0:
        new_timecode = f"00:00:{timecode}"
    else:
        new_timecode = timecode

    return new_timecode

def timecode_to_seconds(timecode: str) -> float:
    if "." in timecode: #deal with ms
        t = datetime.strptime(timecode, "%H:%M:%S.%f")
        return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1000000
    else:
        t = datetime.strptime(timecode, "%H:%M:%S")
        return t.hour * 3600 + t.minute * 60 + t.second

def get_timecode_difference(tc1: str, tc2: str) -> float:
    sec1 = timecode_to_seconds(tc1)
    sec2 = timecode_to_seconds(tc2)
    return abs(sec1 - sec2)
