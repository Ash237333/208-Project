"""
This module handles building of the discriminator model
"""

import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras import layers

IMAGE_DIMENSIONS = (128, 128, 3)  # (H,W,C) - Input Image Dimensions


def build_discriminator() -> Model:
    """
    Defines the architecture of the discriminator

    :return: The fully built model
    """

    con_label = layers.Input(shape=(1,))
    x = layers.Embedding(3, 50)(con_label)  # Encoding the label as a tensor
    size = tf.reduce_prod((128,128, 1)).numpy().item()
    x = layers.Dense(size)(x)
    stream2_input = layers.Reshape((128, 128, 1))(x)  # Reshapes tensor to be the same shape as the image

    stream1_input = layers.Input(shape=IMAGE_DIMENSIONS)
    merge = layers.Concatenate()([stream1_input, stream2_input])  # Adds tensor as an extra colour channel in the image
    
    x = layers.Conv2D(64, 4)(merge)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.Conv2D(64, 4)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.Conv2D(64, 4)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.Conv2D(64, 4)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.Flatten()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(1, activation="sigmoid")(x)

    model = tf.keras.Model([stream1_input, con_label], x)

    return model