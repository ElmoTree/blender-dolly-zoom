bl_info = {
    "name": "Dolly Zoom",
    "author": "Josef Ludvík Böhm",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "3D View > Sidebar (N) > View | Properties > Camera > Lens",
    "description": "Dolly zoom (Hitchcock effect) with 3D Cursor as focal point, for viewport and camera.",
    "doc_url": "https://github.com/Surf-Ace/blender-dolly-zoom",
    "tracker_url": "https://github.com/Surf-Ace/blender-dolly-zoom",
    "category": "3D View",
    "license": "GPL-3.0-or-later",
}

import bpy
from mathutils import Vector

# Helper Functions

def get_active_space_view3d():
    """Returns the active 3D Viewport space, if any."""
    space = getattr(bpy.context, "space_data", None)
    if isinstance(space, bpy.types.SpaceView3D):
        return space
    area = getattr(bpy.context, "area", None)
    return area.spaces.active if (area and area.type == 'VIEW_3D') else None


def get_camera_object_for_data(camera_data):
    """
    Finds the Object associated with camera_data.
    Prioritizes active object, then viewport local/scene camera.
    """
    # 1. Active selected camera
    act = bpy.context.active_object
    if act and act.type == 'CAMERA' and act.data == camera_data:
        return act

    # 2. Viewport local camera or scene camera
    space = get_active_space_view3d()
    if space and space.camera and space.camera.data == camera_data:
        return space.camera

    scene = bpy.context.scene
    if scene and scene.camera and scene.camera.data == camera_data:
        return scene.camera

    return None

# Viewport Dolly Zoom Get/Set Callbacks

def get_viewport_dolly_zoom(self):
    space = get_active_space_view3d()
    return space.lens if space else 50.0


def set_viewport_dolly_zoom(self, value):
    space = get_active_space_view3d()
    if not space or not space.region_3d or space.region_3d.view_perspective == 'ORTHO':
        return

    old_lens = space.lens
    new_lens = max(1.0, float(value))
    if abs(new_lens - old_lens) < 1e-4:
        return

    r3d = space.region_3d
    cursor = bpy.context.scene.cursor.location
    view_forward = r3d.view_rotation @ Vector((0.0, 0.0, -1.0))
    cam_pos = r3d.view_location - (view_forward * r3d.view_distance)

    depth = (cursor - cam_pos).dot(view_forward)
    if depth <= 0.001:
        depth = max(r3d.view_distance, 0.1)

    delta_d = depth * ((new_lens / old_lens) - 1.0)
    new_cam_pos = cam_pos - (view_forward * delta_d)

    new_distance = max(0.01, r3d.view_distance + delta_d)
    r3d.view_distance = new_distance
    r3d.view_location = new_cam_pos + (view_forward * new_distance)

    space.lens = new_lens
    r3d.update()

# Camera Dolly Zoom Get/Set Callbacks

def get_camera_dolly_zoom(self):
    return self.lens


def set_camera_dolly_zoom(self, value):
    if self.type != 'PERSP':
        return

    cam_obj = get_camera_object_for_data(self)
    if not cam_obj:
        return

    old_lens = self.lens
    new_lens = max(1.0, float(value))
    if abs(new_lens - old_lens) < 1e-4:
        return

    rot = cam_obj.matrix_world.to_quaternion()
    view_forward = rot @ Vector((0.0, 0.0, -1.0))
    cam_pos = cam_obj.matrix_world.translation.copy()
    cursor = bpy.context.scene.cursor.location

    depth = (cursor - cam_pos).dot(view_forward)
    if depth <= 0.001:
        depth = max((cursor - cam_pos).length, 1.0)

    delta_d = depth * ((new_lens / old_lens) - 1.0)
    translation_delta = -view_forward * delta_d

    if cam_obj.parent is None:
        cam_obj.location += translation_delta
    else:
        cam_obj.matrix_world.translation += translation_delta

    self.lens = new_lens

# UI Panels

