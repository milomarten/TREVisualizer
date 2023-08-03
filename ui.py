import tkinter as tk
import tkinter.messagebox as mb
from typing import Optional

import beep_boop
from models import Schedule, Train, Station, Time, Route, Order
from script import parse_schedules_from_csv, find_orders_for_time
from uimodels import UITrain, UIStorage, CanvasWrapper
from beep_boop import play_major, play_minor

time_step = 100

fw_terminal = UIStorage(0)
dal_terminal = UIStorage(9)
irving_yard = UIStorage(10)
airport_terminal = UIStorage(17)
texrail_yard = UIStorage(18)

all_stations = [
    # TRE Stations and yards
    Station("Fort Worth T&P Station", 50, 350, Station.RIGHT, storage=fw_terminal),
    Station("Fort Worth Central Station", 50, 325, Station.RIGHT),
    Station("Richland Hills", 150, 260, Station.ABOVE),
    Station("Bell", 250, 200, Station.BELOW),
    Station("CentrePort/ DFW Airport", 350, 200, Station.ABOVE, storage=irving_yard, special=True),
    Station("West Irving", 450, 200, Station.BELOW, storage=irving_yard),
    Station("Downtown Irving/ Heritage Crossing", 550, 200, Station.ABOVE),
    Station("Medical/ Market Center", 650, 200, Station.RIGHT),
    Station("Victory Station @ AA Center", 725, 275, Station.LEFT),
    Station("EBJ Union Station", 800, 350, Station.LEFT, storage=dal_terminal),
    Station("TRE Yard", 400, 250, Station.BELOW, storage=irving_yard),
    # TEXRail Stations and yards
    Station("North Side", 50, 200, Station.RIGHT, storage=texrail_yard),
    Station("Mercantile Center", 100, 150, Station.RIGHT, storage=texrail_yard),
    Station("Iron Horse", 150, 100, Station.LEFT),
    Station("Smithfield", 200, 50, Station.LEFT),
    Station("Grapevine", 300, 50, Station.BELOW),
    Station("DFW Airport North", 350, 50, Station.RIGHT),
    Station("DFW Airport Terminal B", 350, 100, Station.RIGHT, storage=airport_terminal),
    Station("TEXRail Yard", 125, 175, Station.RIGHT, storage=texrail_yard)
]

all_yards = [
    fw_terminal, dal_terminal, irving_yard, airport_terminal, texrail_yard
]

tre = Route("TRE", (15, 56, 144), all_stations[0:10])
texrail = Route("TEXRail", (0, 0, 0), all_stations[0:2] + all_stations[11:18])

def lerp(p1, p2, t):
    return ((p2 - p1) * t) + p1


class CanvasManager:
    def __init__(self, c: CanvasWrapper):
        self.canvas = c

    def delete_from_ui(self, tag):
        if tag is not None:
            self.canvas.delete(tag)


class Simulation(CanvasManager):
    def __init__(self, c: CanvasWrapper, schedule: Schedule, route: Route):
        super().__init__(c)
        self.schedule = schedule
        self.canvas = c
        self.route = route
        # The order that trains are spawned in, sorted by time.
        self.spawn_order = schedule.get_spawn_order()
        # UI elements
        self.trains: list[UITrain] = []

    def get_summary(self):
        in_motion = len(self.trains)
        if self.route.name == "TRE":
            in_idle = fw_terminal.get_count(self.route.name) + dal_terminal.get_count(self.route.name)
        else:
            in_idle = fw_terminal.get_count(self.route.name) + airport_terminal.get_count(self.route.name)
        return f"{in_motion + in_idle} train(s) running ({in_idle} waiting at terminal)"

    def get_x_y_for_train(self, t: Train):
        leg = t.current_leg
        if not t.is_between_stops():
            return self.route[leg].x, self.route[leg].y
        else:
            frac = t.leg_frac
            offset = 1 if t.order.eastbound else -1
            next_leg = leg + offset
            return lerp(self.route[leg].x, self.route[next_leg].x, frac), lerp(self.route[leg].y, self.route[next_leg].y, frac)

    def draw_train(self, train: UITrain):
        (x, y) = self.get_x_y_for_train(train)
        self.delete_from_ui(train.ui)
        train.ui = self.canvas.draw_train(x, y, train)

    def play_train_beeps(self):
        for train in self.trains:
            if not train.is_between_stops():
                if self.route.name == "TRE":
                    play_major(train.current_leg)
                else:
                    play_minor(train.current_leg)

    def reset(self):
        for train in self.trains:
            self.canvas.delete(train.ui)
        self.trains = []

    def update(self, time: Time):
        # Move all trains along the route
        for train in self.trains:
            train.advance_to_time(time)
            self.draw_train(train)

        # Create new trains
        new_orders = [self.schedule.get_order(train_id) for train_id in find_orders_for_time(self.spawn_order, time)]
        for order in new_orders:
            train = UITrain(order, self.route.name)
            train.advance_to_time(time)
            self.trains.append(train)
            self.draw_train(train)
            self.route[train.current_leg].withdraw_train(self.route.name)

        # Delete all trains that have finished their route
        cleaned_trains = []
        for t in self.trains:
            if t.is_complete():
                self.canvas.delete(t.ui)
                self.route[t.current_leg].store_train(self.route.name)
            else:
                cleaned_trains.append(t)
        self.trains = cleaned_trains

        self.play_train_beeps()


