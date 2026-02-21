
import torch
import torch.nn as nn
import torch.nn.functional as F
import lightning.pytorch as pl

class SimpleClassifier(pl.LightningModule):
    """
    A minimal Lightning Module for image classification.
    This is a placeholder CNN — replace it with your own architecture.
    """
    def __init__(self, lr: float = 1e-3, num_channels: int = 1, num_classes: int = 10):
        super().__init__()
        # Saves lr, num_channels, and num_classes to self.hparams for checkpointing
        self.save_hyperparameters()

        # TODO: Replace these layers with your architecture
        self.features = nn.Sequential(
            nn.Conv2d(num_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(64, num_classes),
        )
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, x):
        # TODO: Update forward pass to match your architecture
        x = self.features(x)
        x = self.classifier(x)
        return x

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)
        self.log('train_loss', loss, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)
        self.log('val_loss', loss, prog_bar=True)

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hparams.lr)
        return optimizer

# Required for PyTorch ONNX export to find the model class
if __name__ == "__main__":
    model = SimpleClassifier()
    print("Model initialized for structure review.")
