import threading
import shutil
import os
import random
import shutil
from PIL import Image
import numpy as np
import tensorflow as tf

class CenterCrop():
    """Crops out the center portion of an image and resizes to a target size
    Attributes:
        crop_size: size of the region to crop from the image, the image is 
        cropped to the largest possible square if crop_size > either dimension
        target_size: the cropped image is resized to this size
        interpolation: interpolation method for resizing
    """
    def __init__(self, crop_size, target_size):
        self.crop_size = crop_size
        self.target_size = target_size
        self.interpolation = Image.BILINEAR
    def __call__(self, image):
       w, h = image.size
       width_to_crop = max(w-self.crop_size, 0)
       height_to_crop = max(h-self.crop_size, 0)
       width_to_crop = width_to_crop if height_to_crop!=0 else max(w-h,0)
       height_to_crop = width_to_crop if width_to_crop!=0 else max(h-w,0)
       left = 0+width_to_crop//2
       top = 0+height_to_crop//2
       right = w-(width_to_crop-left)
       bottom = h-(height_to_crop-top)
       image = image.crop((left, top, right, bottom))
       image = image.resize((self.target_size, self.target_size),
                            self.interpolation)
       return image

def undersample(good_items, bad_items):
    """Create two lists of the same length given two lists by removing items 
    from the end of the longer list.
    Args:
        good_items: first list
        bad_items: second list
    """
    N_good = len(good_items)
    N_bad = len(bad_items)
    if N_good>N_bad:
        return good_items[:N_bad], bad_items
    elif N_good<N_bad:
        return good_items, bad_items[:N_good]
    else:
        return good_items, bad_items

def oversample(good_items, bad_items):
    """Create two lists of the same length given two lists by randomly 
    duplicating some items from the shorter list.
    Args:
        good_items: first list
        bad_items: second list
    """
    N_good = len(good_items)
    N_bad = len(bad_items)
    if N_good>N_bad:
        idxs = np.random.choice(range(N_good), N_good-N_bad)
        bad_items = bad_items+[bad_items[i] for i in idxs]
        return good_items, bad_items
    elif N_good<N_bad:
        idxs = np.random.choice(range(N_good), N_bad-N_good)
        good_items = good_items+[good_items[i] for i in idxs]
        return good_items, bad_items
    else:
        return good_items, bad_items

def load_images(images_dir, loader_transform, f_split, sampling_mode): 
    """Loads images from a directory with two subdirectories named "Good" and
    "Bad" into training and validation image tensors. Note: the resulting
    images are shuffled within the classes but ordered by class.
    Args:
        image_dir: directory of images
        loader_transform: callable transform to apply to images after loading
        sampling_type: Optional; allows resampling to correct class bias; Options
        are 'under', 'over', and None
    Returns: X_train, X_val
        X_train: (num_training, height, width, num_channels) torch.tensor of training images
        X_val: (num_val, height, width, num_channels) torch.tensor of validation images
    """
    good_images_dir = images_dir+'/Good'
    good_images = os.listdir(good_images_dir)
    random.shuffle(good_images)
    bad_images_dir = images_dir+'/Bad'
    bad_images = os.listdir(bad_images_dir)
    random.shuffle(bad_images)
    
    N_train_good = int(np.floor(f_split*len(good_images)))
    good_images_train = good_images[:N_train_good]
    good_images_val = good_images[N_train_good:]
    
    N_train_bad = int(np.floor(f_split*len(bad_images)))
    bad_images_train = bad_images[:N_train_bad]
    bad_images_val = bad_images[N_train_bad:]
    
    if sampling_mode == 'under':
        good_images_train, bad_images_train = undersample(good_images_train, bad_images_train)
        good_images_val, bad_images_val = undersample(good_images_val, bad_images_val)
    elif sampling_mode == 'over':
        good_images_train, bad_images_train = oversample(good_images_train, bad_images_train)
        good_images_val, bad_images_val = oversample(good_images_val, bad_images_val)
    
    X_train = []
    y_train = []
    for i, image in enumerate(good_images_train):
        image = Image.open(good_images_dir+'/'+image)
        image = loader_transform(image)
        image_array = np.array(image)
        X_train.append(image_array)
        y_train.append([1.0])
    for i, image in enumerate(bad_images_train):
        image = Image.open(bad_images_dir+'/'+image)
        image = loader_transform(image)
        image_array = np.array(image)
        X_train.append(image_array)
        y_train.append([0.0])
        
    X_val = []
    y_val = []
    for i, image in enumerate(good_images_val):
        image = Image.open(good_images_dir+'/'+image)
        image = loader_transform(image)
        image_array = np.array(image)
        X_val.append(image_array)
        y_val.append([1.0])
    for i, image in enumerate(bad_images_val):
        image = Image.open(bad_images_dir+'/'+image)
        image = loader_transform(image)
        image_array = np.array(image)
        X_val.append(image_array)
        y_val.append([0.0])
    
    X_train = np.array(X_train)
    y_train = np.array(y_train, dtype = 'float32')
    X_val = np.array(X_val)
    y_val = np.array(y_val, dtype = 'float32')
    return X_train, y_train, X_val, y_val
    
