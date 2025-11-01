
import torch
import torch.nn as nn
import torch.nn.functional as F
import pytorch_lightning as pl

class SimpleClassifier(pl.LightningModule):
    """
    A minimal PyTorch Lightning Module for classification.
    """
    def __init__(self, lr: float = 1e-3, input_dim: int = 784, num_classes: int = 10):
        super().__init__()
        # Saves lr, input_dim, and num_classes to self.hparams for checkpointing
        self.save_hyperparameters() 

        # Define layers
        self.layer_1 = nn.Linear(input_dim, 128)
        self.layer_2 = nn.Linear(128, num_classes)
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, x):
        # Flatten input (e.g., if input is a 28x28 image)
        x = x.view(x.size(0), -1)
        x = F.relu(self.layer_1(x))
        x = self.layer_2(x)
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