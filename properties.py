import bpy

from . import isolate_selection as isolate

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    PointerProperty,
    EnumProperty,
    CollectionProperty,
)

from bpy.utils import previews

from math import (
    radians,
    degrees,
)

import os
import glob
import re

# VARIABLES

invalid_chars = '[\\\/\:\*\?"\<\>\|]'

# Errors

marker_name_error = (
    "A marker name can't contain any of these characters: \n" + '\\ / : * ? " < > |'
)
not_in_view_layer_error = "The %s is not in the View Layer"
no_selected_error = "No %s selected"
project_not_saved_error = "The project is not saved"
marker_name_h_missing_error = "Use %H% in Marker name or disable Horizontal Axis"
marker_name_v_missing_error = "Use %V% in Marker name or disable Vertical Axis"
path_empty_error = "Select a path to save the frames"
no_active_camera_error = "There is no active camera"
markers_names_named_error = "Not all frames within the render range have a named marker"

# Messages
render_started_msg = "360 RENDERER: render started\n"
render_finished_msg = "360 RENDERER: render finished\n"
frames_renderer_msg = "360 RENDERER: %s/%s frames rendered\n"

# Icons
icons = None


def register_icons():

    global icons

    icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    icon_names = os.listdir(icons_dir)

    for icon in icon_names:
        icons.load(icon[:-4], os.path.join(icons_dir, icon), "IMAGE")


def unregister_icons():

    global icons

    if icons:
        bpy.utils.previews.remove(icons)


# FUNCTIONS


def validate_file_name(name):

    global invalid_chars
    return not re.search(invalid_chars, name)


def is_in_view_layer(self, object):
    return object in set(bpy.context.scene.objects)


# CLASSES


class Obj(bpy.types.PropertyGroup):
    object: PointerProperty(type=bpy.types.Object)


# PROPERTIES


