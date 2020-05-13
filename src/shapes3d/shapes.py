"""Implements simple classes to add geometric 3d shapes into blender scene conveniently."""

import bpy
from typing import Optional, Tuple

SUBDIVS = 5
SPHERE = "Shapes3D_SPHERE_"
CYLINDER = "Shapes3D_CYLINDER_"
CONE = "Shapes3D_CONE_"
PLANE = "Shapes3D-PLANE_"
CUBOID = "Shapes3D-CUBOID_"


class Shape:
    def __init__(self, id, name, location, color):
        self._id = id
        self._name = name + str(id)

        assert len(color) == 3

        self._color = tuple(color) + (1,)
        self._location = location
        self._render()

    def _render(self):
        bpy.context.object.name = self._name
        mat = bpy.data.materials.new(name='Material_%s' % self._name)
        mat.diffuse_color = self._color
        bpy.context.object.data.materials.append(mat)


class Sphere(Shape):
    def __init__(self, id=None, radius=1, location=(0, 0, 0), color=(1,1,1)):
        self._radius = radius
        super(Sphere, self).__init__(id, SPHERE, location, color)

    def _render(self):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=SUBDIVS,
            radius=self._radius,
            location=self._location,
        )
        super(Sphere, self)._render()


class Cylinder(Shape):
    def __init__(self, id=None, radius=1, height=1, location=(0,0,0), color=(1,1,1)):
        self._radius = radius
        self._height = height
        super(Cylinder, self).__init__(id, CYLINDER, location, color)

    def _render(self):
        bpy.ops.mesh.primitive_cylinder_add(
            depth=self._height,
            radius=self._radius,
            location=self._location,
        )
        super(Cylinder, self)._render()


class Cone(Shape):
    def __init__(self, id=None, radius1=1, radius2=0, height=1, location=(0,0,0), color=(1,1,1)):
        self._radius1 = radius1
        self._radius2 = radius2
        self._height = height
        super(Cone, self).__init__(id, CONE, location, color)

    def _render(self):
        bpy.ops.mesh.primitive_cone_add(
            depth=self._height,
            radius1=self._radius1,
            radius2=self._radius2,
            location=self._location,
        )
        super(Cone, self)._render()


class Cuboid(Shape):
    """ Only Rectangular cubioids """
    def __init__(self, id=None, dims=(1, 1, 1), location=(0, 0, 0),
                 rotation=(0, 0, 0), color=(1, 1, 1)):
        self._dims = dims
        self._rotation = rotation

        super(Cuboid, self).__init__(id, CUBOID, location, color)

    def _render(self):
        bpy.ops.mesh.primitive_cube_add(
            size=1, location=self._location)
        bpy.ops.transform.resize(value=self._dims)
        for axis, rad in zip("XYZ", self._rotation):
            bpy.ops.transform.rotate(value=rad, orient_axis=axis)
        super(Cuboid, self)._render()


class Plane(Shape):
    def __init__(self,
                 id: Optional[int] = None,
                 dims: Tuple[float, float] = (1,1),
                 location: Tuple[float, float, float] = (0,0,0),
                 rotation: Tuple[float, float, float] = (0,0,0),
                 color: Tuple[float, float, float] = (1, 1, 1)) -> None:
        """Location, Dims and Rotation are applied in that order."""
        self._dims = None
        self._rotation = rotation

        self.dims = dims
        super(Plane, self).__init__(id, PLANE, location, color)

    def _render(self):
        bpy.ops.mesh.primitive_plane_add(
            size=1, location=self._location)
        dims = self.dims + (1,)
        bpy.ops.transform.resize(value=dims)
        for axis, rad in zip("XYZ", self._rotation):
            bpy.ops.transform.rotate(value=rad, orient_axis=axis)
        super(Plane, self)._render()

    @property
    def dims(self):
        return self._dims

    @dims.setter
    def dims(self, val):
        if val != self._dims:
            assert isinstance(val, (int, float, tuple, list))
            if isinstance(val, (tuple, list)):
                assert len(val) == 2
                val = tuple(val)
            else:
                val = (val, val)

            self._dims = val
