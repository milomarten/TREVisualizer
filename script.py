import re
from typing import Optional

from models import Time, Order, Schedule, Station

time_regex = re.compile("([0-9]{2}):([0-9]{2})(#?)")


def parse_schedules_from_csv(filename: str) -> Schedule:
    eastbound = "eastbound" in filename
    file = open(filename, "r")
    lines = file.read().splitlines()[1:]

    parsed = [parse_order_from_str(line, eastbound) for line in lines]
    return Schedule(parsed)


def parse_order_from_str(line: str, eastbound: bool) -> Order:
    tokens = line.split("\t")
    train_id = tokens[0]
    time = [parse_time(x) for x in tokens[1:]]
    return Order(train_id, eastbound, time)


def parse_time(time: str) -> Optional[Time]:
    if time == "--:--":
        return None
    parse = re.match(time_regex, time)
    if parse is None:
        raise ValueError

    return Time(int(parse.group(1)), int(parse.group(2)), parse.group(3) == "#")


def find_orders_for_time(orders: list[(str, Time)], search_time: Time) -> list[str]:
    return [id for (id, otime) in orders if otime == search_time]

