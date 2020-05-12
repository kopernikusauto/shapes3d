from shapes3d.worlds import SimpleWorld

if __name__ == '__main__':
    world = SimpleWorld(dims=(10,10,2), use_walls=True, use_gpu=True)

    world.add_sphere()
    world.add_sphere()
    world.add_sphere()
    world.add_cuboid()
    world.add_cuboid()
    world.add_cuboid()
    world.add_cylinder()
    world.add_cylinder()
    world.add_cylinder()

    world.set_focal_length(40)
    world.set_image_resolution(600, 600)

    world.render("./")
    world.close()
