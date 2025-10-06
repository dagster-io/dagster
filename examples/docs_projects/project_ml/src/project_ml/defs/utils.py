from typing import Any

import torch
import torch.nn as nn
import torch.optim as optim


def get_optimizer(config: Any, model_params) -> torch.optim.Optimizer:
    """Get optimizer based on config."""
    if config.optimizer_type.lower() == "adam":
        return optim.Adam(model_params, lr=config.learning_rate, weight_decay=config.weight_decay)
    elif config.optimizer_type.lower() == "sgd":
        return optim.SGD(
            model_params,
            lr=config.learning_rate,
            momentum=config.momentum,
            weight_decay=config.weight_decay,
        )
    return optim.Adam(model_params, lr=config.learning_rate, weight_decay=config.weight_decay)


def create_conv_block(
    in_channels: int, out_channels: int, kernel_size: int, use_batch_norm: bool
) -> nn.Sequential:
    """Create a reusable convolutional block."""
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size, padding=kernel_size // 2),
        nn.BatchNorm2d(out_channels) if use_batch_norm else nn.Identity(),
        nn.ReLU(),
    )
