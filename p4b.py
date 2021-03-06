# QUESTION 1 : I downloaded file (uncased_L-12_H-768_A-12) to a directory (k). How do you run this file straight from git?
#cd ~/environments/k/
# A: You gotta download ethe entire repo

#conda activate p36 #p36 is 3.6.2; p35 doesn't install tf well, & p37 probably gives errors w tf
# Dependnecies part 1
#pip install -U bert-serving-server bert-serving-client
#pip install tensorflow-gpu
#bert-serving-start -model_dir=uncased_L-12_H-768_A-12

# When you see "ready to serve client",start a new tab and install tf again (?) and then go to python
# Optional: if you want  ELMo-like contextual word embedding set -pooling_strategy NONE as follows :
# bert-serving-start -pooling_strategy NONE -model_dir=uncased_L-12_H-768_A-12

# On Python :
Python
import json
import os
import time
import GPUtil
import numpy
import tensorflow as tf
from bert_serving.server import BertServer
# Note: BertClient is imported further below

# QUESTION 2: How do these affect training?
# A:Dimension of the input to LSTM is (Batch_size , timesteps, features or embedding dimension)
# Optional: If you want embeddings that corresponds to every token, you can simply use slice index as follows:
max_seq_len = 12
#pooling_strategy = NONE

# QUESTION 3(same as question 1) can you open this file direct from git? 
# Open json text file to be used by bert client further below :

with open('rows.json', 'r') as f:
        data = f.read().strip();

# These process the json data and prevent error "...expecting string".
str = data.replace("\'", "\"") 
# Optional you can also use jsbeautifier, which is less strict: $ pip install jsbeautifier   $ js-beautify file.js   
  
# QUESTION 4.1 How do these affect the training ?
# QUESTION 4.2 what is "os.environ['CUDA_VISIBLE_DEVICES'] below... ?
# Process the following before making Bert Client furthe below

batch_size = 16
num_parallel_calls = 2
num_clients = 5  

# os.environ['CUDA_VISIBLE_DEVICES'] = str(GPUtil.getFirstAvailable())  # default uses GPU
# os.environ['CUDA_VISIBLE_DEVICES'] = str(GPUtil.getFirstAvailable()), as -1, # to use CPU if you get a "resource exhaused" error
# Make BConcurrentBertClient:

from bert_serving.client import ConcurrentBertClient
bc = ConcurrentBertClient()

# Optional: If you want to use your own tokenizer to segment sentences instead of the default one from BERTencode(is_tokenized=True) on the client slide as follows:
# texts2 = [s.split() for s in texts]
# bc.encode(texts2, is_tokenized=True)  # remember to first run bc = BertClient()

# Make data iteration :

def get_encodes(x):
    # x is `batch_size` of lines, each of which is a json object
    samples = [json.loads(l) for l in x]
    text = [s['fact'][-50:] for s in samples]
    features = bc.encode(text)
    labels = [0 for _ in text]
    return features, labels

# Optional: If you want GPU growth. Allowing tf to only use what it needs. But it won't help a "resource exhasted" error.
# config = tf.ConfigProto()
# config.gpu_options.allow_growth = True 
# session = tf.Session(config=config)

# QUESTION 5: What is data node?
#an = [ 1 ,2 ,3, 5], map(lambda x: x*x,an ) #Maps the labmda function, to the entire list. 
# a = 5, 

data_node = (tf.data.TextLineDataset(str).batch(batch_size)
             .map(lambda x: tf.py_func(get_encodes, [x], [tf.float32, tf.int64], name='bert_client'),
                  num_parallel_calls=num_parallel_calls)
             .map(lambda x, y: {'feature': x, 'label': y})
             .make_one_shot_iterator().get_next())

# Question 6: How do you fix "InvalidArgumentError:..?"

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    cnt, num_samples, start_t = 0, 0, time.perf_counter()
    while True:
        x = sess.run(data_node)
        cnt += 1
        num_samples += x['feature'].shape[0]
        if cnt % 10 == 0:
            time_used = time.perf_counter() - start_t
            print('data speed: %d/s' % int(num_samples / time_used))
            cnt, num_samples, start_t = 0, 0, time.perf_counter()

# Errors & how I fixed them:
tensorflow.python.framework.errors_... No such file or directory..	[fixed with naming the "train_fp.txt" in the last few lines]
tensorflow.python.framework.errors_...OutOfRangeError: End of sequence  [fixed w. more json data]
JSONDecodeError: Expecting value: line 1 column 1 ...[Fixed by opening a good json and running it through str = data.replace("\'", "\"")]
tensorflow.python.framework.errors_impl.InvalidArgumentError:..?
