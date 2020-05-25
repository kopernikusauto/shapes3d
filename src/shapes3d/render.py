"""Implements functions regarding rendering in blender

Implementation of useful functionalities for computer vision 
in single functions, as well as grouping common functions used 
in blender repetitively regarding rendering.
"""

import bpy
import numpy as np
from pathlib import Path
from PIL import Image
from typing import Tuple
from typing import List
from typing import Optional

from shapes3d.utils import UndoChanges

SCENE = 'Scene'
CAMERA = 'Camera'

OUTPUT_NODE_TYPE = 'CompositorNodeOutputFile'
IMAGE_NODE_TYPE = 'CompositorNodeRLayers'
OBJECT_INFO_NODE_TYPE = 'ShaderNodeObjectInfo'
COLOR_RAMP_NODE_TYPE = 'ShaderNodeValToRGB'
EMISSION_NODE_TYPE = 'ShaderNodeEmission'
MAT_OUTPUT_NODE_TYPE = 'ShaderNodeOutputMaterial'
COLOR_VIEW_LAYER_TYPE = 'CompositorNodeViewer'

COLOR_IMG_NODE = 'Shapes3d_Color_img_image_node'
OUTPUT_Z_NODE = 'Shapes3d_Output_z_node'
OUTPUT_Z_NODE_PNG = 'Shapes3d_Output_z_node_png'
OUTPUT_COLOR_NODE = 'Shapes3d_Output_color_node'
OUTPUT_INST_SEG_NODE = 'Shapes3d_Output_inst_seg_node'
COLOR_VIEW_LAYER = 'Shapes3d_View_node'
Z_NORM_NODE = 'Shapes3d_Z_norm_node'

SEGMENTATION_MAT = "Shapes3d_Segmentation_material"

DEPTH_FILE_NAME = "Image_depth_"
DEPTH_PNG_FILE_NAME = "Image_depth_"
COLOR_FILE_NAME = "Image_color_"
BBOX_FILE_NAME = "Bbox_"
BBOX_IMAGE_FILE_NAME = "Image_bbox_"
INST_SEG_FILE_NAME = "Image_inst_seg_"

EXR_FILE_TYPE = 'OPEN_EXR'
PNG_FILE_TYPE = 'PNG'
JPEG_FILE_TYPE = 'JPEG'

CYCLES = 'CYCLES'
EVEE = 'BLENDER_EEVEE'

def unset_color():
    color_scene = bpy.data.scenes[SCENE]
    bpy.context.window.scene = color_scene
    color_scene.use_nodes = True
    tree = color_scene.node_tree

    if OUTPUT_COLOR_NODE in tree.nodes.keys():
        tree.nodes.remove(tree.nodes[OUTPUT_COLOR_NODE])

def set_color(activate: bool=True, file_format: str='PNG',
              alpha: bool=True, denoise: bool=True):
    """
    File format in [PNG, JPEG], alpha only for PNG
    """
    scene = bpy.data.scenes[SCENE]
    bpy.context.window.scene = scene
    scene.use_nodes = True
    tree = scene.node_tree

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

    if denoise:
        scene.view_layers['View Layer'].cycles.use_denoising = True

    # To get img from node for saving bboxes
    if COLOR_VIEW_LAYER not in tree.nodes.keys():
        viewer_node = tree.nodes.new(COLOR_VIEW_LAYER_TYPE)
        viewer_node.name = COLOR_VIEW_LAYER
    links.new(img_node.outputs['Image'], viewer_node.inputs[0])

    if file_format == 'PNG':
        output_color_node.format.file_format = PNG_FILE_TYPE 
        if alpha:
            output_color_node.format.color_mode = 'RGBA'
            bpy.context.scene.render.film_transparent = True
        else:
            output_color_node.format.color_mode = 'RGB'
    else:
        output_color_node.format.file_format = JPEG_FILE_TYPE 

    links.new(img_node.outputs['Image'],
              output_color_node.inputs['Image'])

def set_instance_segmentation(file_format: str='PNG'):
    scene = bpy.data.scenes[SCENE]
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
    color_scene = bpy.data.scenes[SCENE]
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
    color_scene = bpy.data.scenes[SCENE]
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

