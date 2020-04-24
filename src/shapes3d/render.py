"""Implements functions regarding rendering in blender

Implementation of useful functionalities for computer vision 
in single functions, as well as grouping common functions used 
in blender repetitively regarding rendering.
"""

from typing import Tuple, List, Optional
import bpy

from pdb import set_trace

from shapes3d.utils import UndoChanges

COLOR_SCENE = 'Scene'

OUTPUT_NODE_TYPE = 'CompositorNodeOutputFile'
IMAGE_NODE_TYPE = 'CompositorNodeRLayers'
OBJECT_INFO_NODE_TYPE = 'ShaderNodeObjectInfo'
COLOR_RAMP_NODE_TYPE = 'ShaderNodeValToRGB'
EMISSION_NODE_TYPE = 'ShaderNodeEmission'
MAT_OUTPUT_NODE_TYPE = 'ShaderNodeOutputMaterial'

COLOR_IMG_NODE = 'Shapes3d_Color_img_image_node'
OUTPUT_Z_NODE = 'Shapes3d_Output_z_node'
OUTPUT_Z_NODE_PNG = 'Shapes3d_Output_z_node_png'
OUTPUT_COLOR_NODE = 'Shapes3d_Output_color_node'
OUTPUT_INST_SEG_NODE = 'Shapes3d_Output_inst_seg_node'
Z_NORM_NODE = 'Shapes3d_Z_norm_node'

SEGMENTATION_MAT = "Shapes3d_Segmentation_material"

DEPTH_FILE_NAME = "Image_depth_"
DEPTH_PNG_FILE_NAME = "Image_depth_"
COLOR_FILE_NAME = "Image_color_"
INST_SEG_FILE_NAME = "Image_inst_seg_"

EXR_FILE_TYPE = 'OPEN_EXR'
PNG_FILE_TYPE = 'PNG'
JPEG_FILE_TYPE = 'JPEG'

CYCLES = 'CYCLES'
EVEE = 'BLENDER_EEVEE'

def unset_color():
    color_scene = bpy.data.scenes[COLOR_SCENE]
    bpy.context.window.scene = color_scene
    color_scene.use_nodes = True
    tree = color_scene.node_tree

    if OUTPUT_COLOR_NODE in tree.nodes.keys():
        tree.nodes.remove(tree.nodes[OUTPUT_COLOR_NODE])

def set_color(activate: bool=True, file_format: str='PNG', alpha: bool=True):
    """
    File format in [PNG, JPEG], alpha only for PNG
    """
    color_scene = bpy.data.scenes[COLOR_SCENE]
    bpy.context.window.scene = color_scene
    color_scene.use_nodes = True
    tree = color_scene.node_tree

    links = tree.links
    if COLOR_IMG_NODE in tree.nodes.keys():
        img_node = tree.nodes[COLOR_IMG_NODE]
    else:
        img_node = tree.nodes.new(IMAGE_NODE_TYPE)
        img_node.name = COLOR_IMG_NODE 

    if OUTPUT_COLOR_NODE in tree.nodes.keys():
        output_color_node = tree.nodes[OUTPUT_COLOR_NODE]
    else:
        output_color_node = tree.nodes.new(OUTPUT_NODE_TYPE)
        output_color_node.name = OUTPUT_COLOR_NODE
    output_color_node.file_slots[0].path = COLOR_FILE_NAME

    if file_format == 'PNG':
        output_color_node.format.file_format = PNG_FILE_TYPE 
        if alpha:
            output_color_node.format.color_mode = 'RGBA'
        else:
            output_color_node.format.color_mode = 'RGB'
    else:
        output_color_node.format.file_format = JPEG_FILE_TYPE 

    links.new(img_node.outputs['Image'],
              output_color_node.inputs['Image'])