class GlobalSimulation(CanvasManager):
    def __init__(self, c: CanvasWrapper, children: list[Simulation]):
        super().__init__(c)
        self.canvas = c
        self.children = children
        # Current time of the simulation
        self.start_time = self.time = min([s.spawn_order[0][1] for s in children if len(s.spawn_order) > 0])
        # End time of the simulation
        self.end_time = max([s.schedule.get_time_of_last_stop() for s in children])

        self.summary_ui: list[Optional[int]] = [None for _ in children]
        self.clock_ui = None
        self.paused = False

    def update_clock(self):
        clock_text = f"{self.time.hour:02}:{self.time.minute:02}"
        self.delete_from_ui(self.clock_ui)
        self.clock_ui = self.canvas.create_text(10, 10, text=clock_text, anchor=tk.W)

    def update_storage(self):
        for yard in all_yards:
            self.delete_from_ui(yard.ui)
            if yard.get_all_count() > 0:
                yard.ui = self.canvas.draw_storage(all_stations[yard.station_idx])

    def update_summaries(self):
        for idx, child in enumerate(self.children):
            self.delete_from_ui(self.summary_ui[idx])
            text = f"{child.route.name}: {child.get_summary()}"
            self.summary_ui[idx] = self.canvas.create_text(840, 10 + (idx * 15), text=text, anchor=tk.E)

    def update(self):
        self.canvas.start_of_frame()
        self.update_clock()
        self.update_storage()
        self.update_summaries()
        for child in self.children:
            child.update(self.time)
        self.time += 1
        self.canvas.end_of_frame()

        if not self.paused:
            if self.time <= self.end_time:
                self.canvas.after(time_step, self.update)
            else:
                self.canvas.after(time_step, self.finalize)

    def finalize(self):
        self.canvas.start_of_frame()
        self.update_summaries()
        self.canvas.end_of_frame()
        if mb.askokcancel(title="Save?", message="Save output as GIF?"):
            self.canvas.save_gif("output.gif")

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.update()

    def reset(self):
        self.time = self.start_time
        self.canvas.reset()
        [s.reset() for s in self.children]
        self.update_summaries()
        self.update_clock()
        [yard.reset() for yard in all_yards]
        self.update_storage()


tre_eastbound = parse_schedules_from_csv("schedules/eastbound_weekday.csv")
tre_westbound = parse_schedules_from_csv("schedules/westbound_weekday.csv")
tre_schedule = tre_eastbound + tre_westbound

texrail_eastbound = parse_schedules_from_csv("schedules/texrail_eastbound.csv")
texrail_westbound = parse_schedules_from_csv("schedules/texrail_westbound.csv")
texrail_schedule = texrail_eastbound + texrail_westbound

print("Parsing schedules complete")

window = tk.Tk()
window.title("Fort Worth Simulator")
canvas = CanvasWrapper(tk.Canvas(width=850, height=400))

canvas.draw_route(texrail)
canvas.draw_route(tre)
# Station circles
for station in all_stations:
    canvas.draw_station(station)

tre_simulation = Simulation(canvas, tre_schedule, tre)
texrail_simulation = Simulation(canvas, texrail_schedule, texrail)
global_sim = GlobalSimulation(canvas, [tre_simulation, texrail_simulation])

canvas.canvas.grid(column=0, row=0, columnspan=5)

# Blob of button logic. It could be a lot better...
button_holder = {}

def start_sim():
    window.after(0, global_sim.update)
    button_holder['start']['state'] = 'disabled'
    button_holder['pause']['state'] = 'active'
    button_holder['reset']['state'] = 'active'

def pause_resume_sim():
    if global_sim.paused:
        global_sim.resume()
        button_holder['pause'].configure(text="Pause")
        button_holder['add_minute']['state'] = 'disabled'
    else:
        global_sim.pause()
        button_holder['pause'].configure(text="Resume")
        button_holder['add_minute']['state'] = 'active'

def stop_start_music():
    beep_boop.enabled = not beep_boop.enabled
    button_holder['music'].configure(text="Turn Music OFF" if beep_boop.enabled else "Turn Music ON")

def plus_one_minute():
    global_sim.update()

def reset():
    global_sim.reset()


btn = tk.Button(text="Start!", command=start_sim)
btn.grid(column=0, row=1)
button_holder['start'] = btn

btn = tk.Button(text="Pause", command=pause_resume_sim)
btn.grid(column=1, row=1)
button_holder['pause'] = btn
btn["state"] = "disabled"

btn = tk.Button(text="+1 Minute", command=plus_one_minute)
btn.grid(column=2, row=1)
button_holder['add_minute'] = btn
btn["state"] = "disabled"

btn = tk.Button(text="Turn Music OFF", command=stop_start_music)
btn.grid(column=3, row=1)
button_holder['music'] = btn

btn = tk.Button(text="Reset", command=reset)
btn.grid(column=4, row=1)
button_holder['reset'] = btn
btn["state"] = "disabled"

window.mainloop()
