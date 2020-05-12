import math
from pdb import set_trace
import random
from typing import Tuple, List, Optional, Union

import bpy
import numpy as np

import shapes3d as shps
from shapes3d.shapes import Plane, Sphere, Cuboid, Cylinder, Cone

class SimpleWorld:
    """Simple World class using shapes3d.

    This environment takes care of simple radius-based collision check. Randomization
    of positions and color textures. Tracking objects.

    Args:
        dims (tuple): (width, lenght, height) tuple of floats in meters for 
                the dimensions of the base/floor and height of the walls
        use_walls (bool): Whether create wall or not
        use_gpu (bool): Use gpu or not
    """
    def __init__(self,
                 use_walls: bool=False,
                 dims: tuple=(10, 10, 2),
                 use_gpu: bool=False
                 ):
        self._clean_scene()
        self._close_blender_when_done = True

        self._floor = None
        self._walls = []
        self._shapes = []

        self._use_walls = use_walls
        self._dims = dims
        self._use_gpu = use_gpu

        # Create plane
        self._floor = Plane(id=0, dims=self._dims[:2])

        # create walls
        if self._use_walls:
            self._create_walls()

        # Create light
        self.set_light()

        # Set renderer
        self.set_renderer(gpu=use_gpu)
        shps.render.set_color()
        shps.render.set_depth_map(include_png=True)
        shps.render.set_instance_segmentation()

        # Set background color
        shps.scene.set_background_color((0,0,0,0))

    def _create_walls(self):
        bit_a = 0 # width or height, x or y
        bit_b = 0 # positive or negative
        for i in range(4):
            loc = [0,0,(self._dims[-1]/2)]
            loc[bit_a] = (self._dims[bit_a]*(-1)**bit_b)/2

            dims = list(self._dims[:2])
            dims[bit_a] = self._dims[-1]

            rot = [0,0,0]
            rot[bit_a ^ 1] = (-1**bit_b)*math.pi/2

            wall = Plane(i+1, location=loc, dims=dims, rotation=rot)

            self._walls.append(wall)

            bit_b, bit_a = bit_a, 1 ^ bit_b

    def reset(self):
        bpy.ops.object.select_all(action='DESELECT')
        for shp in self._shapes:
            obj = bpy.data.objects.get(shp._name, None)
            if obj:
                obj.select_set(True)
        bpy.ops.object.delete()
        self._shapes = []

    def generate_intrinsic_parameters(self):
        """Returns intrinsic parameters.

        Intrinsic parameters not returned in this function (e.g. skew)
        are assumed to be zero.

        Returns:
            x focal lenght (float)
            y focal lenght (float)
            x principal point (int)
            y principal point (int)
        """
        return shps.camera.get_intrinsic_parameters() 

    def generate_extrinsic_parameters(self):
        return shps.camera.get_extrinsic_parameters()
    
    def set_light(self, location=(4,1,6)):
        shps.scene.set_light(location=location)

    def _clean_scene(self):
        shps.scene.clean_scene()

    def set_focal_length(self, mm: float):
        """Set the focal lenght of the camera.

        This function will overwrite the field of view value
        
        Args:
            mm (float): focal lenght in milimeters
        """
        shps.camera.set_focal_length(mm)

    def set_fov(self, radians: float):
        """Sets the fild of view of the camera

        This function will overwrite the focal lenght
        
        Args:
            radians (flot): in radians
        """
        shps.camera.set_fov(radians)

    def set_near(self, meters: float):
        shps.camera.set_near(meters)

    def set_far(self, meters: float):
        shps.camera.set_far(meters)

    def set_image_resolution(self, width_px: int, height_px: int):
        shps.render.set_image_resolution(width_px, height_px)

    def render(self,
               folder_path: str,
               file_id: int=1,
               camera_location: tuple=None,
               camera_rotation: tuple=None):
        """Renders the environment.

        Args:
            camera_location (tuple): (tx, ty, tx) tuple of floats in meters
            camera_rotation (tuple): (yaw, pitch, roll) tuple of floats in radians
        """
        if camera_location:
            shps.camera.set_location(*camera_location)

        if camera_rotation:
            shps.camera.set_rotation(*camera_rotation)

        shps.render.set_image_path(folder_path, file_id)
        shps.render.render()

    def _get_collision_radius(self, shape):
        if 'SPHERE' in shape._name:
            return shape._radius
        elif 'CYLINDER' in shape._name:
            #return max(self._radius, max(self._dims))
            return shape._radius
        elif 'CONE' in shape._name:
            return max([shape._radius1, shape._radius2])
        else:
            return max(shape._dims)

    def check_collisions(self, x, y, collision_radius):
        """Checks for collisions.
        
        Checks if the position x,y collide with any obj in objs with a
        collision_raidus of collision_radius.

        Args:
            x (float): x position
            y (float): y position
            collision_radius (float): the area around x and y

        Returns:
            True if there are no collisions, else False
        """
        eps = 0.2
        for shp in self._shapes:
            shp_collision_radius = self._get_collision_radius(shp)
            if (shp._location[0] - x)**2 + (shp._location[1] - y)**2 <= \
                    (shp_collision_radius + collision_radius + eps)**2:
                return False
        else:
            return True

    def add_sphere(self,
                   radius: Optional[float] = None,
                   location: Optional[Tuple[float, float]] = None,
                   color: Optional[Tuple[float, float, float]] = None) -> bool:
        """Adds a ico_sphere in the scene.

        If an arg is None, it will given a scene-consistent random value (e.g. if location is
        None the object will be placed somewhere where does not traverse objects or walls)

        Args: 
            radius (float): radius of sphere in meters
            location (tuple): (x,y) or (x,y,z). If z is not specified the object will be on
                the floor
            color (tuple): (r,g,b) tuple of floats between 0,1

        Returns:
            bool: If the operation was successfull in case of random elements, mainly 
                regarding collision checks
        """
        success, radius, location, color = self._add_shape(radius, location, color)

        if not success:
            return False
        else:
            if len(location) == 2:
                location.append(radius)

            s = Sphere(self._next_id(),radius=radius, location=location, color=color)
            self._shapes.append(s)

            return True

    def add_cuboid(self,
                   dims: Optional[tuple]=None,
                   location: Optional[tuple]=None,
                   rotation: tuple=(0,0,0),
                   color: Optional[tuple]=None) -> bool:
        """Adds a cuboid in the scene.

        If an arg is None, it will given a scene-consistent random value (e.g. if location is
        None the object will be placed somewhere where does not traverse objects or walls).
        Collision check will be made on an un-rotated cuboid

        Args: 
            radius (float): radius of sphere in meters
            location (tuple): (x,y) or (x,y,z). If z is not specified the object will be on
                the floor
            rotation (tuple): (x,y,z) rotation angles in gradians. Euler angles on XYZ
            color (tuple): (r,g,b) tuple of floats between 0,1

        Returns:
            bool: If the operation was successfull in case of random elements, mainly 
                regarding collision checks
        """
        eps = 0.5
        max_dim = max(dims) if dims else None
        success, max_dim, location, color = self._add_shape(max_dim, location, color)

        if not success:
            return False
        else:
            if not dims:
                w = random.uniform(eps, max_dim)
                l = random.uniform(eps, max_dim)
                h = random.uniform(eps, max_dim)
                dims = (w,l,h)

            if len(location) == 2:
                location.append(dims[-1]/2)

            c = Cuboid(self._next_id(),
                       dims=dims,
                       location=location,
                       rotation=rotation,
                       color=color)
            self._shapes.append(c)

            return True

    def add_cylinder(self,
                     radius: Optional[float]=None,
                     height: Optional[float]=None,
                     location: Optional[tuple]=None,
                     color: Optional[tuple]=None):
        success, radius, location, color = self._add_shape(radius, location, color)

        if not success:
            return False
        else:
            if not height:
                height = random.uniform(0.5, self._dims[-1]/2)

            if len(location) == 2:
                location.append(height/2)

            c = Cylinder(self._next_id(),
                         radius=radius,
                         height=height,
                         location=location,
                         color=color)
            self._shapes.append(c)
            return True

    def add_cone(self,
                 radius1: Optional[float]=None,
                 radius2: Optional[float]=None,
                 height: Optional[float]=None,
                 location: Optional[tuple]=None,
                 color: Optional[tuple]=None):
        if not radius1 and not radius2:
            max_radius = None
        else:
            if not radius1:
                max_radius = radius2
            elif not radius2:
                max_radius = radius1
            else:
                max_radius = max([radius1, radius2])

        success, max_radius, location, color = self._add_shape(max_radius, location, color)

        if not success:
            return False
        else:
            if not height:
                height = random.uniform(0.5, self._dims[-1]/2)

            if len(location) == 2:
                location.append(height/2)

            if not radius1:
                radius1 = max_radius
            if not radius2:
                radius2 = 0

            c = Cone(self._next_id(),
                     radius1=radius1,
                     radius2=radius2,
                     height=height,
                     location=location,
                     color=color)
            self._shapes.append(c)
            return True

    def add_capsule(self):
        raise NotImplementedError

    def _add_shape(self, max_dim: float, location: tuple, color: tuple) -> tuple:
        """Generic method to generate random values for None arguments.
        
        Args:
            max_dim (float): max dim of shape to check for collisions only if location
                or max_dim is None
            location (tuple): (x,y,z) or (x,y) tuple of floats in meters
            color (tuple): (r,g,b) tuple of floats in 0..1
            
        Returns:
            bool: If the method was successful or not
            tuple: location (x,y,z)
            tuple: color (r,g,b)
        """
        eps = 2e-1
        for _ in range(20):
            if not max_dim: 
                tmp_max_dim = random.uniform(eps, 1)*self._dims[-1]/2
            else:
                tmp_max_dim = max_dim

            if not location:
                x_lim = (self._dims[0]-eps)/2 - tmp_max_dim
                x = (random.uniform(-1, 1)) * x_lim

                y_lim = (self._dims[1]-eps)/2 - tmp_max_dim
                y = (random.uniform(-1, 1)) * y_lim

                tmp_location = [x, y]
            else:
                tmp_location = location

            if not max_dim or not location:
                # Collision check
                if self.check_collisions(*tmp_location[:2], tmp_max_dim):
                    break
            else:
                break
        else:
            return False, None, None, None

        location = tmp_location
        max_dim = tmp_max_dim

        if not color: 
            r = random.uniform(0,1)
            g = random.uniform(0,1)
            b = random.uniform(0,1)
            color = (r, g, b) 

        return True, max_dim, location, color

    def close(self):
        """Closes Blender."""
        shps.scene.close()

    def set_renderer(self,
                     render_type: str='Cycles',
                     gpu: Optional[bool]=None,
                     image_resolution: tuple=(600, 600),
                     samples: Optional[int]=256,
                     max_bouces: Optional[int]=4,
                     tile_dim: Optional[Tuple[int, int]]=(256, 256)):
        """Sets the render in blender.

        For more information see shps.render.set_config

        Args:
            render_type (str): 'Cycles' or 'Eevee'
            gpu (bool): Use or not gpu. Only valid for Cycles
            image_resolution (tuple): tuple of ints for resolution for width and height
            samples (int): Number of samples per image per pixel
            max_bouces (int): number or bouces per ray
            tile_dim (tuple): Dimensions of tiles when rendering
        """
        shps.render.set_render_config(render=render_type,
                                      image_resolution=image_resolution,
                                      gpu=gpu,
                                      samples=samples,
                                      max_bounces=max_bouces,
                                      tile_dim=tile_dim)

    def _next_id(self):
        return len(self._shapes)

    @property
    def use_walls(self):
        return self._use_walls

    @use_walls.setter
    def use_walls(self, val):
        assert type(val) == bool

        if val != self._use_walls:
            self._use_walls = val
            if val:
                # create walls variable
                pass
            else:
                # remove walls variable
                del walls 