def get_2d_bounding_boxes(save_txt: Optional[bool]=False,
                          path: Optional[str]="./",
                          file_id: Optional[int]=None,
                          quick: bool=False,
                          clip_to_frame: Optional[bool]=True) -> list:
    """Returns the bounding box of the objects.

    Returns the bounding boxes of the objects in the scene and if 
    path is passed it also saves it in a file. Does not support classes yet
    
    Args:
        plot_bboxes (bool): Save an image with the bounding boxes or not
        save_txt (bool): Save a txt file with bboxes
        path (str): if none, no txt file is saved
        file_id (int): Default None. if None, it uses the current blender frame.
            Ignored if path is None
        clip_to_frame (bool): Clip bbox to image dimensions
        quick (bool): approximates the 2d bounding box using
            the 3d bounding box. It is not recommended to use quick option.
            It heavily depends on the rotation and 3D shape of the object.
        
    Returns: List(name, x, y, width, height)
        name: of mesh
        x, y: bottom, left corner
        width: of the bounding box
        height: of the bounding box
    """
    bboxes = []
    scene = bpy.data.scenes[SCENE]
    cam = bpy.data.objects[CAMERA]

    to_cam = np.array(cam.matrix_world.inverted().normalized())

    # Get output img
    im_width = scene.render.resolution_x
    im_height = scene.render.resolution_y

    # get focal lenght and sensor size
    cam.data.lens_unit = 'MILLIMETERS'
    cam.data.sensor_fit = 'HORIZONTAL'
    fl = cam.data.lens
    sensor_w = cam.data.sensor_width
    sensor_h = sensor_w * im_height / im_width

    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue 

        if quick:
            verts = ob.bound_box
            verts = np.array([list(v) + [1,] for v in verts]).T
        else:
            verts = ob.data.vertices
            verts = np.array([list(v.co) + [1,] for v in verts]).T

        # Get transformations
        to_ob = np.array(ob.matrix_world.normalized())

        # Move corners to ob and to cam view
        verts = to_ob @ verts # to ob
        verts = to_cam @ verts # to cam

        # Perspective transformation
        K = np.array([[-fl / sensor_w * im_width, 0, im_width / 2],
                      [0, fl / sensor_h * im_height, im_height / 2],
                      [0, 0, 1]])

        verts = K @ verts[:3]
        verts /= verts[2]

        if clip_to_frame:
            filt = (0 < verts[0]) & (verts[0] < im_width-1) & (0 < verts[1]) & (verts[1] < im_height-1)
            verts = verts[:, filt]

        if len(verts) == 0 or verts.size == 0:
            continue 

        min_x = verts[0].min()
        max_x = verts[0].max()
        min_y = verts[1].min()
        max_y = verts[1].max()

        bbox = [int(round(min_x, 0)),
                int(round(min_y, 0)),
                int(round(max_x, 0)),
                int(round(max_y, 0)),
                ob.name]

        if max_x - min_x < 1 or max_y - min_y < 1:
            continue

        bboxes.append(bbox)

    if save_txt:
        if file_id is None:
            file_id = scene.frame_current

        path = Path(path)
        file_path = path / (BBOX_FILE_NAME + str(file_id) + ".txt")

        with open(file_path, "w") as f:
            f.write("min_x, min_y, max_x, max_y, object_name")
            for bbox in bboxes:
                bbox = [str(el) for el in bbox]
                f.write(" ".join(bbox))
                f.write("\n")

    return bboxes

def plot_2d_bboxes(bboxes: List[List],
                   path: str,
                   file_id: Optional[int]=None,
                   ) -> None:
    """Plots the bboxes in the current scene and saves the file.

    Use quick only for debugging purposes.
    
    Args:
        bboxes (list): List of bboxes as returned in get_2d_bounding_boxes.
        path (str): Directory where to save the file
        file_id (int): id of the file. If None, the current frame of the scene is used
    """
    if not has_color():
        raise RuntimeError("To plot bounding boxes call first set_color")

    scene = bpy.data.scenes[SCENE]
    tree = scene.node_tree
    output_color_node = tree.nodes[OUTPUT_COLOR_NODE]

    # Get output img
    im_width = scene.render.resolution_x
    im_height = scene.render.resolution_y

    im_id = bpy.data.scenes['Scene'].frame_current
    im_path = bpy.context.scene.render.filepath
    im_name = output_color_node.file_slots[0].path
    im_extension = output_color_node.format.file_format
    im = Path(im_path) / "{:s}{:04d}.{:s}".format(im_name, im_id, im_extension.lower())

    try:
        im = np.array(Image.open(str(im)))
    except:
        raise RuntimeError("Call this function just after calling render()")

    # To use in-memory pixel information
    # Which is no the same as the final rendered image
    # im = np.array(bpy.data.images['Viewer Node'].pixels)
    # im = im.reshape((im_height, im_width, 4))[::-1]

    if file_id is None:
        file_id = scene.frame_current

    for min_x, min_y, max_x, max_y, _ in bboxes:
        im[min_y, min_x:max_x] = [255, 0, 0, 255]
        im[max_y, min_x:max_x] = [255, 0, 0, 255]
        im[min_y:max_y, min_x] = [255, 0, 0, 255]
        im[min_y:max_y, max_x] = [255, 0, 0, 255]

        # Uncomment this to plot using matplotlib
        # bbox = np.array([[min_x, min_y],
        #                  [min_x, min_y + b_height],
        #                  [min_x + b_width, min_y + b_height],
        #                  [min_x + b_width, min_y],
        #                  [min_x, min_y]]).T

    path = Path(path)
    Image.fromarray(im).save(
            str(path / "{}{:04d}.png".format(BBOX_IMAGE_FILE_NAME,file_id)))

    # Uncomment this to plot using matplotlib
    # plt.imshow(im[::-1])
    # plt.plot(bbox[0], bbox[1], "-r")
    # plt.show()

