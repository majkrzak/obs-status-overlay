from obspython import (
    obs_properties_create,
    obs_properties_add_bool,
    obs_properties_add_font,
    obs_properties_add_color,
    obs_properties_add_group,
    OBS_GROUP_NORMAL,
    OBS_GROUP_CHECKABLE,
    obs_data_get_bool,
    obs_data_get_string,
    obs_data_get_int,
    obs_data_get_obj,
    obs_data_get_json,
    obs_data_set_default_int,
    obs_data_set_default_bool,
    obs_data_set_default_obj,
    obs_data_create_from_json,
    timer_add,
    timer_remove,
    obs_frontend_recording_active,
    obs_frontend_streaming_active,
    obs_frontend_get_streaming_output,
    obs_output_get_total_frames,
    obs_output_get_frames_dropped,
    obs_get_frame_interval_ns,
    obs_source_get_name,
    obs_frontend_get_current_scene,
)
from math import ceil
from json import dumps, loads
from types import SimpleNamespace
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase


class Config:

    schema: list

    def __init__(self, schema: list):
        self.schema = schema

    def get_properties(self) -> "obs_properties_t *":
        props = obs_properties_create()
        for group in self.schema:
            group_props = obs_properties_create()
            for property in group.children:
                {
                    "bool": obs_properties_add_bool,
                    "color": obs_properties_add_color,
                    "font": obs_properties_add_font,
                }[property.kind](group_props, property.code, property.name)
            obs_properties_add_group(
                props,
                group.code,
                group.name,
                {"bool": OBS_GROUP_CHECKABLE, None: OBS_GROUP_NORMAL}[group.kind],
                group_props,
            )
        return props

    def set_defaults(self, settings: "obs_data_t *") -> None:
        for group in self.schema:
            if group.kind == "bool":
                obs_data_set_default_bool(settings, group.code, group.default)
            for property in group.children:
                if property.kind == "bool":
                    obs_data_set_default_bool(settings, property.code, property.default)
                elif property.kind == "color":
                    obs_data_set_default_int(
                        settings,
                        property.code,
                        int.from_bytes(property.default, byteorder="little"),
                    )
                elif property.kind == "font":
                    obs_data_set_default_obj(
                        settings,
                        property.code,
                        obs_data_create_from_json(dumps(property.default.__dict__)),
                    )
                else:
                    raise NotImplementedError()

    def load(self, settings: "obs_data_t *") -> None:
        for group in self.schema:
            if group.kind == "bool":
                setattr(self, group.code, obs_data_get_bool(settings, group.code))
            for property in group.children:
                if property.kind == "bool":
                    setattr(
                        self, property.code, obs_data_get_bool(settings, property.code)
                    )
                elif property.kind == "color":
                    setattr(
                        self,
                        property.code,
                        tuple(
                            obs_data_get_int(settings, property.code).to_bytes(
                                4, byteorder="little"
                            )
                        ),
                    )
                elif property.kind == "font":
                    setattr(
                        self,
                        property.code,
                        loads(
                            obs_data_get_json(
                                obs_data_get_obj(settings, property.code)
                            ),
                            object_hook=lambda d: SimpleNamespace(**d),
                        ),
                    )
                else:
                    raise NotImplementedError()


window: QLabel
config: Config = Config(
    [
        SimpleNamespace(
            code="show",
            name="Show",
            kind="bool",
            default=True,
            children=[
                SimpleNamespace(
                    code="show_status",
                    name="Show Status",
                    kind="bool",
                    default=True,
                ),
                SimpleNamespace(
                    code="show_timer",
                    name="Show Timer",
                    kind="bool",
                    default=True,
                ),
                SimpleNamespace(
                    code="show_scene",
                    name="Show Scene",
                    kind="bool",
                    default=True,
                ),
                SimpleNamespace(
                    code="show_dropped_frames",
                    name="Show Dropped Frames",
                    kind="bool",
                    default=True,
                ),
            ],
        ),
        SimpleNamespace(
            code="style",
            name="Style",
            kind=None,
            children=[
                SimpleNamespace(
                    code="color",
                    name="Color",
                    kind="color",
                    default=(255, 0, 0, 255),
                ),
                SimpleNamespace(
                    code="font",
                    name="Font",
                    kind="font",
                    default=SimpleNamespace(
                        face=QFontDatabase.systemFont(
                            QFontDatabase.SystemFont.FixedFont
                        ).family(),
                        size=6,
                        flags=0,
                        style="Regular",
                    ),
                ),
            ],
        ),
    ]
)


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


def get_dropped_frames() -> str:
    streaming_output = obs_frontend_get_streaming_output()
    total_frames = obs_output_get_total_frames(streaming_output)
    dropped_frames = obs_output_get_frames_dropped(streaming_output)
    dropped_ratio = dropped_frames / total_frames if total_frames else 0

    return f"{dropped_frames}({dropped_ratio*100:.2f}%)"


def get_current_scene() -> str:
    return obs_source_get_name(obs_frontend_get_current_scene())


def update() -> None:
    window.setText(
        " ".join(
            filter(
                lambda x: x,
                [
                    get_status() if config.show_status else None,
                    get_live_timer() if config.show_timer else None,
                    get_dropped_frames() if config.show_dropped_frames else None,
                    get_current_scene() if config.show_scene else None,
                ],
            )
        )
    )
    window.adjustSize()


def script_description() -> str:
    return '<a href="https://github.com/majkrzak/obs-status-overlay"><tt>majkrzak/obs-status-overlay</tt></a>'


def script_properties() -> "obs_properties_t *":
    return config.get_properties()


def script_defaults(settings: "obs_data_t *") -> None:
    config.set_defaults(settings)


def script_load(settings: "obs_data_t *") -> None:
    global window
    window = QLabel()

    window.setWindowFlags(
        Qt.WindowType.Window
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.BypassWindowManagerHint
        | Qt.WindowType.WindowDoesNotAcceptFocus
        | Qt.WindowType.WindowTransparentForInput
    )

    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    window.show()

    timer_add(update, 100)


def script_update(settings: "obs_data_t *") -> None:
    config.load(settings)

    window.setStyleSheet(
        "".join(
            [
                f"color: rgb({config.color[0]},{config.color[1]},{config.color[2]});",
                f"font-family: {config.font.face};",
                f"font-size: {config.font.size}pt;",
            ]
        )
    )

    if config.show:
        window.show()
    else:
        window.hide()


def script_unload() -> None:
    timer_remove(update)
    window.destroy()
