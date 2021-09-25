from obspython import obs_properties_create
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

window: QLabel


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


def script_update(settings: "obs_data_t *") -> None:
    global window
    window.hide()
    window.show()


def script_unload() -> None:
    global window
    window.destroy()
