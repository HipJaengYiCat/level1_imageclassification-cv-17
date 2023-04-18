import argparse
import glob
import json
import multiprocessing
import os
import random
import re
from importlib import import_module
from pathlib import Path
from tqdm import tqdm

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision import transforms
from torchvision.transforms import Resize, ToTensor, Normalize
import torchvision.transforms.functional as F
from PIL import Image
import seaborn as sns

from dataset import MaskBaseDataset, MaskPreprocessDataset# dataset.py
from dataset import TestDataset
from loss import create_criterion # loss.py
from f1score import get_F1_Score # f1score.py
from submission import submission # submission.py
from inference import inference # inference.py
import wandb


from dataset import MaskBaseDataset # dataset.py
from dataset import TestDataset
from loss import create_criterion # loss.py
from f1score import get_F1_Score # f1score.py
from submission import submission # submission.py
from inference import inference # inference.py
import wandb

class RandomGaussianBlur(object):
    def __init__(self, kernel_size):
        self.kernel_size = kernel_size
        
    def __call__(self, img):
        if np.random.rand() < 0.5:
            return img
        else:
            return F.gaussian_blur(img, kernel_size=self.kernel_size, sigma=(0.1, 2.0))    


def random_transform(image):
    scale = (0.005, 0.025)
    ratio = (0.3, 3.3)
    transform = transforms.Compose([transforms.ToTensor(),
                                    transforms.RandomHorizontalFlip(p=0.6),
                                    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                                    transforms.RandomErasing(p=0.7, scale=scale, ratio=ratio),
                                    transforms.RandomErasing(p=0.5, scale=scale, ratio=ratio),
                                    RandomGaussianBlur(kernel_size=3),
                                    transforms.RandomRotation(5),
                                    transforms.ToPILImage()
                                   ])
    return transform(image)    


def AddAugmentation(label_paths,idx,aug_size, dir_name):
    idx2label = ['mask']*6+['incorrect']*6+['normal']*6
#     os.makedirs(dir_name.exist_ok = True)
    idx = int(idx)
    aug_size = int(aug_size)
    data_size = len(label_paths[idx])
    repeat = aug_size - data_size
    print(aug_size, data_size, repeat)
    print("up", repeat)
    if repeat < 0: #마이너스면 삭제 처리해줌 
        for _ in tqdm(range(-repeat)):        
            if len(label_paths[idx]) <= 0:  # 이미지 경로가 남아있지 않으면 중지
                break
            random_int = random.randint(0, len(label_paths[idx])-1)
            img_path = label_paths[idx][random_int]
            os.remove(img_path)
            label_paths[idx].remove(img_path)


    else : #플러스면 증강 처리해줌
        for _ in tqdm(range(repeat)):
            random_int = random.randint(0,data_size-1)
            img_id = label_paths[idx][random_int].split('/')[-2]
    #         print(random_int)
            img = Image.open(label_paths[idx][random_int])
            img = random_transform(img)
            img.save(os.path.join(dir_name+'/train/images',img_id,idx2label[idx]+str(_+10)+'.jpg'))
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--dataset', type=str, default='MaskPreprocessDataset', help='dataset augmentation type (default: MaskBaseDataset)')
    parser.add_argument('--data_dir', type=str, default=os.environ.get('SM_CHANNEL_TRAIN', '/opt/ml/input/data/train/images'))
#     parser.add_argument('--delplus', type=int, default=0,choices=[1, 0], help = 'want? (y : 1 enter ,n : 0 enter 1를 입력하면 지정 텍스트 파일을 읽어 실행됨)') # 무조건 실행되므로 필요없음
    parser.add_argument('--dir_name', type=str, default='/opt/ml/input/data/augmentation_delete_data', help = 'creat preprocess dataset folder')

    args = parser.parse_args()
    print(args)

#     delplus = args.delplus
    data_dir = args.data_dir
    dir_name = args.dir_name

    dataset_module = getattr(import_module("dataset"), args.dataset)  # default: MaskPreprocessDataset
    dataset = dataset_module(
        data_dir=data_dir,
    )
    
    # -- delplus 다현 추가 부분
    with open('./delplustxt.txt', 'r') as f:
        for line in f:
            idx,size = line.strip().split(',')
            AddAugmentation(dataset.label_paths,idx,size, dir_name)
            

# python datapreprocess.py --data_dir /opt/ml/input/data/train/images