def set_instance_segmentation(file_format: str='PNG'):
    scene = bpy.data.scenes[COLOR_SCENE]
    scene = bpy.context.scene

    if SEGMENTATION_MAT in bpy.data.materials.keys():
        material = bpy.data.materials[SEGMENTATION_MAT]
    else:
        material = bpy.data.materials.new(name=SEGMENTATION_MAT)

    material.use_nodes = True
    tree = material.node_tree
    links = tree.links

    for node in material.node_tree.nodes:
        tree.nodes.remove(node)

    if OBJECT_INFO_NODE_TYPE in tree.nodes.keys():
        object_info_node = tree.nodes[OBJECT_INFO_NODE_TYPE]
    else:
        object_info_node = tree.nodes.new(OBJECT_INFO_NODE_TYPE)

    if COLOR_RAMP_NODE_TYPE in tree.nodes.keys():
        col_ramp_node = tree.nodes[COLOR_RAMP_NODE_TYPE]
    else:
        col_ramp_node = tree.nodes.new(COLOR_RAMP_NODE_TYPE)
        for i in range(3):
            col_ramp_node.color_ramp.elements.new(1/4*(i+1))
        for i, el in enumerate(col_ramp_node.color_ramp.elements[1:-1]):
            c = [0,0,0]
            c[i] = 1
            c += [1,]
            el.color.data.color = c
    links.new(object_info_node.outputs['Random'],
              col_ramp_node.inputs['Fac'])

    if EMISSION_NODE_TYPE in tree.nodes.keys():
        emission_node = tree.nodes[EMISSION_NODE_TYPE]
    else:
        emission_node = tree.nodes.new(EMISSION_NODE_TYPE)
    links.new(col_ramp_node.outputs['Color'],
              emission_node.inputs['Color'])

    if MAT_OUTPUT_NODE_TYPE in tree.nodes.keys():
        mat_output_node = tree.nodes[MAT_OUTPUT_NODE_TYPE]
    else:
        mat_output_node = tree.nodes.new(MAT_OUTPUT_NODE_TYPE)
    links.new(emission_node.outputs['Emission'],
              mat_output_node.inputs['Surface'])

    # Set output node for png
    bpy.context.window.scene = scene
    scene.use_nodes = True
    tree = scene.node_tree

    links = tree.links
    if COLOR_IMG_NODE in tree.nodes.keys():
        img_node = tree.nodes[COLOR_IMG_NODE]
    else:
        img_node = tree.nodes.new(IMAGE_NODE_TYPE)
        img_node.name = COLOR_IMG_NODE 

    if OUTPUT_INST_SEG_NODE in tree.nodes.keys():
        output_color_node = tree.nodes[OUTPUT_INST_SEG_NODE]
    else:
        output_color_node = tree.nodes.new(OUTPUT_NODE_TYPE)
        output_color_node.name = OUTPUT_INST_SEG_NODE
    output_color_node.file_slots[0].path = INST_SEG_FILE_NAME
    output_color_node.mute = True

    if file_format == 'PNG':
        output_color_node.format.file_format = PNG_FILE_TYPE 
        output_color_node.format.color_mode = 'RGB'
    else:
        output_color_node.format.file_format = JPEG_FILE_TYPE 

    links.new(img_node.outputs['Image'],
              output_color_node.inputs['Image'])
        
def unset_instance_segmentation():
    if has_instance_segmentation_map():
        bpy.data.materials.remove(bpy.data.materials[SEGMENTATION_MAT])

def uset_depth_map():
    color_scene = bpy.data.scenes[COLOR_SCENE]
    bpy.context.window.scene = color_scene
    color_scene.use_nodes = True
    tree = color_scene.node_tree

    if OUTPUT_Z_NODE in tree.nodes.keys():
        tree.nodes.remove(tree.nodes[OUTPUT_Z_NODE])
    if OUTPUT_Z_NODE_PNG in tree.nodes.keys():
        tree.nodes.remove(tree.nodes[OUTPUT_Z_NODE_PNG])
    if Z_NORM_NODE in tree.nodes.keys():
        tree.nodes.remove(tree.nodes[Z_NORM_NODE])

def set_depth_map(include_png: bool = False):
    color_scene = bpy.data.scenes[COLOR_SCENE]
    bpy.context.window.scene = color_scene
    color_scene.use_nodes = True
    tree = color_scene.node_tree

    links = tree.links

    # From
    if COLOR_IMG_NODE in tree.nodes.keys():
        img_node = tree.nodes[COLOR_IMG_NODE]
    else:
        img_node = tree.nodes.new(IMAGE_NODE_TYPE)
        img_node.name = COLOR_IMG_NODE 

    # Output
    if OUTPUT_Z_NODE in tree.nodes.keys():
        output_node = tree.nodes[OUTPUT_Z_NODE]
    else:
        output_node = tree.nodes.new(OUTPUT_NODE_TYPE)
        output_node.name = OUTPUT_Z_NODE
    output_node.format.file_format = EXR_FILE_TYPE
    output_node.file_slots[0].path = DEPTH_FILE_NAME

    links.new(img_node.outputs['Depth'],
              output_node.inputs['Image'])

    if include_png:
        # PNG output
        if OUTPUT_Z_NODE_PNG in tree.nodes.keys():
            output_png_node = tree.nodes[OUTPUT_Z_NODE_PNG]
        else:
            output_png_node = tree.nodes.new(OUTPUT_NODE_TYPE)
            output_png_node.name = OUTPUT_Z_NODE_PNG
        output_png_node.format.file_format = PNG_FILE_TYPE
        output_png_node.file_slots[0].path = DEPTH_PNG_FILE_NAME
        output_png_node.format.color_mode = "BW"


        # Normalizer
        if Z_NORM_NODE in tree.nodes.keys():
            norm_node = tree.nodes[Z_NORM_NODE]
        else:
            norm_node = tree.nodes.new('CompositorNodeNormalize')
            norm_node.name = Z_NORM_NODE

        links.new(img_node.outputs['Depth'],
                  norm_node.inputs['Value'])
        links.new(norm_node.outputs['Value'],
                  output_png_node.inputs['Image'])

def set_image_resolution(width_px: int, height_px: int):
    bpy.data.scenes[COLOR_SCENE].render.resolution_x = width_px
    bpy.data.scenes[COLOR_SCENE].render.resolution_y = height_px