class VIEW3D_PT_dolly_zoom(bpy.types.Panel):
    """Subpanel in 3D Viewport N-Panel under View > View."""
    bl_idname = "VIEW3D_PT_dolly_zoom"
    bl_label = "Dolly Zoom"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_parent_id = "VIEW3D_PT_view3d_properties"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        space = context.space_data
        r3d = space.region_3d if space else None
        if not r3d:
            return

        if r3d.view_perspective != 'CAMERA':
            # Free Viewport Mode -> Always Viewport Dolly Zoom
            col = layout.column()
            is_persp = (r3d.view_perspective == 'PERSP')
            col.enabled = is_persp
            col.prop(context.window_manager, "viewport_dolly_zoom", text="Dolly Zoom")
            if not is_persp:
                col.label(text="Disabled: Viewport is Orthographic", icon='INFO')
        else:
            # Looking through Camera -> Camera Dolly Zoom (Active Camera or Scene Camera)
            act = context.active_object
            cam_obj = act if (act and act.type == 'CAMERA') else (space.camera or context.scene.camera)

            if cam_obj and cam_obj.type == 'CAMERA':
                col = layout.column()
                is_persp = (cam_obj.data.type == 'PERSP')
                col.enabled = is_persp
                col.prop(cam_obj.data, "dolly_zoom", text="Camera Dolly Zoom")
                if not is_persp:
                    col.label(text=f"Disabled: Camera is {cam_obj.data.type.capitalize()}", icon='INFO')
            else:
                layout.label(text="No Scene Camera", icon='CAMERA_DATA')

        row = layout.row()
        row.alignment = 'RIGHT'
        row.label(text="Target: 3D Cursor", icon='CURSOR')


class DATA_PT_camera_dolly_zoom(bpy.types.Panel):
    """Subpanel in Properties Editor > Camera Data > Lens."""
    bl_idname = "DATA_PT_camera_dolly_zoom"
    bl_label = "Dolly Zoom"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "DATA_PT_lens"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        cam = context.camera
        if not cam:
            return

        col = layout.column()
        is_persp = (cam.type == 'PERSP')
        col.enabled = is_persp
        col.prop(cam, "dolly_zoom", text="Dolly Zoom")
        if not is_persp:
            col.label(text=f"Disabled: Camera is {cam.type.capitalize()}", icon='INFO')

        row = layout.row()
        row.alignment = 'RIGHT'
        row.label(text="Target: 3D Cursor", icon='CURSOR')

# Registration

classes = (
    VIEW3D_PT_dolly_zoom,
    DATA_PT_camera_dolly_zoom,
)

PROPERTY_DESCRIPTION = (
    "Adjust focal length while dollying to match framing at the 3D Cursor.\n"
    "Staging tool only (not animatable). To animate, keyframe Camera Location and Focal Length"
)


def register():
    bpy.types.WindowManager.viewport_dolly_zoom = bpy.props.FloatProperty(
        name="Dolly Zoom",
        description=PROPERTY_DESCRIPTION,
        unit='CAMERA',
        min=1.0,
        max=10000.0,
        soft_min=1.0,
        soft_max=500.0,
        step=10,
        precision=2,
        options={'SKIP_SAVE'},
        get=get_viewport_dolly_zoom,
        set=set_viewport_dolly_zoom,
    )

    bpy.types.Camera.dolly_zoom = bpy.props.FloatProperty(
        name="Dolly Zoom",
        description=PROPERTY_DESCRIPTION,
        unit='CAMERA',
        min=1.0,
        max=10000.0,
        soft_min=1.0,
        soft_max=500.0,
        step=10,
        precision=2,
        options={'SKIP_SAVE'},
        get=get_camera_dolly_zoom,
        set=set_camera_dolly_zoom,
    )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    if hasattr(bpy.types.Camera, "dolly_zoom"):
        del bpy.types.Camera.dolly_zoom

    if hasattr(bpy.types.WindowManager, "viewport_dolly_zoom"):
        del bpy.types.WindowManager.viewport_dolly_zoom


if __name__ == "__main__":
    register()