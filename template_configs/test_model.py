import torch
from ${moduleName}.model.model import SimpleClassifier


def test_model_forward():
    model = SimpleClassifier(lr=1e-3, num_channels=3, num_classes=10)
    x = torch.randn(2, 3, 224, 224)
    out = model(x)
    assert out.shape == (2, 10)


def test_model_checkpoint(tmp_path):
    model = SimpleClassifier(lr=1e-3, num_channels=3, num_classes=10)
    ckpt_path = tmp_path / "model.ckpt"

    import lightning.pytorch as pl

    trainer = pl.Trainer(max_epochs=0)
    trainer.strategy.connect(model)
    trainer.save_checkpoint(str(ckpt_path))

    loaded = SimpleClassifier.load_from_checkpoint(str(ckpt_path))
    assert loaded.hparams.num_channels == 3