def remove_nodes(scene: bpy.types.Scene):
    tree = scene.node_tree
    for n in tree.nodes:
        tree.nodes.remove(n)

def _has_node(scene_name: str, node_name: str) -> bool:
    bpy.data.scenes[scene_name].use_nodes = True
    tree = bpy.data.scenes[scene_name].node_tree
    return node_name in tree.nodes.keys()

def set_image_path(path: Optional[str]=None, file_id: Optional[int]=None):
    if not path and not file_id:
        raise AttributeError("At least one input has to be passed")

    tree = bpy.data.scenes[COLOR_SCENE].node_tree

    if file_id:
        bpy.data.scenes['Scene'].frame_set(file_id)

    if has_color():
        if path:
            bpy.context.scene.render.filepath = path
            tree.nodes[OUTPUT_COLOR_NODE].base_path = path

    if has_depth_map():
        tree.nodes[OUTPUT_Z_NODE].base_path = path

        if has_norm_depth_map():
            tree.nodes[OUTPUT_Z_NODE_PNG].base_path = path

    if has_instance_segmentation_map():
        tree.nodes[OUTPUT_INST_SEG_NODE].base_path = path

def has_color()-> bool:
    return _has_node(COLOR_SCENE, OUTPUT_COLOR_NODE)

def has_depth_map()-> bool:
    return _has_node(COLOR_SCENE, OUTPUT_Z_NODE)

def has_norm_depth_map()-> bool:
    return _has_node(COLOR_SCENE, OUTPUT_Z_NODE_PNG)

def has_instance_segmentation_map()-> bool:
    return SEGMENTATION_MAT in bpy.data.materials.keys()

def set_render_config(render: Optional[str]=None,
                      gpu: Optional[bool]=False,
                      image_resolution: Optional[Tuple[int, int]] = None,
                      max_bounces: Optional[int] = None,
                      tile_dim: Optional[Tuple[int, int]] = None,
                      samples: Optional[int] = None):
    """Sets the configuration for rendering in one function

    Args:
        render (str): Either 'Eevee' or 'Cycles'. The render engine to use
        gpu (bool): True to use gpu. Only works when render='Cycles'. Sets 
            render='Cycles' if render = None and gpu = True.
        image_resoluion (tuple): (width_px, height_px) tuple of ints in pixels
        max_bounces (int): Number of max bouces of ray (Cycles only)
        tile_dim (int): (x,y) tuple of ints in pixels
        samples (int): Number of samples in int (Cycles only)
    """
    if gpu and not render:
        render = CYCLES

    if render == 'Eevee':
        bpy.context.scene.render.engine = EEVEE 
    elif render == 'Cycles':
        bpy.context.scene.render.engine = CYCLES 
        if gpu:
            bpy.context.scene.cycles.device = 'GPU'
        else:
            bpy.context.scene.cycles.device = 'CPU'
    
    if image_resolution:
        set_image_resolution(*image_resolution)

    if samples:
        bpy.context.scene.cycles.samples = samples

    if max_bounces:
        bpy.context.scene.cycles.max_bounces = max_bounces

    if tile_dim:
        bpy.context.scene.render.tile_x = tile_dim[0]
        bpy.context.scene.render.tile_y = tile_dim[1]

def render(path: Optional[str] = None, file_id: Optional[int]=None) -> None:
    """Renders the scene with the values previously configured.

    This is the only way to render the instance segmentation. To render
    the depth or color image F12 in blender will also work.

    Args:
        path (str): where to save images
        file_id (int): int to add to the name of the file. Default=frame of the scene
    """
    if path or file_id:
        set_image_path(path, file_id)

    # Render color and depth
    bpy.ops.render.render()

    if has_instance_segmentation_map():
        # Render Segmentation 
        with UndoChanges():
            scene = bpy.data.scenes[COLOR_SCENE]
            scene.node_tree.nodes[OUTPUT_INST_SEG_NODE].mute = False
            if has_depth_map():
                scene.node_tree.nodes[OUTPUT_Z_NODE].mute = True

                if has_norm_depth_map():
                    scene.node_tree.nodes[OUTPUT_Z_NODE_PNG].mute = True

            if has_color():
                scene.node_tree.nodes[OUTPUT_COLOR_NODE].mute = True

            # For all objects unlink material
            set_scene_into_instance_segmentation()

            # Render again only instance segmentation
            bpy.ops.render.render()

def set_scene_into_instance_segmentation(scene_name: str = COLOR_SCENE):
    if not has_instance_segmentation_map():
        raise UserWarning("Calling set_scene_into_instance_segmentation before calling set_instance_segmentation")
        set_instance_segmentation()

    scene = bpy.data.scenes[scene_name]
    material = bpy.data.materials[SEGMENTATION_MAT]
    for obj in scene.objects:
        if obj.type == 'MESH':
            if len(obj.material_slots) == 0:
                context = {"object": obj}
                bpy.ops.object.material_slot_add(context)
            for slot in obj.material_slots:
                slot.material = material
