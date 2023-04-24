import argparse as ap
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from typing import Any
from keras.preprocessing.image import ImageDataGenerator, DirectoryIterator
from keras.utils import load_img, img_to_array


class ModelTrain:
    def __init__(self, image_path: str) -> None:
        self.IMAGE_PATH = image_path
        self.TRAIN_DIR = "./data/train"
        self.VALID_DIR = "./data/valid"

    def _create_generator(self) -> tuple[DirectoryIterator]:
        train_datagen = ImageDataGenerator(rescale=1/255)
        validation_datagen = ImageDataGenerator(rescale=1/255)

        train_generator = train_datagen.flow_from_directory(
            self.TRAIN_DIR,
            classes=['human', 'shark'],
            target_size=(200, 200),
            batch_size=190,
            class_mode='binary')

        validation_generator = validation_datagen.flow_from_directory(
            self.VALID_DIR,
            classes=['human', 'shark'],
            target_size=(200, 200),
            batch_size=15,
            class_mode='binary',
            shuffle=False)

        return (train_generator, validation_generator)

    def _model_compile(self) -> tuple[tf.keras.models.Sequential, Any]:
        (train_generator, validation_generator) = self._create_generator()
        model = tf.keras.models.Sequential([
            tf.keras.layers.Flatten(input_shape=(200, 200, 3)),
            tf.keras.layers.Dense(128, activation=tf.nn.relu),
            tf.keras.layers.Dense(1, activation=tf.nn.sigmoid)
        ])

        model.summary()
        model.compile(optimizer=tf.keras.optimizers.Adam(),
                      loss='binary_crossentropy',
                      metrics=['accuracy'])

        history = model.fit(train_generator,
                            steps_per_epoch=15,
                            epochs=15,
                            verbose=1,
                            validation_data=validation_generator,
                            validation_steps=15)
        return (model, history)

    def predict_image(self) -> str:
        (model, history) = self._model_compile()
        img = load_img(self.IMAGE_PATH, target_size=(200, 200))
        x = img_to_array(img)
        plt.imshow(x / 255.)
        x = np.expand_dims(x, axis=0)
        images = np.vstack([x])
        classes = model.predict(images, batch_size=19)
        return_value = "There"
        return_value += " is a **Human**" if classes[0] < 0.5 else " is a **Shark**"
        return_value += " in your image. "
        acc_res = history.history['accuracy']
        return_value += f"\nACC result: **{sum(acc_res) / len(acc_res)}**"
        tf.keras.backend.clear_session()
        return return_value
