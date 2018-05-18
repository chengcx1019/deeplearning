#!/usr/bin/env python
# encoding: utf-8

"""
@author: changxin
@software: PyCharm
@file: fluid_loader.py
@time: 2018/5/4 15:04
"""
from __future__ import print_function
from __future__ import division

import math
import multiprocessing
import operator
import os
import time

from nose.tools import assert_equal
import numpy as np
import pandas as pd

from  utils.preprocess import fluid_process_pointcloud

BASE_DIR = '/data/datasets/simulation_data'
DATA_DIR = os.path.join(BASE_DIR, 'water')

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

class Processor(object):
    def __init__(self, particles, labels, index, data_dir, aug, is_testset):
        self.particles = particles
        self.labels = labels
        self.index = index
        self.data_dir = data_dir
        self.aug = aug
        self.is_testset = is_testset

    def __call__(self, load_index):
        label = self.labels[load_index]
        voxel = fluid_process_pointcloud(self.particles, load_index)
        ret = [voxel, label]

        return ret


def get_all_frames(data_dir=DATA_DIR):
    dirs = os.listdir(data_dir)
    frames = []
    for item in dirs:
        screen_path = os.path.join(data_dir, item)
        allfiles = os.listdir(screen_path)
        frames.extend(map(lambda x:os.path.join(item, x), allfiles))
    return map(lambda x:os.path.join(data_dir, x), frames)

# for test return subset of frames
def create_train_files(max_num):
    TRAIN_FILES = []
    files_map = get_all_frames()
    i = 0
    max_count = 2
    for item in files_map:
        if i == max_count:
            break
        TRAIN_FILES.append(item)
        i = i + 1

    assert_equal(len(TRAIN_FILES), max_count)
    return TRAIN_FILES

def convert_str_float(frame_particles):
    fps = pd.DataFrame(frame_particles[1:], columns=frame_particles[0])
    fps = fps[fps.columns[:-1]]
    for col in fps.columns:
        #if col == 'isFluidSolid':
        fps[col] = fps[col].astype(float)
    return fps

def laod_csv(filename):
    frame_particles = np.loadtxt(
            filename, dtype=np.str, delimiter=",")
    return convert_str_float(frame_particles)

def load_data_file(filename):
    suffix = filename.split('/')[-1].split('.')[-1]
    print(suffix)
    if suffix == 'csv':
        return laod_csv(filename)

def load_data_label(filename):
    particles = load_data_file(filename)
    cols = particles.columns
    data_cols = operator.add(list(cols[0:6]), list(cols[7:9])) # extrat timestep
    label_cols = cols[15:18]

    isfluid = cols[7]
    fluid_parts = particles[particles[isfluid] == 0]
    index = fluid_parts.index
    data = particles[data_cols].values
    label = fluid_parts[label_cols].values

    return data, label, index

def shuffle_data(data, labels):
    """ Shuffle data and labels.
        Input:
          data: B,N,... numpy array
          label: B,N... numpy array
        Return:
          shuffled data, label and shuffle indices
    """
    idx = np.arange(labels.shape[0])
    np.random.shuffle(idx)
    return data[idx, ...], labels[idx, ...], idx

def concat_data_label(train_files, max_points, dimention_data, dimention_label):
    """
    intercept max_points
    """
    TRAIN_FILES = train_files
    train_file_idxs = np.arange(0, len(TRAIN_FILES))
    np.random.shuffle(train_file_idxs)
    def get_array(shape):
        return np.empty(shape=shape)
    FRAMES_NUM = len(TRAIN_FILES)
    MAX_POINTS = max_points
    DIMENTION_DATA = dimention_data
    DIMENTION_LABEL = dimention_label
    data_shape = (FRAMES_NUM, MAX_POINTS, DIMENTION_DATA)
    """
    Different from the classification task, our lable is for every particle, we record label with (frame, particle index \
    , three-dimentions accelaration)(BxNx3)
    """
    label_shape = (FRAMES_NUM, MAX_POINTS, DIMENTION_LABEL)
    current_data = get_array(data_shape)
    current_label = get_array(label_shape)
    start = time.clock()
    for fn in range(len(TRAIN_FILES)):
        current_data_single, current_label_single = load_data_label(TRAIN_FILES[train_file_idxs[fn]])
        current_data[fn] = current_data_single.values[:MAX_POINTS, :]
        current_label[fn]= current_label_single.values[:MAX_POINTS, :]
    running = time.clock() - start
    print("runtime: %s" % str(running))
    return current_data, current_label

