import os
import time
import datetime
from picamera import PiCamera
import yaml
import imageio
import re
yaml_file = open("conf/conf.yml", 'r')
yaml_content = yaml.safe_load(yaml_file)


LOCAL_FOLDER = yaml_content.get("camera").get("local_folder")
RESOLUTION = (int(yaml_content.get("camera").get("resolution").split('x')[0]),
              int(yaml_content.get("camera").get("resolution").split('x')[1]))

IMAGE_NAME = 'picture_{}.jpg'


class Camera:

    def capture():
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
        name = IMAGE_NAME.format(timestamp)
        camera = PiCamera()
        camera.resolution = RESOLUTION
        camera.start_preview()
        # Camera warm-up time
        time.sleep(2)
        camera.capture(os.path.join(LOCAL_FOLDER, name))
        return name

    def generate_gif(date):
        images = []
        filenames = [os.path.join(LOCAL_FOLDER, f) for f in os.listdir(LOCAL_FOLDER) if re.match(r'picture.*{}.*'.format(date), f)]
        if len(filenames) == 0:
            print("No picture found for {}".format(date))
            return None
        for filename in filenames:
            images.append(imageio.imread(filename))
        gif_name = "day_{}.gif".format(date)
        imageio.mimsave(os.path.join(LOCAL_FOLDER, gif_name), images)
        return gif_name
