import shapes3d as shps
import math

env = shps.worlds.SimpleWorld(use_gpu=True)
env.add_sphere()
env.add_cuboid()
env.add_cylinder()
env.add_sphere()
env.add_cuboid()
env.add_cylinder()
env.add_sphere()
env.add_cuboid()
env.add_cylinder()

distance = 6
for i in range(360):
    x = math.cos(i*math.pi/180)*distance
    y = math.sin(i*math.pi/180)*distance
    angle = math.pi/2 + i*math.pi/180

    env.render("examples/turning/", i,
               camera_location=(x, y, 2),
               camera_rotation=(math.pi/2 - math.pi/8, 0, angle))
