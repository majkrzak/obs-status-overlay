from obspython import (
    obs_properties_create,
    obs_properties_add_bool,
    timer_add,
    timer_remove,
    obs_frontend_recording_active,
    obs_frontend_streaming_active,
)
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

window: QLabel


def get_status() -> str:
    return {
        (False, False): "IDLE",
        (False, True): "AIR",
        (True, False): "REC",
        (True, True): "REC&AIR",
    }[(obs_frontend_recording_active(), obs_frontend_streaming_active())]


def update() -> None:
    global window
    window.setText(f"{get_status()}")
    window.adjustSize()


def script_description() -> str:
    return '<a href="https://github.com/majkrzak/obs-status-overlay"><tt>majkrzak/obs-status-overlay</tt></a>'


def script_properties() -> "obs_properties_t *":
    props = obs_properties_create()
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

    timer_add(update, 100)


def script_update(settings: "obs_data_t *") -> None:
    global window
    window.hide()
    window.show()


def script_unload() -> None:
    global window
    timer_remove(update)
    window.destroy()
