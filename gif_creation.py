import rasterio
import imageio
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import numpy as np
from skimage import exposure
import glob
import cv2
import os



def add_basemap_names(dirname):

    for f in dirname:
        print(f.split(".")[1])
        img = Image.open(f)
        size = img.size
        font_size = int((size[0]+size[1])/50)
        font = ImageFont.truetype("Microsoft Sans Serif.ttf", font_size)
        dest = Image.new("RGB", (size[0], size[1] + font_size*2), "White")
        dest.paste(img, (0,0))
        ImageDraw.Draw(dest).text((int(font_size/4), size[1]), f.split(".")[1].split("/")[4], "Black", font)
        dest.close()


def geotiff_to_video(geotiff_filenames, video_filename, bands, fps):
    writer = imageio.get_writer(video_filename, format='FFMPEG', mode='I', fps=fps)
    for name in geotiff_filenames:
        with rasterio.open(name) as src:
            data = src.read(bands)  # Read the specified bands
            data = np.moveaxis(data, 0, -1)  # move the first axis (bands) to the last
            data = data / 65535  # Normalize to range 0-1 for equalize_hist

            # Perform a histogram equalization
            data = exposure.equalize_hist(data)

            # Scale back to 0-255 for video writer
            data = (data * 255).astype(np.uint8)

            filename = os.path.basename(name)
            cv2.putText(data, filename, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            writer.append_data(data)
    writer.close()



def main():
    folders = glob.glob('.\\JoCoAOI\\*')
    for folder in folders:
        print(folder)
        geotiff_filenames = glob.glob(folder+"/*/*/*/*mosaic_merge_clip.tif")
        if len(geotiff_filenames) == 0:
            geotiff_filenames = glob.glob(folder + "/*/*/*/*mosaic_clip.tif")

        output = folder + ".mp4"
        geotiff_to_video(geotiff_filenames, output, bands=[3,2,4], fps=2)

main()