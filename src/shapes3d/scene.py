"""Deals with generic behaviours regarding the scene properties and elements."""

from typing import Tuple
import bpy

LIGHT_TYPE = 'LIGHT'
LIGHT_NAME = 'Light'
SUN_TYPE = 'SUN'
LIGHT_SUPPORTED_TYPES = [SUN_TYPE]

def clean_scene():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
        else:
            obj.select_set(False)

    # Call the operator only once
    bpy.ops.object.delete()

def set_light(light_type: str=SUN_TYPE, location: tuple=(4,1,6), energy: float=1):
    """Sets light of the scene.
    
    Args:
        light_type (str): type of light, only supported 'SUN'
        location (tuple): (x,y,z) in meters
        energy (float): energy of light.
    """
    assert light_type in LIGHT_SUPPORTED_TYPES
    l = get_light()
    if not l:
        # create
        bpy.ops.object.light_add(type=light_type, radius=1, location=(0, 0, 0))
        l = bpy.data.objects[LIGHT_NAME]

    l.data.type = light_type
    l.data.energy = energy
    l.location = location

def get_light()->bool:
    """Return the first light element or None if there is none"""
    light = bpy.data.objects.get(LIGHT_NAME, None)
    for obj in bpy.data.objects:
        if obj.type == LIGHT_TYPE:
            light = obj
            break
    return light 

def close():
    bpy.ops.wm.quit_blender()

def set_background_color(color: Tuple[float, float, float, float]):
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = color
