from obspython import (
    obs_properties_create,
    obs_properties_add_bool,
    obs_properties_add_font,
    obs_properties_add_color,
    obs_data_get_string,
    obs_data_get_int,
    obs_data_get_obj,
    obs_data_get_json,
    timer_add,
    timer_remove,
    obs_frontend_recording_active,
    obs_frontend_streaming_active,
    obs_frontend_get_streaming_output,
    obs_output_get_total_frames,
    obs_get_frame_interval_ns,
    obs_source_get_name,
    obs_frontend_get_current_scene,
)
from math import ceil
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

window: QLabel


def set_font(font: "obs_data_t *") -> None:
    global window
    window.setFont(
        QFont(
            obs_data_get_string(font, "face"),
            obs_data_get_int(font, "size"),
        )
        if font
        else QFont()
    )


def set_color(r: int, g: int, b: int) -> None:
    global window
    window.setStyleSheet(f"color : rgb({r},{g},{b});")


def get_status() -> str:
    return {
        (False, False): "IDLE",
        (False, True): "AIR",
        (True, False): "REC",
        (True, True): "REC&AIR",
    }[(obs_frontend_recording_active(), obs_frontend_streaming_active())]


def get_live_timer() -> str:
    t = (
        ceil(
            obs_output_get_total_frames(obs_frontend_get_streaming_output())
            * obs_get_frame_interval_ns()
            / 1000
            / 1000
            / 1000
        )
        if obs_frontend_streaming_active()
        else 0
    )
    return f"{t//60//60:02d}:{t//60%60:02d}:{t%60:02d}"


def get_current_scene() -> str:
    return obs_source_get_name(obs_frontend_get_current_scene())


def update() -> None:
    global window
    window.setText(
        " ".join(
            [
                get_status(),
                get_live_timer(),
                get_current_scene(),
            ]
        )
    )
    window.adjustSize()


def script_description() -> str:
    return '<a href="https://github.com/majkrzak/obs-status-overlay"><tt>majkrzak/obs-status-overlay</tt></a>'


def script_properties() -> "obs_properties_t *":
    props = obs_properties_create()
    obs_properties_add_font(props, "font", "Font")
    obs_properties_add_color(props, "color", "Color")
    return props


def script_defaults(settings: "obs_data_t *") -> None:
    pass


def script_load(settings: "obs_data_t *") -> None:
    global window
    window = QLabel()

    window.setWindowFlags(
        Qt.Window
        | Qt.WindowStaysOnTopHint
        | Qt.FramelessWindowHint
        | Qt.BypassWindowManagerHint
        | Qt.WindowDoesNotAcceptFocus
        | Qt.WindowTransparentForInput
    )

    window.setAttribute(Qt.WA_TranslucentBackground)

    window.show()

    timer_add(update, 100)


def script_update(settings: "obs_data_t *") -> None:
    set_font(obs_data_get_obj(settings, "font"))
    set_color(*obs_data_get_int(settings, "color").to_bytes(4, byteorder="little")[0:3])


def script_unload() -> None:
    global window
    timer_remove(update)
    window.destroy()
