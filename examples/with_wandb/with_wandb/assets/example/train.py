#!/usr/bin/env python
# ruff: noqa: T201

"""Based on: https://github.com/wandb/examples/blob/master/examples/pytorch/pytorch-cnn-fashion/train.py
Builds a convolutional neural network on the fashion mnist data set.
Designed to show wandb integration with pytorch.
"""

import os

import torch
import torch.nn as nn
import torchvision.transforms as transforms
import wandb
from fashion_data import fashion
from torch.autograd import Variable

hyperparameter_defaults = dict(
    dropout=0.5,
    channels_one=16,
    channels_two=32,
    batch_size=100,
    learning_rate=0.001,
    epochs=2,
)

wandb.init(config=hyperparameter_defaults, project="pytorch-cnn-fashion")
config = wandb.config


class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()

        # Convolution 1
        self.cnn1 = nn.Conv2d(
            in_channels=1,
            out_channels=config.channels_one,
            kernel_size=5,
            stride=1,
            padding=0,
        )
        self.relu1 = nn.ReLU()
        # Max pool 1
        self.maxpool1 = nn.MaxPool2d(kernel_size=2)

        # Convolution 2
        self.cnn2 = nn.Conv2d(
            in_channels=config.channels_one,
            out_channels=config.channels_two,
            kernel_size=5,
            stride=1,
            padding=0,
        )
        self.relu2 = nn.ReLU()

        # Max pool 2
        self.maxpool2 = nn.MaxPool2d(kernel_size=2)

        self.dropout = nn.Dropout(p=config.dropout)

        # Fully connected 1 (readout)
        self.fc1 = nn.Linear(config.channels_two * 4 * 4, 10)

    def forward(self, x):
        # Convolution 1
        out = self.cnn1(x)
        out = self.relu1(out)

        # Max pool 1
        out = self.maxpool1(out)

        # Convolution 2
        out = self.cnn2(out)
        out = self.relu2(out)

        # Max pool 2
        out = self.maxpool2(out)

        # Resize
        # Original size: (100, 32, 7, 7)
        # out.size(0): 100
        # New out size: (100, 32*7*7)
        out = out.view(out.size(0), -1)
        out = self.dropout(out)
        # Linear function (readout)
        out = self.fc1(out)

        return out


def main():
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
    )

    train_dataset = fashion(root="./data", train=True, transform=transform, download=True)

    test_dataset = fashion(
        root="./data",
        train=False,
        transform=transform,
    )

    label_names = [
        "T-shirt or top",
        "Trouser",
        "Pullover",
        "Dress",
        "Coat",
        "Sandal",
        "Shirt",
        "Sneaker",
        "Bag",
        "Boot",
    ]

    train_loader = torch.utils.data.DataLoader(
        dataset=train_dataset, batch_size=config.batch_size, shuffle=True
    )

    test_loader = torch.utils.data.DataLoader(
        dataset=test_dataset, batch_size=config.batch_size, shuffle=False
    )

    model = CNNModel()
    wandb.watch(model)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

    iter = 0
    for epoch in range(config.epochs):
        for i, (training_images, training_labels) in enumerate(train_loader):
            images = Variable(training_images)
            labels = Variable(training_labels)

            # Clear gradients w.r.t. parameters
            optimizer.zero_grad()

            # Forward pass to get output/logits
            outputs = model(images)

            # Calculate Loss: softmax --> cross entropy loss
            loss = criterion(outputs, labels)

            # Getting gradients w.r.t. parameters
            loss.backward()

            # Updating parameters
            optimizer.step()

            iter += 1

            if iter % 100 == 0:
                # Calculate Accuracy
                correct = 0.0
                correct_arr = [0.0] * 10
                total = 0.0
                total_arr = [0.0] * 10

                # Iterate through test dataset
                for test_images, test_labels in test_loader:
                    images = Variable(test_images)

                    # Forward pass only to get logits/output
                    outputs = model(images)

                    # Get predictions from the maximum value
                    _, predicted = torch.max(outputs.data, 1)

                    # Total number of test_labels
                    total += test_labels.size(0)
                    correct += (predicted == test_labels).sum()

                    for label in range(10):
                        correct_arr[label] += (
                            (predicted == test_labels) & (test_labels == label)
                        ).sum()
                        total_arr[label] += (test_labels == label).sum()

                accuracy = correct / total

                metrics = {"accuracy": accuracy, "loss": loss}
                for label in range(10):
                    metrics["Accuracy " + label_names[label]] = (
                        correct_arr[label] / total_arr[label]
                    )

                wandb.log(metrics)

                # Print Loss
                print("Iteration: {0} Loss: {1:.2f} Accuracy: {2:.2f}".format(iter, loss, accuracy))
    torch.save(model.state_dict(), os.path.join(wandb.run.dir, "model.pt"))


if __name__ == "__main__":
    main()
