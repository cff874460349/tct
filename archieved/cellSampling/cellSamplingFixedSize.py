# coding=utf-8
# for marked region of size no bigger than 600x600, clip a fixed-size window (600x600)
# for those bigger than 600x600, first pad it with 100, slide through the broadened region and clip 600x600 windows, with step of 200

import os
import openslide
import scipy.misc
from xml.dom.minidom import parse
import xml.dom.minidom


def scan_files(directory, prefix=None, postfix=None):
    files_list = []

    for root, sub_dirs, files in os.walk(directory):
        for special_file in files:
            if postfix:
                if special_file.endswith(postfix):
                    files_list.append(os.path.join(root, special_file))
            elif prefix:
                if special_file.startswith(prefix):
                    files_list.append(os.path.join(root, special_file))
            else:
                files_list.append(os.path.join(root, special_file))

    return files_list


colors = {"#000000": 0,
               "#aa0000": 0,
               "#aa007f": 0,
               "#aa00ff": 0,
               "#ff0000": 0,
               "#005500": 0,
               "#00557f": 0,
               "#0055ff": 0,
               "#aa5500": 0,
               "#aa557f": 0,
               "#aa55ff": 0,
               "#ff5500": 0,
               "#ff557f": 0,
               "#ff55ff": 0,
               "#00aa00": 0,
               "#00aa7f": 0,
               "#00aaff": 0,
               "#55aa00": 0,
               "#55aa7f": 0}


def choose_xy(x_coords, y_coords, size):
    # get mininum-area-bounding-rectangle
    x_min = min(x_coords)
    x_max = max(x_coords)
    y_min = min(y_coords)
    y_max = max(y_coords)

    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2
    x_span = x_max - x_min
    y_span = y_max - y_min

    # print(x_center, y_center, x_span, y_span)
    points_xy = []

    if x_span <= size and y_span <= size:
        x = x_center - size / 2
        y = y_center - size / 2
        points_xy.append([x, y])
    # if marked region is too big, slide through x & y direction, 200 each step
    else:
        padding = 100
        pace = 200
        x = x_min - padding
        y = y_min - padding
        while x + size <= x_max + padding:
            # take a block
            points_xy.append([x, y])
            curr_y = y
            while y + size <= y_max + padding:
                y += pace
                # take a block
                points_xy.append([x, y])
            y = curr_y
            x += pace

        while y + size <= y_max + padding:
            # take a block
            points_xy.append([x, y])
            y += pace

    return points_xy


def cellSampling(files_list, save_path, size):
    right = 0
    wrong = 0
    for xml_file in files_list:
        # from .xml filename, get .til filename
        filename = os.path.splitext(xml_file)[0]
        filetype = ".tif"

        # open .tif file
        tif_file = filename + filetype
        try:
            slide = openslide.OpenSlide(tif_file)

            # open .xml file
            DOMTree = xml.dom.minidom.parse(xml_file)
            collection = DOMTree.documentElement
            annotations = collection.getElementsByTagName("Annotation")

            for annotation in annotations:
                if annotation.getAttribute("Color") in colors:
                    coordinates = annotation.getElementsByTagName("Coordinate")

                    # read (x, y) coordinates
                    x_coords = []
                    y_coords = []
                    for coordinate in coordinates:
                        x_coords.append(float(coordinate.getAttribute("X")))
                        y_coords.append(float(coordinate.getAttribute("Y")))

                    # stores the (x, y) coordinates for read_region()
                    points_xy = choose_xy(x_coords, y_coords, size)
                    for point_xy in points_xy:
                        cell = slide.read_region((int(point_xy[0]), int(point_xy[1])), 0, (size, size))
                        cell = cell.convert("RGB")
                        scipy.misc.imsave(save_path + "\\" + annotation.getAttribute("Color") + "\\" + str(right).zfill(6) + "_" + filename[3:].replace("\\", "_") + "_" + annotation.getAttribute("Name") + ".jpeg", cell)
                        right += 1

                else:
                    wrong += 1

            slide.close()

        except:
            print(filename + " cannot be processed")

    print("# images taken: " + str(right))
    print("# wrong color: " + str(wrong))


if __name__ == "__main__":
    file_path = "C:\\liyu\\files\\tiff"
    files_list = scan_files(file_path, postfix=".xml")

    save_path = "C:\\liyu\\files\\tiff\\0002cells"
    cellSampling(files_list, save_path, 600)


