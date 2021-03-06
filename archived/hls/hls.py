import os
import cv2
import numpy as np
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed


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


def get_ls(image_name):
    image = cv2.imread(image_name)

    # 图像归一化，且转换为浮点型
    hlsImg = image.astype(np.float32)
    hlsImg = hlsImg / 255.0
    # 颜色空间转换 BGR转为HLS
    hlsImg = cv2.cvtColor(hlsImg, cv2.COLOR_BGR2HLS)
    # 1.亮度
    l = np.average(hlsImg[:,:,1])
    # 2.饱和度
    s = np.average(hlsImg[:,:,2])

    return l, s


def hls_trans(image_name, depth, save_path, HLS_L=0.9, HLS_S=0.5):
    image = cv2.imread(image_name)

    # 图像归一化，且转换为浮点型
    hlsImg = image.astype(np.float32)
    hlsImg = hlsImg / 255.0
    # 颜色空间转换 BGR转为HLS
    hlsImg = cv2.cvtColor(hlsImg, cv2.COLOR_BGR2HLS)
    # 1.调整亮度, 2.将hlsCopy[:, :, 1]和hlsCopy[:, :, 2]中大于1的全部截取
    # hlsImg[:, :, 1] = (1.0 + HLS_L) * hlsImg[:, :, 1]
    l = np.average(hlsImg[:,:,1])
    hlsImg[:, :, 1] = HLS_L / l * hlsImg[:, :, 1]
    hlsImg[:, :, 1][hlsImg[:, :, 1] > 1] = 1
    # 2.调整饱和度
    # hlsImg[:, :, 2] = (1.0 + HLS_S) * hlsImg[:, :, 2]
    s = np.average(hlsImg[:,:,2])
    hlsImg[:, :, 2] = HLS_S / s * hlsImg[:, :, 2]
    hlsImg[:, :, 2][hlsImg[:, :, 2] > 1] = 1
    # HLS2BGR
    hlsImg = cv2.cvtColor(hlsImg, cv2.COLOR_HLS2BGR)
    # 转换为8位unsigned char
    hlsImg = hlsImg * 255
    image = hlsImg.astype(np.uint8)
    
    tokens = image_name.rsplit(os.sep, depth+1)
    image_name_out = os.path.join(save_path, *tokens[1:])
    os.makedirs(os.path.dirname(image_name_out), exist_ok=True)

    cv2.imwrite(image_name_out, image)


def batch_hls_trans(image_names, depth, save_path, HLS_L=0.20, HLS_S=0.8):
    for image_name in image_names:
        hls_trans(image_name, depth, save_path, HLS_L, HLS_S)


def process(image_path, depth, save_path, HLS_L=0.8, HLS_S=0.8):
    image_names = scan_files(image_path, postfix=".jpg")
    print("total of {} images to process".format(len(image_names)))

    executor = ProcessPoolExecutor(max_workers=cpu_count() - 2)
    tasks = []

    batch_size = 1000
    for i in range(0, len(image_names), batch_size):
        batch = image_names[i : i+batch_size]
        tasks.append(executor.submit(batch_hls_trans, batch, depth, save_path, HLS_L, HLS_S))

    job_count = len(tasks)
    for future in as_completed(tasks):
        # result = future.result()  # get the returning result from calling fuction
        job_count -= 1
        print("One Job Done, Remaining Job Count: {}".format(job_count))



if __name__ == "__main__":
    # image_path = "/home/hdd0/Develop/tct/hls/test_data/zhengzhou_refined_299"
    # save_path = "/home/hdd0/Develop/tct/hls/test_data/zhengzhou_refined_299_hls"
    # # hls_trans(image_name, 1, save_path)
    # process(image_path, 1, save_path)

    src_dir = "/home/hdd0/Develop/tct/hls/samples"
    src_imgs = scan_files(src_dir, postfix=".jpg")

    for src_img in src_imgs:
        # src_img = "/home/hdd0/Develop/tct/conference/xception/batch6.1_hls_half_train/20181205_BATCH_6.1/HSIL_B/2017-09-07-08_47_59_x13097_y7826_w167_h446.jpg"
        print(src_img, get_ls(src_img))


        save_path = "/home/hdd0/Develop/tct/hls"
        hls_trans(src_img, 0, save_path)