import os
import glob
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
from utils import LabelClass


def get_file_path_newspaper(file_path):
    no_extension = os.path.splitext(file_path)[0]
    newspaper_str = os.path.basename(no_extension).split('_')[0]
    return newspaper_str


def get_file_path_date(file_path):
    no_extension = os.path.splitext(file_path)[0]
    date_str = os.path.basename(no_extension).split('_')[1]
    return date_str


def get_file_path_newspaper_and_date(file_path):
    no_extension = os.path.splitext(file_path)[0]
    filename = os.path.basename(no_extension)
    return filename


def sort_by_filename(l):
    return sorted(
        l,
        key=lambda fname: get_file_path_newspaper_and_date(fname),
        reverse=True)


class CoversDataset(object):
    def __init__(self, root):
        self.images = sort_by_filename(
            glob.glob(os.path.join(root, 'covers', '*.jpeg')))
        self.labels = sort_by_filename(
            glob.glob(os.path.join(root, 'labels', '*.xml')))

    def __getitem__(self, idx):
        img_path = self.images[idx]
        label_path = self.labels[idx]

        assert get_file_path_newspaper_and_date(img_path) == get_file_path_newspaper_and_date(label_path)

        img = Image.open(img_path).convert("RGB")

        labels = []
        boxes = []
        areas = []
        tree = ET.parse(label_path)
        for obj in tree.findall('object'):
            obj_name = obj.find('name').text

            label_class = LabelClass[obj_name.upper()]
            labels.append(label_class.id)
            box = obj.find('bndbox')
            xmin, ymin = int(box.find('xmin').text), int(box.find('ymin').text)
            xmax, ymax = int(box.find('xmax').text), int(box.find('ymax').text)
            boxes.append([xmin, ymin, xmax, ymax])
            areas.append((xmax - xmin) * (ymax - ymin))

        labels = np.array(labels, dtype=np.int64)
        boxes = np.array(boxes, dtype=np.float32)
        areas = np.array(areas, dtype=np.float32)
        image_id = np.array([idx])
        iscrowd = np.zeros((boxes.shape[0], ), dtype=np.int64)

        target = {}
        target['boxes'] = boxes
        target['labels'] = labels
        target['area'] = areas
        target["image_id"] = image_id
        target["iscrowd"] = iscrowd
        target["image_width"] = int(tree.find('size').find('width').text)
        target['image_height'] = int(tree.find('size').find('height').text)

        return img, target

    def __len__(self):
        return len(self.images)
