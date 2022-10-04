#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2022-07-28$

@author: Jonathan Beaulieu-Emond
"""
import os

import torch
import yaml

from CheXpert2.Experiment import Experiment
from CheXpert2.models.CNN import CNN
from CheXpert2.training.train import main
from CheXpert2 import names

def test_train():
    try:
        img_dir = os.environ["img_dir"]
    except:
        img_dir = ""

    torch.cuda.is_available = lambda: False
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["DEBUG"] = "True"
    os.environ["WANDB_MODE"] = "offline"

    config = {
        "model": "convnext_tiny",
        "batch_size": 2,
        "img_size": 224,
        "num_worker": 0,
        "augment_intensity": 0,
        "cache": False,
        "N": 0,
        "M": 2,
        "clip_norm": 100,
        "label_smoothing": 0,
        "lr": 0.001,
        "beta1": 0.9,
        "beta2": 0.999,
        "weight_decay": 0.01,
        "freeze": False,
        "pretrained": False,
        "pretraining": 0,
        "channels": 1,
        "autocast": True,
        "pos_weight": 1,
    }

    experiment = Experiment(
        f"{config['model']}", names=names, tags=None, config=config, epoch_max=1, patience=5
    )
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    prob = [0, ] * 6
    model = CNN(config["model"], len(names), img_size=config["img_size"], freeze_backbone=config["freeze"],
                pretrained=config["pretrained"], channels=config["channels"], pretraining=False)
    results = main(config, img_dir, model, experiment, torch.optim.SGD(model.parameters(), lr=config["lr"]),
                   torch.nn.BCEWithLogitsLoss, device, prob, None,pretrain=False)

    assert experiment.best_loss != 0


if __name__ == "__main__":
    test_train()
