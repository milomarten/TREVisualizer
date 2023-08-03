from typing import Optional


class Time:
    def __init__(self, hour: int, minute: int, rollover: bool):
        self.hour = hour
        self.minute = minute
        self.rollover = rollover

    def as_minutes(self) -> int:
        hour = self.hour
        if self.rollover:
            hour += 24
        return (hour * 60) + self.minute

    def __repr__(self):
        return f"{self.hour}:{self.minute} {self.rollover}"

    def __str__(self):
        return f"{self.hour:02}:{self.minute:02}{'#' if self.rollover else ''}"

    def __eq__(self, other):
        return self.hour == other.hour and self.minute == other.minute and self.rollover == other.rollover

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if self.rollover and not other.rollover:
            return False
        elif other.rollover and not self.rollover:
            return True
        elif self.hour < other.hour:
            return True
        elif self.hour > other.hour:
            return False
        else:
            return self.minute < other.minute

    def __gt__(self, other):
        if self.rollover and not other.rollover:
            return True
        elif other.rollover and not self.rollover:
            return False
        elif self.hour > other.hour:
            return True
        elif self.hour < other.hour:
            return False
        else:
            return self.minute > other.minute

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __add__(self, other):
        new_hours = self.hour
        new_minutes = self.minute + other
        new_rollover = self.rollover
        if new_minutes >= 60:
            new_hours += (new_minutes // 60)
            new_minutes = new_minutes % 60
        if new_hours >= 24:
            new_rollover = True
            new_hours = new_hours % 24
        return Time(new_hours, new_minutes, new_rollover)


class Order:
    def __init__(self, order_id: str, eastbound: bool, times: list[Optional[Time]]):
        self.order_id = order_id
        self.eastbound = eastbound
        self.times = times

    def get_absolute_idx(self, rel_idx):
        return rel_idx if self.eastbound else -1 - rel_idx

    def get_spawn_place_and_time(self) -> (str, Time):
        for idx in range(len(self.times)):
            if self.times[idx] is not None:
                return self.order_id, self.times[idx]
        raise ValueError

    def __repr__(self):
        return f"Schedule(number={self.order_id},eastbound={self.eastbound},times={self.times})"


class Storage:
    def __init__(self):
        self._count = {}

    def store(self, name: str):
        if name not in self._count.keys():
            self._count[name] = 0
        self._count[name] += 1

    def withdraw(self, name: str):
        if self.has_any(name):
            self._count[name] -= 1
        else:
            self._count[name] = 0

    def has_any(self, name: str) -> bool:
        if name not in self._count.keys():
            return False
        return self._count[name] > 0

    def get_count(self, name: str) -> int:
        if name not in self._count.keys():
            return 0
        return self._count[name]

    def get_all_count(self) -> int:
        return sum([v for _, v in self._count.items()])

    def reset(self):
        self._count = {}


class Station:
    ABOVE = 0
    BELOW = 1
    LEFT = 2
    RIGHT = 3

    def __init__(self, name: str, x: int, y: int, name_orientation: int, storage=None, special=False):
        self.name = name
        self.x = x
        self.y = y
        self.name_orientation = name_orientation
        self.storage = storage
        self.special = special

    def withdraw_train(self, route_name: str):
        if self.storage is not None:
            self.storage.withdraw(route_name)

    def store_train(self, route_name: str):
        if self.storage is not None:
            self.storage.store(route_name)

    def get_count(self, route_name: str) -> int:
        if self.storage is not None:
            return self.storage.get_count(route_name)
        return 0

    def get_all_count(self) -> int:
        if self.storage is not None:
            return self.storage.get_all_count()
        return 0


class Route:
    def __init__(self, name: str, color: (int, int, int), stations: list[Station]):
        self.name = name
        self.color = color
        self.stations = stations

    def color_as_string(self) -> str:
        (r, g, b) = self.color
        return f"#{r:02x}{g:02x}{b:02x}"

    def color_as_tuple(self) -> (int, int, int):
        return self.color

    def __getitem__(self, item):
        return self.stations[item]

    def __len__(self):
        return len(self.stations)


class Schedule:
    def __init__(self, schedules: list[Order]):
        self.schedules = schedules
        self.route_map = {order.order_id: order for order in schedules}

    def __add__(self, other):
        return Schedule(self.schedules + other.schedules)

    def get_spawn_order(self) -> list[(str, Time)]:
        # [(id, time)]
        raw = [s.get_spawn_place_and_time() for s in self.schedules]
        return sorted(raw, key= lambda line: line[1])

    def get_order(self, train_number: str) -> Order:
        return self.route_map[train_number]

    def get_time_of_last_stop(self) -> Time:
        max_time = Time(0, 0, False)
        for schedule in self.schedules:
            for time in schedule.times:
                if time is not None:
                    max_time = max(max_time, time)
        return max_time


class Train:
    def __init__(self, order: Order, system: str):
        self.order = order
        self.current_leg = 0
        self.leg_frac = 0.0
        self.system = system

    def advance_to_time(self, time: Time):
        # Find the time in the schedule
        last_non_none_idx = None
        for idx, time_to_check in enumerate(self.order.times):
            if time_to_check is None:
                continue
            else:
                last_non_none_idx = idx

            if time_to_check > time:
                self.set_current_leg(idx - 1, time)
                return
            elif time_to_check == time:
                self.set_current_leg(idx, time)
                return
        # Went out of bounds, so it stays at the end perpetually until claimed.
        self.set_current_leg(last_non_none_idx, time)

    def set_current_leg(self, idx: int, current_time: Time):
        self.current_leg = self.order.get_absolute_idx(idx)
        # Calculate fraction of the route beyond the current leg.
        time_at_start_of_leg = self.order.times[idx]
        if idx + 1 >= len(self.order.times) or self.order.times[idx+1] is None:
            self.leg_frac = 1.0
            return
        time_at_end_of_leg = self.order.times[idx + 1]
        elapsed_minutes = current_time.as_minutes() - time_at_start_of_leg.as_minutes()
        total_minutes = time_at_end_of_leg.as_minutes() - time_at_start_of_leg.as_minutes()
        self.leg_frac = elapsed_minutes / total_minutes

    def is_complete(self):
        return self.leg_frac == 1.0

    def is_between_stops(self):
        return 0.0 < self.leg_frac < 1.0