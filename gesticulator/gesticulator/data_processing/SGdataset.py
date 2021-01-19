from __future__ import print_function, division
from os import path
import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

torch.set_default_tensor_type('torch.FloatTensor')

class SpeechGestureDataset(Dataset):
    """Trinity Speech-Gesture Dataset class."""

    def __init__(self, root_dir, apply_PCA=False, train=True, use_mirror_augment=False):
        """
        Args:
            root_dir (string): Directory with the datasat.
        """
        self.root_dir = root_dir
        # Get the data
        if train:
            self.audio = np.load(path.join(root_dir, 'X_train.npy')).astype(np.float32)
            self.text = np.load(path.join(root_dir, 'T_train.npy')).astype(np.float32)

            # apply PCA
            if apply_PCA:
                self.gesture = np.load(path.join(root_dir, 'PCA', 'Y_train.npy')).astype(np.float32)
                if use_mirror_augment:
                    print("[WARNING] the 'use_mirror_augment' parameter is ignored because 'apply_PCA' is set to true!")
            else:
                self.gesture = np.load(path.join(root_dir, 'Y_train.npy')).astype(np.float32)
                
                if use_mirror_augment:
                    gesture_mirrored = np.load(path.join(root_dir, 'Y_train_mirrored.npy')).astype(np.float32)
                    self.gesture = np.concatenate((self.gesture, gesture_mirrored), axis=0)
        else:
            self.audio = np.load(path.join(root_dir, 'X_dev.npy')).astype(np.float32)
            self.text = np.load(path.join(root_dir, 'T_dev.npy')).astype(np.float32)
            # apply PCA
            if apply_PCA:
                self.gesture = np.load(path.join(root_dir, 'PCA', 'Y_dev.npy')).astype(np.float32)
            else:
                self.gesture = np.load(path.join(root_dir, 'Y_dev.npy')).astype(np.float32)

        # upsample text to get the same sampling rate as the audio
        cols = np.linspace(0, self.text.shape[1], endpoint=False, num=self.text.shape[1]*2, dtype=int)
        self.text = self.text[:, cols,:]

        self.audio_dim = self[0]['audio'].shape[-1]


    def __len__(self):
        # NOTE: it's important to take the length of the gestures and not the speech
        #       because the gestures might be twice the length if mirroring is used
        return len(self.gesture)


    def __getitem__(self, idx):
        # if mirroring is used, 'idx' can go up to twice the length of audio/text
        # instead of storing them twice, we can take the modulo
        audio = self.audio[idx % len(self.audio)]
        text = self.text[idx % len(self.text)]
        gesture = self.gesture[idx]

        sample = {'audio': audio, 'output': gesture, 'text': text}

        return sample


class ValidationDataset(Dataset):
    """Validation samples from the Trinity Speech-Gesture Dataset."""

    def __init__(self, root_dir, past_context, future_context):
        """
        Args:
            root_dir (string): Directory with the datasat.
        """
        self.root_dir = root_dir
        self.past_context = past_context
        self.future_context = future_context
        # Get the data
        self.audio = np.load(path.join(root_dir, 'dev_inputs', 'X_dev_Recording_001.npy')).astype(np.float32)
        self.text = np.load(path.join(root_dir, 'dev_inputs', 'T_dev_Recording_001.npy')).astype(np.float32)
        # upsample text to get the same sampling rate as the audio
        cols = np.linspace(0, self.text.shape[0], endpoint=False, num=self.text.shape[0]*2, dtype=int)
        self.text = self.text[cols,:]

        self.start_times = [100, 200, 300, 400]
        self.end_times = [t + 15 for t in self.start_times]

        self.audio_dim = self[0]['audio'].shape[-1]

    def __len__(self):
        return len(self.start_times)

    def __getitem__(self, idx):
        
        start = int(self.start_times[idx] * 20) # 20fps
        end = int(self.end_times[idx] * 20)  # 20fps
        audio = self.audio[start-self.past_context : end+self.future_context]
        text = self.text[start-self.past_context : end+self.future_context]

        sample = {'audio': audio, 'text': text}

        return sample


def fit_and_standardize(data):
    shape = data.shape
    flat = data.reshape((shape[0]*shape[1], shape[2]))
    scaler = StandardScaler().fit(flat)
    scaled = scaler.transform(flat).reshape(shape)
    return scaled, scaler

def standardize(data, scaler):
    shape = data.shape
    flat = data.reshape((shape[0]*shape[1], shape[2]))
    scaled = scaler.transform(flat).reshape(shape)
    return scaled

def inv_standardize(data, scaler):      
    shape = data.shape
    flat = data.reshape((shape[0]*shape[1], shape[2]))
    scaled = scaler.inverse_transform(flat).reshape(shape)
    return scaled     