def set_image_resolution(width_px: int, height_px: int):
    bpy.data.scenes[SCENE].render.resolution_x = width_px
    bpy.data.scenes[SCENE].render.resolution_y = height_px

def remove_nodes(scene: bpy.types.Scene):
    tree = scene.node_tree
    for n in tree.nodes:
        tree.nodes.remove(n)

def _has_node(scene_name: str, node_name: str) -> bool:
    bpy.data.scenes[scene_name].use_nodes = True
    tree = bpy.data.scenes[scene_name].node_tree
    return node_name in tree.nodes.keys()

def set_image_path(path: Optional[str]=None, file_id: Optional[int]=None):
    if not path and not isinstance(file_id, int):
        raise AttributeError("At least one input has to be passed")

    tree = bpy.data.scenes[SCENE].node_tree

    if isinstance(file_id, int):
        if bpy.context.scene.frame_start > file_id:
            bpy.context.scene.frame_start = file_id
        bpy.data.scenes['Scene'].frame_set(file_id)

    if path:
        bpy.context.scene.render.filepath = path
        if has_color():
            tree.nodes[OUTPUT_COLOR_NODE].base_path = path

    if has_depth_map():
        tree.nodes[OUTPUT_Z_NODE].base_path = path

        if has_norm_depth_map():
            tree.nodes[OUTPUT_Z_NODE_PNG].base_path = path

    if has_instance_segmentation_map():
        tree.nodes[OUTPUT_INST_SEG_NODE].base_path = path

def has_color()-> bool:
    return _has_node(SCENE, OUTPUT_COLOR_NODE)

def has_depth_map()-> bool:
    return _has_node(SCENE, OUTPUT_Z_NODE)

def has_norm_depth_map()-> bool:
    return _has_node(SCENE, OUTPUT_Z_NODE_PNG)

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

def render(path: Optional[str] = None,
           file_id: Optional[int]=None,
           include_bbox2d: Optional[bool]=False,
           save_bbox2d_to_txt: Optional[bool]=False,
           plot_bbox2d: Optional[bool]=False,
           bbox2d_quick: Optional[bool]=False,
           bbox2d_clip_to_frame: Optional[bool]=True) -> List:
    """Renders the scene with the values previously configured.

    This is the only way to render the instance segmentation. To render
    the depth or color image F12 in blender will also work.

    Args:
        path (str): where to save images.
        file_id (int): int to add to the name of the file. Default=frame of the scene.
        include_bbox2d (bool): Returns bounding boxes of objects.
        save_bbox2d_to_txt (bool): Saves bboxes to txt file.
        plot_bbox2d (bool): Save image with bboxes plotted.
        bbox2d_quick (bool): Use approximations to calculate bbox.
        bbox2d_clip_to_frame (bool): Do not allow bbox coords outside of image frame.

    Returns:
        if include_bbox2d or save_bbox2d_to_txt is True, returns list of all
        bboxes. Each box is [min_x, min_y, max_x, max_y, object name]. Else,
        returns None
    """
    if path or isinstance(file_id, int):
        set_image_path(path, file_id)

    # Render color and depth
    bpy.ops.render.render()

    bboxes = None
    # Call this just after rendering color
    if include_bbox2d or save_bbox2d_to_txt or plot_bbox2d: 
        # if path is None but color image has one, use that one
        if path is None and has_color():
            path = tree.nodes[OUTPUT_COLOR_NODE].base_path

        bboxes = get_2d_bounding_boxes(save_txt=save_bbox2d_to_txt,
                                       path=path,
                                       file_id=file_id,
                                       quick=bbox2d_quick,
                                       clip_to_frame=bbox2d_clip_to_frame)

        plot_2d_bboxes(bboxes, path=path, file_id=file_id)

    if has_instance_segmentation_map():
        # Render Segmentation 
        with UndoChanges():
            scene = bpy.data.scenes[SCENE]
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

    return bboxes

def set_scene_into_instance_segmentation(scene_name: str = SCENE):
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
