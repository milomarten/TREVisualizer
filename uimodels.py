import tkinter as tk
from typing import Optional

from PIL import Image, ImageDraw
from PIL.ImageFont import truetype

from models import Train, Storage, Station, Route

station_radius = 10
train_width = 10


class UITrain(Train):
    ui = None


class UIStorage(Storage):
    def __init__(self, station_idx: int):
        super().__init__()
        self.ui = None
        self.station_idx = station_idx



def get_x_y_anchor_for_station_names(station: Station) -> (int, int, str):
    if station.name_orientation == Station.RIGHT:
        return station.x + station_radius + 10, station.y, tk.W
    elif station.name_orientation == Station.LEFT:
        return station.x - station_radius - 10, station.y, tk.E
    elif station.name_orientation == Station.ABOVE:
        return station.x, station.y - station_radius - 10, tk.CENTER
    else:
        return station.x, station.y + station_radius + 10, tk.CENTER


anchor_map = {
    tk.CENTER: "mm",
    tk.W: "lm",
    tk.E: "rm"
}

class CanvasWrapper:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.font = truetype(font="segoeui.ttf", size=9)
        self.images: list[Image] = []
        self.current_image: Optional[Image] = None
        self.current_frame: Optional[ImageDraw] = None
        self.backgrounds = []

    def pack(self):
        self.canvas.pack()

    def delete(self, tag):
        self.canvas.delete(tag)

    def create_text(self, x, y, text='', anchor=tk.CENTER) -> int:
        self.current_frame.text((x, y), text, anchor=anchor_map[anchor], fill=(0,0,0), font=self.font)
        return self.canvas.create_text(x, y, text=text, anchor=anchor)

    def reset(self):
        self.images = []
        self.current_image = None
        self.current_frame = None
        self.start_of_frame()

    def start_of_frame(self):
        self.current_image = Image.new("RGB", (850, 400), (255, 255, 255))
        self.current_frame = ImageDraw.Draw(self.current_image)

        for callback in self.backgrounds:
            callback()

    def end_of_frame(self):
        self.images.append(self.current_image)
        self.current_image = None
        self.current_frame = None

    def draw_route(self, route: Route):
        for idx in range(len(route) - 1):
            start = route[idx]
            end = route[idx + 1]
            self.canvas.create_line(start.x, start.y, end.x, end.y, fill=route.color_as_string())

        def draw_route_pil():
            for idx in range(len(route) - 1):
                start = route[idx]
                end = route[idx + 1]
                self.current_frame.line([(start.x, start.y), (end.x, end.y)], fill=route.color_as_tuple(), width=1)
        self.backgrounds.append(draw_route_pil)

    def draw_station(self, station: Station):
        self.canvas.create_oval(station.x - station_radius,
                                station.y - station_radius,
                                station.x + station_radius,
                                station.y + station_radius,
                                fill='#FF0' if station.special else "#FFF",
                                width=3
                                )
        (x, y, anchor) = get_x_y_anchor_for_station_names(station)
        self.canvas.create_text(x, y, text=station.name, anchor=anchor)

        def draw_station_pil():
            self.current_frame.ellipse([(station.x - station_radius, station.y - station_radius),
                                        (station.x + station_radius, station.y + station_radius)],
                                        outline=(0, 0, 0),
                                        fill='#FF0' if station.special else "#FFF",
                                        width=3
                                       )
            self.current_frame.text((x, y), station.name, anchor=anchor_map[anchor], fill=(0,0,0), font=self.font)
        self.backgrounds.append(draw_station_pil)

    def draw_storage(self, point: Station) -> int:
        x0 = point.x - train_width
        y0 = point.y - train_width
        x1 = point.x + train_width
        y1 = point.y + train_width
        color = "#F0F"
        count = point.get_all_count()
        if count == 2:
            color = "#909"
        elif count > 2:
            color = "#505"

        self.current_frame.rectangle([(x0, y0), (x1, y1)],
                                     fill=color,
                                     outline=(0, 0, 0),
                                     width=1
                                     )

        return self.canvas.create_rectangle(x0, y0, x1, y1, fill=color)

    def draw_train(self, x: int, y: int, train: UITrain) -> int:
        x0 = x - train_width
        y0 = y - train_width
        x1 = x + train_width
        y1 = y + train_width

        self.current_frame.rectangle([(x0, y0), (x1, y1)],
                                     fill=(255, 0, 0) if train.system == "TRE" else (0, 0, 255),
                                     outline=(0, 0, 0),
                                     width=1
                                     )

        return self.canvas.create_rectangle(
            x0, y0, x1, y1,
            fill="#F00" if train.system == "TRE" else "#00F"
        )

    def after(self, millis, action):
        self.canvas.after(millis, action)

    def save_gif(self, filename):
        self.images[0].save(filename, save_all=True, append_images=self.images[1:])