class MyProperties(bpy.types.PropertyGroup):

    # GETTER/SETTER

    # Horizontal Axis

    # Turn Around

    def get_x_steps(self):
        return self.get("x_steps", 360)

    def set_x_steps(self, value):
        self["x_steps"] = value
        self["x_clamped_angle"] = radians(360 / value)

    def get_x_clamped_angle(self):
        return self.get("x_clamped_angle", radians(1))

    def set_x_clamped_angle(self, value):
        self["x_steps"] = round(360 / degrees(value))
        self["x_clamped_angle"] = radians(360 / self["x_steps"])

    # Custom

    def get_x_angle(self):
        return self.get("x_angle", radians(1))

    def set_x_angle(self, value):

        left_steps = self.get("left_steps", 0)
        right_steps = self.get("right_steps", 0)

        # Change angle
        self["x_angle"] = value

        # Change max steps
        angle = round(degrees(self["x_angle"]), 4)
        self["x_steps_max"] = 360 // angle
        if 360 % angle == 0:
            self["x_steps_max"] -= 1

        # Change right/left steps
        x_steps_total = right_steps + left_steps

        if x_steps_total > self["x_steps_max"]:

            # Distribute the max steps proportionally (losing the decimals == 1 unit)
            factor = self["x_steps_max"] / x_steps_total

            left_steps_new = int(left_steps * factor)
            right_steps_new = int(right_steps * factor)

            # Distribute the unit
            x_steps_total = left_steps_new + right_steps_new

            if x_steps_total < self["x_steps_max"]:

                if right_steps >= left_steps:
                    right_steps_new += 1
                else:
                    left_steps_new += 1

            self["left_steps"] = left_steps_new
            self["right_steps"] = right_steps_new

    def get_right_steps(self):
        return self.get("right_steps", 0)

    def set_right_steps(self, value):

        left_steps = self.get("left_steps", 0)
        x_steps_max = self.get("x_steps_max", 359)

        # Clamp value to max steps
        value = max(0, min(value, x_steps_max))

        # Change right steps
        self["right_steps"] = value

        # Clamp left steps with the rest
        self["left_steps"] = max(0, min(left_steps, x_steps_max - self["right_steps"]))

    def get_left_steps(self):
        return self.get("left_steps", 0)

    def set_left_steps(self, value):

        right_steps = self.get("right_steps", 0)
        x_steps_max = self.get("x_steps_max", 359)

        # Clamp value to max steps
        value = max(0, min(value, x_steps_max))

        # Change left steps
        self["left_steps"] = value

        # Clamp right steps with the rest
        self["right_steps"] = max(0, min(right_steps, x_steps_max - self["left_steps"]))

    # Vertical Axis

    # Turn Around

    def get_y_steps(self):
        return self.get("y_steps", 360)

    def set_y_steps(self, value):
        self["y_steps"] = value
        self["y_clamped_angle"] = radians(360 / value)

    def get_y_clamped_angle(self):
        return self.get("y_clamped_angle", radians(1))

    def set_y_clamped_angle(self, value):
        self["y_steps"] = round(360 / degrees(value))
        self["y_clamped_angle"] = radians(360 / self["y_steps"])

    # Custom

    def get_y_angle(self):
        return self.get("y_angle", radians(1))

    def set_y_angle(self, value):

        up_steps = self.get("up_steps", 0)
        down_steps = self.get("down_steps", 0)

        # Change angle
        self["y_angle"] = value

        # Change max steps
        angle = round(degrees(self["y_angle"]), 4)
        self["y_steps_max"] = 360 // angle
        if 360 % angle == 0:
            self["y_steps_max"] -= 1

        # Change up/down steps
        y_steps_total = up_steps + down_steps

        if y_steps_total > self["y_steps_max"]:

            # Distribute the max steps proportionally (losing the decimals == 1 unit)
            factor = self["y_steps_max"] / y_steps_total

            down_steps_new = int(down_steps * factor)
            up_steps_new = int(up_steps * factor)

            # Distribute the unit
            y_steps_total = down_steps_new + up_steps_new

            if y_steps_total < self["y_steps_max"]:

                if up_steps >= down_steps:
                    up_steps_new += 1
                else:
                    down_steps_new += 1

            self["down_steps"] = down_steps_new
            self["up_steps"] = up_steps_new

    def get_up_steps(self):
        return self.get("up_steps", 0)

    def set_up_steps(self, value):

        down_steps = self.get("down_steps", 0)
        y_steps_max = self.get("y_steps_max", 359)

        # Clamp value to max steps
        value = max(0, min(value, y_steps_max))

        # Change up steps
        self["up_steps"] = value

        # Clamp down steps with the rest
        self["down_steps"] = max(0, min(down_steps, y_steps_max - self["up_steps"]))

    def get_down_steps(self):
        return self.get("down_steps", 0)

    def set_down_steps(self, value):

        up_steps = self.get("up_steps", 0)
        y_steps_max = self.get("y_steps_max", 359)

        # Clamp value to max steps
        value = max(0, min(value, y_steps_max))

        # Change left steps
        self["down_steps"] = value

        # Clamp right steps with the rest
        self["up_steps"] = max(0, min(up_steps, y_steps_max - self["down_steps"]))

    # Create keyframes

    def get_marker_name(self):
        return self.get("marker_name", "V%V%H%H%")

    def set_marker_name(self, value):

        global marker_name
        global marker_name_preview

        if not value:
            marker_name = "No marker name"
            marker_name_preview = ""
        else:
            marker_name = value
            marker_name_preview = value
            marker_name_preview = marker_name_preview.replace("%V%", "1")
            marker_name_preview = marker_name_preview.replace("%H%", "0")

    def get_marker_name_preview(self):
        return self.get("marker_name_preview", "V1H0")

    def get_views_count(self):

        x = 0
        y = 0

        x_axis = self.get("x_axis", False)
        y_axis = self.get("y_axis", False)

        # Set x and y
        if x_axis:
            if self.get("x_turnaround", False):
                x = self.get("x_steps", 360)
            else:
                x = 1 + self.get("right_steps", 0) + self.get("left_steps", 0)
        else:
            x = 1

        if y_axis:
            if self.get("y_turnaround", False):
                y = self.get("y_steps", 360)
            else:
                y = 1 + self.get("up_steps", 0) + self.get("down_steps", 0)
        else:
            y = 1

        # Calculate views count
        if not x_axis and not y_axis:
            return 1
        elif x_axis and y_axis:
            return x * y
        elif x_axis:
            return x
        else:
            return y

    def get_frames_count(self):

        scene = bpy.context.scene
        return 1 + scene.frame_end - scene.frame_start

    def get_abs_path(self):
        return self.get("path", "")

    def set_abs_path(self, value):
        self["path"] = bpy.path.abspath(value)

    # PROPERTY DEFINITIONS

    # Setup

    controller: PointerProperty(
        type=bpy.types.Object,
        name="",
        description="Controller to rotate",
        poll=is_in_view_layer,
    )

    obj: PointerProperty(
        type=bpy.types.Object,
        name="",
        description="Object to align",
        poll=is_in_view_layer,
    )

    controller_to_obj: BoolProperty(
        name="",
        description="Alignment direction",
        default=True,
    )

    # Keyframe Assistant

    # X Turnaround

    x_axis: BoolProperty(
        name="",
        default=False,
    )

    x_rotation_axis: EnumProperty(
        items=[
            ("X", "X", ""),
            ("Y", "Y", ""),
            ("Z", "Z", ""),
            ("-X", "-X", ""),
            ("-Y", "-Y", ""),
            ("-Z", "-Z", ""),
        ],
        name="Axis",
        description="Rotation Axis (default: Z)",
        default="Z",
    )

    x_turnaround: BoolProperty(
        name="",
        default=False,
    )
    x_steps: IntProperty(
        name="",
        min=1,
        max=360,
        default=1,
        get=get_x_steps,
        set=set_x_steps,
    )

    x_steps_max: IntProperty()

    # Y Turnaround

    y_axis: BoolProperty(
        name="",
        default=False,
    )

    y_rotation_axis: EnumProperty(
        items=[
            ("X", "X", ""),
            ("Y", "Y", ""),
            ("Z", "Z", ""),
            ("-X", "-X", ""),
            ("-Y", "-Y", ""),
            ("-Z", "-Z", ""),
        ],
        name="Axis",
        description="Rotation Axis (default: X)",
        default="X",
    )

    y_turnaround: BoolProperty(
        name="",
        default=False,
    )

    y_steps: IntProperty(
        name="",
        default=1,
        min=1,
        max=360,
        get=get_y_steps,
        set=set_y_steps,
    )

    y_steps_max: IntProperty()

    # X Custom

    x_angle: FloatProperty(
        name="",
        description="Angle of each step in Z",
        default=radians(1),
        min=radians(1),
        max=radians(359.99),
        precision=3,
        subtype="ANGLE",
        unit="ROTATION",
        get=get_x_angle,
        set=set_x_angle,
    )

    x_clamped_angle: FloatProperty(
        name="",
        description="Angle of each part in Z",
        default=radians(1),
        min=radians(1),
        max=radians(360),
        precision=3,
        subtype="ANGLE",
        unit="ROTATION",
        get=get_x_clamped_angle,
        set=set_x_clamped_angle,
    )

    right_steps: IntProperty(
        name="",
        description="Steps to rotate in +Z",
        default=0,
        min=0,
        max=359,
        get=get_right_steps,
        set=set_right_steps,
    )

    left_steps: IntProperty(
        name="",
        description="Steps to rotate in -Z",
        default=0,
        min=0,
        max=359,
        get=get_left_steps,
        set=set_left_steps,
    )

    # Y Custom

    y_angle: FloatProperty(
        name="",
        description="Angle of each step in X",
        default=radians(1),
        min=radians(1),
        max=radians(359.99),
        precision=3,
        subtype="ANGLE",
        unit="ROTATION",
        get=get_y_angle,
        set=set_y_angle,
    )

    y_clamped_angle: FloatProperty(
        name="",
        description="Angle of each part in X",
        default=radians(1),
        min=radians(1),
        max=radians(360),
        precision=3,
        subtype="ANGLE",
        unit="ROTATION",
        get=get_y_clamped_angle,
        set=set_y_clamped_angle,
    )

    up_steps: IntProperty(
        name="",
        description="Steps to rotate in +X",
        default=0,
        min=0,
        max=359,
        get=get_up_steps,
        set=set_up_steps,
    )

    down_steps: IntProperty(
        name="",
        description="Steps to rotate in -X",
        default=0,
        min=0,
        max=359,
        get=get_down_steps,
        set=set_down_steps,
    )

    # Insert keyframes

    views_count: IntProperty(
        default=1,
        get=get_views_count,
    )

    marker_name: StringProperty(
        name="",
        description="Markers name (use %H% and %V% for horizontal and vertical values)",
        default="No marker name",
        maxlen=1024,
        subtype="FILE_NAME",
        get=get_marker_name,
        set=set_marker_name,
    )

    marker_name_preview: StringProperty(
        name="",
        description="Example marker name",
        default="V1H0",
        maxlen=1024,
        subtype="FILE_NAME",
        get=get_marker_name_preview,
    )

    # Render

    path: StringProperty(
        name="",
        description="Path to save the frames",
        default="",
        maxlen=1024,
        subtype="DIR_PATH",
        get=get_abs_path,
        set=set_abs_path,
    )

    hidden_objects: CollectionProperty(type=Obj)

    only_selected: BoolProperty(
        name="",
        description="Hide/Show non-selected renderable objects in viewport and in render",
        default=False,
        update=lambda self, context: isolate.isolate_selection_func(
            self, context, "only_selected"
        ),
    )

    frames_count: IntProperty(
        default=1,
        get=get_frames_count,
    )


classes = (
    Obj,
    MyProperties,
)
