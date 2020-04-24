"""Deals with functions in blender regarding the camera object."""

import bpy


CAMERA = 'Camera'
SCENE = 'Scene'

def set_focal_length(mm: float):
    """ In milimeters. This overwrites fov """
    bpy.data.objects[CAMERA].data.lens = mm

def set_fov(radians: float):
    """ In radians. This overwrites focal length """
    bpy.data.objects[CAMERA].data.angle = radians

def set_near(meters: float):
    bpy.data.objects[CAMERA].data.clip_start = meters

def set_far(meters: float):
    bpy.data.objects[CAMERA].data.clip_end = meters

def set_location(tx: float, ty: float, tz: float):
    """ Location in meters """
    scene = bpy.data.scenes[SCENE]
    scene.camera.rotation_mode = 'XYZ'
    scene.camera.location.x = tx
    scene.camera.location.y = ty
    scene.camera.location.z = tz

def set_rotation(rx: float, ry: float, rz: float):
    """
    Rotation is in Euler angles XYZ in radians
    """
    scene = bpy.data.scenes[SCENE]
    scene.camera.rotation_mode = 'XYZ'
    scene.camera.rotation_euler[0] = rx
    scene.camera.rotation_euler[1] = ry
    scene.camera.rotation_euler[2] = rz

def get_intrinsic_parameters():
    """Returns intrinsic parameters.

    Intrinsic parameters not returned in this function (e.g. skew)
    are assumed to be zero.

    Returns:
        x focal lenght (float)
        y focal lenght (float)
        x principal point (int)
        y principal point (int)
    """
    fx = bpy.data.objects[CAMERA].data.lens/10/1000
    fy = fx
    cx = bpy.data.scenes[SCENE].render.resolution_x/2
    cy = bpy.data.scenes[SCENE].render.resolution_y/2
    intrinsic = [fx, fy, cx, cy]
    return intrinsic

def get_extrinsic_parameters():
    """Returns camera translation and rotation parameters.
    
    Returns
        rx,ry,rz,tx,ty,tz: r in gradians and t in meters
    """
    scene = bpy.data.scenes[SCENE]
    tx = scene.camera.location.x
    ty = scene.camera.location.y
    tz = scene.camera.location.z

    rx = scene.camera.rotation_euler[0]
    ry = scene.camera.rotation_euler[1]
    rz = scene.camera.rotation_euler[3]

    extrinsic = [rx, ry, rz, tx, ty, tz]
    return extrinsic

def close():
    bpy.ops.wm.quit_blender()
