"""
Contains the CGAN model class

This module defines how a CGAN will function with the 2 different models composing it
as well as a custom training process along with custom loss functions and metric
reporting.The CGAN class itself contains init, compile and a dynamic property
called metrics that can be used by other code
"""

import tensorflow as tf
from keras import metrics
from tensorflow.keras.models import Model


class CGAN(Model):
    def __init__(self, generator, discriminator):
        """
        Instantiates an instance of a CGAN

        :param generator: An instance of the Generator model class
        :param discriminator: An instance of the Generator model class
        """

        super(CGAN, self).__init__()
        self.generator = generator
        self.discriminator = discriminator
        self.d_optimiser = None
        self.g_optimiser = None
        self.gradient_penalty = metrics.Mean()
        self.discriminator_loss = metrics.Mean()
        self.generator_loss = metrics.Mean()

    def compile(self, gen_optimiser, disc_optimiser):
        """
        Adds the optimisers to the two models

        :param gen_optimiser: The optimiser for the generator
        :param disc_optimiser: The optimiser for the discriminator
        """
        super().compile()
        self.g_optimiser = gen_optimiser
        self.d_optimiser = disc_optimiser

    @tf.function
    def train_step(self, data):
        """
        Defines the training process of a single batch. The discriminator is updated
        5 times for each batch then the generator is updated once

        :param data: The batch of images and labels
        :return: The result of the training
        """
        real_images, labels = data
        batch_size = tf.shape(real_images)[0]
        noise = tf.random.normal([batch_size, 128])
        gps = []

        for _ in range(5):
            with tf.GradientTape() as tape:

                fake_images = self.generator([noise, labels], training=True)
                pred_real = self.discriminator([real_images, labels], training=True)
                pred_fake = self.discriminator([fake_images, labels], training=True)

                gp = self.gp_func(real_images, fake_images, labels)
                gps.append(gp)

                real_loss = tf.reduce_mean(pred_real)
                fake_loss = tf.reduce_mean(pred_fake)
                disc_loss = (fake_loss - real_loss) + (gp * 10)

            grads = tape.gradient(disc_loss, self.discriminator.trainable_variables)

            self.d_optimiser.apply_gradients(zip(grads, self.discriminator.trainable_variables))

        with tf.GradientTape() as tape:
            fake_images = self.generator([noise, labels], training=True)
            pred_fake = self.discriminator([fake_images, labels], training=True)
            gen_loss = -tf.reduce_mean(pred_fake)

        grads = tape.gradient(gen_loss, self.generator.trainable_variables)

        self.g_optimiser.apply_gradients(zip(grads, self.generator.trainable_variables))

        avg_gp = tf.reduce_mean(gps)
        self.gradient_penalty.update_state(avg_gp)
        self.discriminator_loss.update_state(disc_loss)
        self.generator_loss.update_state(gen_loss)

        return {"discriminator_loss": self.discriminator_loss.result(),
                "generator_loss": self.generator_loss.result(),
                "gradient_penalty": self.gradient_penalty.result()}

    def gp_func(self, real_images, fake_images, labels):
        """
        Calculates the gradient penalty according to the WGAN-GP paper

        :param real_images: The batch of real images
        :param fake_images: The corresponding batch of generated images
        :param labels: The labels for the images
        :return: The calculated gradient penalty
        """
        batch_size = tf.shape(real_images)[0]

        alpha = tf.random.uniform(shape=[batch_size, 1, 1, 1], minval=0, maxval=1)

        interpolated_images = alpha * real_images + ((1 - alpha) * fake_images)

        with tf.GradientTape() as tape:
            tape.watch(interpolated_images)
            logits = self.discriminator([interpolated_images, labels], training=True)

        gradients = tape.gradient(logits, interpolated_images)

        gradients_norm = tf.sqrt(tf.reduce_sum(tf.square(gradients), axis=[1, 2, 3]))

        gradient_penalty = tf.reduce_mean((gradients_norm - 1.0) ** 2)

        return gradient_penalty

    @property
    def metrics(self):
        """
        Dynamic property needed to reset metrics each epoch

        :return: An array of all the loss items
        """
        return [self.discriminator_loss, self.generator_loss, self.gradient_penalty]
