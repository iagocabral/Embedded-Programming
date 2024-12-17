import board
import busio
import adafruit_ssd1306
from time import sleep

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

stats1 = 'PARADO'
stats2 = 'PARADO'
temp1 = '20.5'
temp2 = '20.5'

def up_temp(temperatura1,temperatura2): 
    global temp1, temp2
    temp1 = temperatura1
    temp2 = temperatura2
    sleep(0.1)
    show_display()

def up_status(status1, elevador): 
    global stats1, stats2
    if elevador == 0:
        stats1 = status1
    if elevador == 1:
        stats2 = status1
    show_display()


def show_display():
    i2c = busio.I2C(board.SCL, board.SDA)
    disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)

    disp.fill(0)
    disp.show()

    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))

    WIDTH = 128
    HEIGHT = 64 
    BORDER = 5

    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)
    
    font = ImageFont.load_default()
    draw.text((0, 0), 'Elevador 1', font=font, fill=255)
    draw.text((0, 10), 'Temp:' + temp1, font=font, fill=255)
    draw.text((0, 20),  stats1, font=font, fill=255)
    draw.text((0, 35), 'Elevador 2', font=font, fill=255)
    draw.text((0, 45), 'Temp:' + temp2, font=font, fill=255)
    draw.text((0, 55),  stats2, font=font, fill=255)
    disp.image(image)
    disp.show()
