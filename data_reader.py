import pickle, os
from data_preprocess import data_dir, train_file, valid_file, cities
from tqdm import tqdm
import random
import numpy as np
import tensorflow as tf

NUM_SENTENCES = 30
NUM_WORDS = 30


class DataReader:

    def __init__(self, num_images=3, train_shuffle=False):
        self.num_images = num_images
        self.train_shuffle = train_shuffle

        self.train_data = self._read_data(train_file)
        self.valid_data = self._read_data(valid_file)
        self.test_data = {}
        for city in cities:
            test_file = '{}_test.pickle'.format(city)
            self.test_data[city] = self._read_data(os.path.join(data_dir, 'test', test_file))

    def _read_data(self, file_path):
        print('Reading data from %s' % file_path)  # file_path is train.pickle
        data = []
        with open(file_path, 'rb') as f:
            try:
                i=1
                while True:
                    review, images, rating = pickle.load(f)

                    # clip review to specified max lengths
                    review = review[:NUM_SENTENCES]
                    review = [sent[:NUM_WORDS] for sent in review]

                    if i % 6 == 0:
                        for j in range(0,len(review)):
                            if len(review[j])>1:
                                sen1=review[j]
                                min1=min(sen1)
                                max1=max(sen1)
                                nr = np.array(sen1)
                                gaussian_noise = np.random.normal(0, 1, nr.shape)
                                noisy_review=np.abs(nr+10*gaussian_noise)
                                sen2=noisy_review.tolist()
                                min2 = min(sen2)
                                max2 = max(sen2)
                                sen3=[]
                                for n in sen2:
                                    new=(n-min2)/(max2-min2) * (max1-min1)
                                    sen3.append(new)
                                review[j]=sen3
                    i+=1

                    images = images[:self.num_images]

                    rating -= 1
                    assert rating >= 0 and rating <= 4

                    data.append((review, images, rating))
            except EOFError:
                return data

    def _batch_iterator(self, data, batch_size=1, desc=None):
        num_batches = int(np.ceil(len(data) / batch_size))
        for b in tqdm(range(num_batches), desc):
            begin_offset = batch_size * b
            end_offset = batch_size * b + batch_size
            if end_offset > len(data):
                end_offset = len(data)
            review_batch = []
            images_batch = []
            label_batch = []
            for offset in range(begin_offset, end_offset):
                review_batch.append(data[offset][0])
                images_batch.append(data[offset][1])
                label_batch.append(data[offset][2])
            # print(review_batch)
            yield review_batch, images_batch, label_batch

    def read_train_set(self, batch_size=1):
        if self.train_shuffle:
            random.shuffle(self.train_data)
        return self._batch_iterator(self.train_data, batch_size, desc='Training')

    def read_valid_set(self, batch_size=1):
        return self._batch_iterator(self.valid_data, batch_size, desc='Validation')

    def read_test_set(self, city, batch_size=1):
        return self._batch_iterator(self.test_data[city], batch_size, desc=city)
