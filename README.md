# Dolly Zoom Blender extension

A simple Blender extension that provides a "Dolly Zoom" (Hitchcock effect / Perspective gain) property for both the 3D Viewport and cameras.

Adjusting the Dolly Zoom property changes the focal length, while simultaneously moving viewport/camera forward/backward along the viewing Z-axis, keeping objects at the 3D Cursor framed at the same size.

This makes framing a shot far more convenient in some cases. To animate this effect focal length and camera location needs to be keyframed individually. Camera dolly zoom property is not key-able on its own. 

## Features
- Works in 3D Viewport (`N-panel > View > Dolly Zoom`).
- Works on Camera objects (`Properties > Camera > Lens > Dolly Zoom`).
- Keeps two-way synchronization with Blender's native Focal Length.
- Target focal point is always the 3D Cursor.

## Compatibility
- Blender 4.2+ / 5.x (as an Extension).
- Blender 3.x / 4.1 (as a standard Add-on).

## Support and Documentation
- Repository: https://github.com/ElmoTree/blender-dolly-zoom