def concat_data_label_all(train_files, dimention_data, dimention_label):
    """
    use all data in a file
    """
    TRAIN_FILES = train_files
    train_file_idxs = np.arange(0, len(TRAIN_FILES))
    np.random.shuffle(train_file_idxs)

    DIMENTION_DATA = dimention_data
    DIMENTION_LABEL = dimention_label
    """
    Different from the classification task, our lable is for every particle, we record label with (frame, particle index \
    , three-dimentions accelaration)(BxNx3)
    """
    current_data = []
    current_label = []
    start = time.clock()
    for fn in range(len(TRAIN_FILES)):
        current_data_single, current_label_single = load_data_label(TRAIN_FILES[train_file_idxs[fn]])
        current_data.append(current_data_single)
        current_label.append(current_label_single)
    running = time.clock() - start
    print("runtime: %s" % str(running))
    return current_data, current_label

# global pool
TRAIN_POOL = multiprocessing.Pool(4)

def iterate_data(data_dir, shuffle=False, aug=False, is_testset=False, batch_size=1, multi_gpu_sum=1):
    TRAIN_FILES = get_all_frames(data_dir)
    for f in TRAIN_FILES:
        data, label, index = load_data_label(f)
        # TODO the common part of feature
        nums = len(index)
        indices = list(range(nums))
        num_batches = int(math.floor( nums / float(batch_size)))

        proc = Processor(data, label, index, data_dir, aug, is_testset)

        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            excerpt = indices[start_idx:start_idx + batch_size]
            rets = TRAIN_POOL.map(proc, excerpt)

            voxel = [ret[0] for ret in rets]
            assert_equal(len(voxel), batch_size)
            labels = [ret[1] for ret in rets]

            # only for voxel -> [gpu, k_single_batch, ...]
            vox_feature, vox_number, vox_coordinate = [], [], []
            vox_labels = []
            # TODO ccx if bach_size smalls than multi_gpu_sum
            single_batch_size = int(batch_size / multi_gpu_sum)
            for idx in range(multi_gpu_sum):
                label = labels[idx * single_batch_size:(idx + 1) * single_batch_size]
                _, per_vox_feature, per_vox_number, per_vox_coordinate = build_input(
                    voxel[idx * single_batch_size:(idx + 1) * single_batch_size])
                # a batch concate all files together ∑K
                vox_labels.append(label)
                vox_feature.append(per_vox_feature)
                vox_number.append(per_vox_number)
                vox_coordinate.append(per_vox_coordinate)

            ret = (
                np.array(vox_labels),
                np.array(vox_feature),
                np.array(vox_number),
                np.array(vox_coordinate),
            )

            yield ret

def build_input(voxel_dict_list):
    batch_size = len(voxel_dict_list)

    feature_list = []
    number_list = []
    coordinate_list = []
    for i, voxel_dict in zip(range(batch_size), voxel_dict_list):
        feature_list.append(voxel_dict['feature_buffer'])
        number_list.append(voxel_dict['number_buffer'])
        coordinate = voxel_dict['coordinate_buffer']
        coordinate_list.append(
            np.pad(coordinate, ((0, 0), (1, 0)),
                   mode='constant', constant_values=i)) # ccx add index for [[i, x1, y1, z1], [i, x2, y2, z2],...,]

    feature = np.concatenate(feature_list)
    number = np.concatenate(number_list)
    coordinate = np.concatenate(coordinate_list)
    return batch_size, feature, number, coordinate

if __name__ == '__main__':
    BATCH_SIZE = 2
    TRAIN_FILES = create_train_files(2)
    print(TRAIN_FILES)