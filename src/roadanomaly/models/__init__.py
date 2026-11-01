"""Model builders, one module per approach.

- deeplabv3plus : Binôme A, DeepLabV3+ with a frozen ImageNet ResNet50 encoder
- autoencoder   : Binôme B baseline, convolutional autoencoder on pixel patches (+ loss variants)
- feature_ae    : Binôme B final model, autoencoder on frozen ImageNet (VGG16) features
- cnn           : Binôme C baseline, encoder-decoder CNN without skip connections (Hejer)
- unet          : Binôme C, U-Net from scratch and U-Net with an ImageNet ResNet50 encoder (Walid)
"""
