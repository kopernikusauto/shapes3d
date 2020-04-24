""" Defines an example to create a dataset of an environment """

import argparse
import os
import random
from collections import namedtuple
from pdb import set_trace
from PIL import Image
from shapes3d.worlds import SimpleWorld
import math
from tqdm import tqdm
import bpy
import sys

ENV_DIM = 20
MAX_NUM_OBJS = 15
MIN_NUM_OBJS = 7
FOV = 45
PLANE_COLOR = [1, 1, 1]
TYPES = ['sphere', 'cuboid', 'cylinder']

def generate_dataset(destination_folder,
                     num_total_imgs,
                     num_total_envs,
                     num_eval_envs,
                     width,
                     height):

    train, val = [], []

    # Check if folder exists
    check_folder_or_create(destination_folder)

    # Create general environment
    env = SimpleWorld(dims=[ENV_DIM, ENV_DIM, 2], use_walls=True, use_gpu=True)
    env.set_renderer(render_type='Cycles',
                     gpu=True,
                     image_resolution=(600, 600),
                     samples=256,
                     max_bouces=4,
                     tile_dim=(256, 256))

    # Get instrinsic and extrinsic matrices
    intrinsic = [str(i) for i in env.generate_intrinsic_parameters()]
    intrinsic = [" ".join(intrinsic), "fx fy cx cy"]
    save_in_txt(os.path.join(destination_folder, "intrinsic_matrix.txt"), intrinsic, "\n")

    with tqdm(total=num_total_imgs) as pbar:
        for env_num in range(num_total_envs):
            env.reset()
            epsilon = 0.1
            folder = os.path.join(destination_folder, str(env_num))
            check_folder_or_create(folder)

            check_folder_or_create(os.path.join(destination_folder, str(env_num)))

            # Create objects
            # Choose number of objects
            num_obj = random.randint(MIN_NUM_OBJS, MAX_NUM_OBJS)
            for _ in range(num_obj):
                # Choose random type
                obj_type = random.choice(TYPES)

                if obj_type == "cuboid":
                    env.add_cuboid()
                elif obj_type == "sphere":
                    env.add_sphere()
                elif obj_type == "capsule":
                    env.add_capsule()
                elif obj_type == "cylinder":
                    env.add_cylinder()

            # Choose a random pose and orientation for camera
            for img_num in range(num_total_imgs//num_total_envs):
                while True:
                    ref = random.choice(env._shapes)
                    x, y, _ = ref._location[:]
                
                    range_dis = ENV_DIM/2 - max(abs(x), abs(y))

                    angle = random.uniform(0, 2*math.pi)
                    distance = random.uniform(4, range_dis - epsilon)

                    dx1 = random.uniform(-1, 1)
                    dy1 = random.uniform(-1, 1)
                    dz1 = 0
                    dyaw1 = 0

                    x1 = x + math.cos(angle)*distance + dx1
                    y1 = y + math.sin(angle)*distance + dy1

                    if max(abs(x1),abs(y1)) > ENV_DIM/2 - 1:
                        continue

                    # Check if valid 
                    if not env.check_collisions(x1, y1, 1):
                        continue
                    
                    # Generate second position
                    for _ in range(20):
                        dx2 = random.uniform(-1, 1)
                        dy2 = random.uniform(-1, 1)
                        dz2 = 0

                        dyaw2 = random.uniform(-1, 1) * math.pi/8

                        if env.check_collisions(x1 + dx2, y1 + dy2, 1):
                            break
                    else:
                        continue
                    break
                
                # Get base yaw
                yaw = math.pi/2 + angle

                # render from x1,y2 and from x1+dx2 and y1+dy1
                tra1 = (x1, y1, 1)
                tra2 = (x1 + dx2, y1 + dy2, 1)
                rot1 = (math.pi/2, 0, yaw + dyaw1)
                rot2 = (math.pi/2, 0, yaw + dyaw2)

                env.render(folder, 2*img_num+1,
                           camera_location=tra1,
                           camera_rotation=rot1)
                env.render(folder, 2*img_num+2,
                           camera_location=tra2,
                           camera_rotation=rot2)

                extrinsic1 = [str(i) for i in tra1 + rot1]
                extrinsic2 = [str(i) for i in tra2 + rot2]

                extrinsic1 = [" ".join(extrinsic1), "rx ry rz tx ty tz"]
                extrinsic2 = [" ".join(extrinsic2), "rx ry rz tx ty tz"]

                save_in_txt(
                    os.path.join(folder, "Extrinsic_{:04d}.txt".format(2*img_num+1)),
                    extrinsic1, "\n")
                save_in_txt(
                    os.path.join(folder, "Extrinsic_{:04d}.txt".format(2*img_num+2)),
                    extrinsic2, "\n")

                if env_num < num_eval_envs:
                    val.append((str(env_num), str(2*img_num+1)))
                    val.append((str(env_num), str(2*img_num+2)))
                else:
                    train.append((str(env_num), str(2*img_num+1)))
                    train.append((str(env_num), str(2*img_num+2)))

                pbar.update(1)

    env.close()
    train = [' '.join(x) for x in train]
    val = [' '.join(x) for x in val]

    save_in_txt(os.path.join(destination_folder, "train.txt"), train, '\n')
    save_in_txt(os.path.join(destination_folder, "val.txt"), val, '\n')

def save_in_txt(destination, array, char=' '):
    """ saves array elements in destination with spaces between values """
    if os.path.exists(destination):
        os.remove(destination)
    with open(destination, 'w') as txt:
        txt.write(char.join([str(i) for i in array]))

def check_folder_or_create(folder):
    """ Checks if the folder exits, if not it creates it """
    if not os.path.exists(folder):
        print("Creating folder %s" % folder)
        os.makedirs(folder)

if __name__ == '__main__':
    # get params: number of images, number of envs and folder
    parser = argparse.ArgumentParser(
        description="Arguments to generate a dataset using this environment")

    parser.add_argument('-f', '--destination', type=str, default="dataset_generated",
                        help="Folder destination for the dataset files")
    parser.add_argument('-i', '--num_total_imgs', type=int, default=1000,
                        help="Number of images to generate in total")
    parser.add_argument('-e', '--num_total_envs', type=int, default=10,
                        help="Number of environments to generate")
    parser.add_argument('--num_eval_envs', type=int, default=1,
                        help="Number of environments used in evaluation")
    parser.add_argument('--width', type=int, default=300,
                        help="Width in pixels of the images")
    parser.add_argument('--height', type=int, default=300,
                        help="Width in pixels of the images")

    argv = sys.argv
    if " -- " in argv:
        argv = argv[argv.index(" -- ") + 1:]
    else:
        argv = ""

    args = parser.parse_args(argv)

    generate_dataset(args.destination, args.num_total_imgs, args.num_total_envs, args.num_eval_envs, width=args.width, height=args.height)