def create_ds(X, y, batch_size, shuffle = True, aug = None):
    """Creates a dataset given ndarrays of data and labels
    Args:
        X: (N, H, W, C) ndarray of uint8 images
        y: (N, M) ndarray of float32 ground truth labels
        batch_size: batch_size
        shuffle: bool; toggle shuffle shuffle data
        aug: tf.keras.Model; augmentation transform
    """
    autotune = tf.data.experimental.AUTOTUNE
    ds = tf.data.Dataset.from_tensor_slices((X, y))
    if shuffle:
        ds = ds.shuffle(buffer_size = 1024, reshuffle_each_iteration = True)
    ds = ds.batch(batch_size)
    if aug is not None:
        ds = ds.map(lambda x, y: (aug(x, training = True), y),
                    num_parallel_calls = autotune)
    return ds.prefetch(buffer_size = autotune)

class Train(threading.Thread):
    """Trains a CNN model on a binary image dataset and puts results in a queue
    Attributes:
        queue: queue to hold results
        filename: working directory for training
        model_path: path to folder containing pre-trained model
        filters: list of 4 ints; number of channels for hidden layers
        kernels: list of 3 ints; pixel size of convolutional kernels
        batch_size: batch size
        input_size: size of images input to model
        crop_size: after loading, the images are center-cropped to this size
        epochs: number of training epochs
        f_split: fraction of data to use for training set
        rebalance_classes: bool; set True to oversample minority class
        lr: learning rate
        pre-trained weights
    """
    def __init__(self, queue, filename, model_path, filters, 
                 kernels, batch_size, input_size, epochs):
        threading.Thread.__init__(self)
        self.queue = queue
        self.filename = filename+"/Neural_Network"
        self.model_path = model_path
        self.filters = filters
        self.kernels = kernels
        self.batch_size = batch_size
        self.input_size = input_size
        self.crop_size = np.inf
        self.epochs = epochs
        self.f_split = 0.8
        self.lr = 3e-4
        self.sampling_mode = 'over'
        self.seed = 2139
        
    def run(self):
        
        np.random.seed(self.seed)
        random.seed(self.seed)
        tf.random.set_seed(self.seed)
        
        epoch_dir="temp_model"
        try:    
            os.mkdir(epoch_dir)
        except Exception as e:
            print(e)
        print('Loading Dataset')
        loader_transform = CenterCrop(self.crop_size, self.input_size)
        X_train, y_train, X_val, y_val = load_images(self.filename, 
                                                     loader_transform, 
                                                     self.f_split,
                                                     self.sampling_mode)
        
        rng_state = np.random.get_state()
        np.random.shuffle(X_train)
        np.random.set_state(rng_state)
        np.random.shuffle(y_train)
        
        data_augmentation = tf.keras.Sequential([
                tf.keras.layers.experimental.preprocessing.RandomFlip("horizontal_and_vertical"),
                tf.keras.layers.experimental.preprocessing.RandomRotation(0.25),
                tf.keras.layers.experimental.preprocessing.RandomZoom(0.1)])
        train_ds = create_ds(X_train, y_train, self.batch_size, aug = data_augmentation)
        val_ds = create_ds(X_val, y_val, self.batch_size, shuffle = False)
        
        if self.model_path is not '':
            with open(self.model_path+'/trained_model.json', 'r') as json_file:
                model_json = json_file.read()
                model = tf.keras.models.model_from_json(model_json)
                model.load_weights(self.model_path+'/trained_model.h5')
                self.lr = 2e-4
        else:
            model = tf.keras.Sequential([
                    tf.keras.layers.Input((self.input_size, self.input_size, 3)),
                    tf.keras.layers.experimental.preprocessing.Rescaling(1./255),
                    tf.keras.layers.Conv2D(self.filters[0], 
                                           (self.kernels[0],self.kernels[0]), 
                                           padding='same', activation='relu',
                                            kernel_initializer = 'glorot_normal'),
                    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
                    tf.keras.layers.Conv2D(self.filters[1], 
                                           (self.kernels[1],self.kernels[1]), 
                                           padding='same', activation='relu',
                                            kernel_initializer = 'glorot_normal'),
                    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
                    tf.keras.layers.Conv2D(self.filters[2], 
                                           (self.kernels[2],self.kernels[2]), 
                                           padding='same', activation='relu',
                                            kernel_initializer = 'glorot_normal'),
                    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
                    tf.keras.layers.Dropout(0.1),
                    tf.keras.layers.Flatten(),
                    tf.keras.layers.Dense(self.filters[3], activation='relu'),
                    tf.keras.layers.Dense(2)])
                    
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=self.lr),
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                                                      metrics=['accuracy'])
                    
        checkpoint_path = epoch_dir+"/cp-{epoch:01d}.ckpt"
        print(checkpoint_path)
        
        cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path,
                                                 save_weights_only=True,
                                                 verbose=1)

        print('Starting Training')
        history = model.fit(train_ds, validation_data=val_ds, epochs=self.epochs, 
                        callbacks=[cp_callback])

        epochs = range(self.epochs)
        hist_dict = history.history
        acc = hist_dict['accuracy']
        loss = hist_dict['loss']
        val_acc = hist_dict['val_accuracy']
        val_loss = hist_dict['val_loss']
        class_names = ['Bad', 'Good']
        self.queue.put([class_names,[epochs,acc,val_acc,loss,val_loss],[model]])
        
        if os.path.exists(epoch_dir):
                shutil.rmtree(epoch_dir)