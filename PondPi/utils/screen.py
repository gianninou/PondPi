
from waveshare_epd import epd2in13_V2
from PIL import Image, ImageDraw, ImageFont

font20 = ImageFont.truetype('Font.ttc', 20)

epd = epd2in13_V2.EPD()

BLACK = 0
WHITE = 255


def update_screen(self):
    epd.init(epd.FULL_UPDATE)
    time_image = Image.new('1', (epd.height, epd.width), 255)
    time_draw = ImageDraw.Draw(time_image)
    epd.displayPartBaseImage(epd.getbuffer(time_image))
    epd.init(epd.PART_UPDATE)

    time_draw.rectangle((0, 0, 240, 120), fill=WHITE)
    time_draw.text((0, 10), "Temp1: {}°".format(self.temp1), font=font20, fill=BLACK)
    time_draw.text((125, 10), "Air: {}°".format(self.temp_air), font=font20, fill=BLACK)

    time_draw.text((0, 35), "Temp2: {}°".format(self.temp2), font=font20, fill=BLACK)
    time_draw.text((125, 35), "Hum: {}%".format(self.moisture), font=font20, fill=BLACK)

    time_draw.line([(0, 62), (240, 62)], fill=0, width=1)

    time_draw.text((0, 65), "Pump 1: {}  ".format(("ON" if self.pump1 else "OFF")), font=font20, fill=BLACK)
    time_draw.text((125, 65), "UV: {}  ".format(("ON" if self.UV else "OFF")), font=font20, fill=BLACK)

    time_draw.text((0, 90), "Pump 2: {}  ".format(("ON" if self.pump2 else "OFF")), font=font20, fill=BLACK)
    time_draw.text((125, 90), "Water: {}".format(("HIGH" if self.water_level else "LOW")), font=font20, fill=BLACK)
    if not self.water_level:
        time_draw.rectangle([(185, 88), (240, 115)], width=3)
    epd.displayPartial(epd.getbuffer(time_image))
