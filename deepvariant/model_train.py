# Copyright 2017 Google LLC.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Trains the DeepVariant model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os



from absl import flags
from absl import logging
from tensor2tensor.utils import metrics_hook
import tensorflow as tf

from third_party.nucleus.util import proto_utils
from deepvariant import data_providers
from deepvariant import logging_level
from deepvariant import modeling
from deepvariant import tf_utils

slim = tf.contrib.slim

FLAGS = flags.FLAGS

# Data set selection parameters
flags.DEFINE_string('dataset_config_pbtxt', None,
                    'The path to the dataset config file.')

flags.DEFINE_string('model_name', 'inception_v3',
                    'The name of the model to use for predictions.')

flags.DEFINE_integer('batch_size', 64, 'The number of samples in each batch.')

# Cloud TPU Cluster Resolvers
flags.DEFINE_string(
    'gcp_project', None,
    'Project name for the Cloud TPU-enabled project. If not specified, we '
    'will attempt to automatically detect the GCE project from metadata.')
flags.DEFINE_string(
    'tpu_zone', None,
    'GCE zone where the Cloud TPU is located in. If not specified, we '
    'will attempt to automatically detect the GCE project from metadata.')
flags.DEFINE_string(
    'tpu_name', None,
    'Name of the Cloud TPU for Cluster Resolvers. You must specify either '
    'this flag or --master.')

flags.DEFINE_string(
    'master', None,
    'GRPC URL of the master (e.g. grpc://ip.address.of.tpu:8470). You '
    'must specify either this flag or --tpu_name.')

flags.DEFINE_string('train_dir', '/tmp/deepvariant/',
                    'Directory where to write event logs.')

flags.DEFINE_boolean('use_tpu', False, 'use tpu if available')

flags.DEFINE_integer('worker_replicas', 1, 'Number of worker replicas.')

flags.DEFINE_integer(
    'ps_tasks', 0,
    'The number of parameter servers. If the value is 0, then the parameters '
    'are handled locally by the worker.')

flags.DEFINE_integer('task', 0, 'Task id of the replica running the training.')

flags.DEFINE_integer('number_of_steps', 8000000,
                     'Maximum number of global steps to take when training.')

flags.DEFINE_boolean('use_early_stopping', False, 'Use early stopping hook.')

flags.DEFINE_string(
    'early_stopping_directory', 'eval_on_tune',
    'Directory containing event files for early stopping hook to monitor.')

flags.DEFINE_string(
    'early_stopping_tag', 'F1/All',
    'The metric to monitor for early stopping (eg. loss, accuracy, etc.)')

flags.DEFINE_float(
    'early_stopping_plateau_delta', 1e-7,
    'The amount of change of a metric over num_plateau_steps that indicates '
    'the metric has stopped improving.')

flags.DEFINE_integer('early_stopping_num_plateau_steps', 1000000,
                     'Number of steps the metric needs to be plateaued for.')

flags.DEFINE_enum(
    'early_stopping_metric_direction', 'increase', ['increase', 'decrease'],
    'Whether to check if the metric has increased by delta or decreased by '
    'delta.')

flags.DEFINE_integer('early_stopping_every_n_steps', 10,
                     'Run early stopping hook every n steps.')

flags.DEFINE_integer(
    'num_retries', 0,
    'The number of times to retry on InternalError or UnavailableError.')

# Pre-trained model parameters
flags.DEFINE_string(
    'start_from_checkpoint', 'model_default',
    'A path to a checkpoint of model weights to initalize our model at the '
    'start of training. If None or "", the model will start from random weights'
    '. The special value "model_default" will use the default pretrained '
    'path for the selected model.')

flags.DEFINE_integer('max_checkpoints_to_keep', 10,
                     'Number of last checkpoints to keep during training. '
                     'Passing "0" preserves all checkpoints.')

flags.DEFINE_string(
    'kmp_blocktime', '0',
    'Value to set the KMP_BLOCKTIME environment variable to for efficient MKL '
    'training. See https://www.tensorflow.org/performance/performance_guide '
    'for more information. The default value is 0, which provides the best '
    'performance in our tests. Set this flag to "" to not set the variable.')


def loss(logits, one_hot_labels, label_smoothing):
  """Creates a loss function for training logits against one_hot_labels.

  Args:
      logits: tensor. logits of the model we want to train.
    one_hot_labels: One-hot encoded truth labels that we want to train this
      model to predict.
    label_smoothing: float. label_smoothing value for softmax_cross_entropy.

  Returns:
    A `Tensor` whose value represents the total loss.
  """
  slim.losses.softmax_cross_entropy(
      logits, one_hot_labels, label_smoothing=label_smoothing, weights=1.0)
  return slim.losses.get_total_loss()


def run(target, unused_is_chief, device_fn, use_tpu):
  """Run training.

  Args:
     target: The target of the TensorFlow standard server to use. Can be the
       empty string to run locally using an inprocess server.
     device_fn: Device function used to assign ops to devices.
     use_tpu: turn on tpu code path.
  """
  if not FLAGS.dataset_config_pbtxt:
    logging.error('Need to specify --dataset_config_pbtxt')
    return

  g = tf.Graph()
  with g.as_default():
    with tf.device(device_fn):
      # If ps_tasks is zero, the local device is used. When using multiple
      # (non-local) replicas, the ReplicaDeviceSetter distributes the variables
      # across the different devices.

      tf_dataset = data_providers.get_input_fn_from_dataset(
          dataset_config_filename=FLAGS.dataset_config_pbtxt,
          mode=tf.estimator.ModeKeys.TRAIN,
          use_tpu=use_tpu)
      model = modeling.get_model(FLAGS.model_name)
      logging.info('Running training on %s with model %s and tpu %s',
                   tf_dataset, FLAGS.model_name, use_tpu)

      batches_per_epoch = tf_dataset.num_examples // FLAGS.batch_size
      logging.info('Batches per epoch %s', batches_per_epoch)
      params = dict(batches_per_epoch=batches_per_epoch,)
      estimator = model.make_estimator(
          batch_size=FLAGS.batch_size,
          model_dir=FLAGS.train_dir,
          params=params,
          use_tpu=use_tpu,
          master=target,
          start_from_checkpoint=FLAGS.start_from_checkpoint,
      )

      training_hooks = None
      if FLAGS.use_early_stopping:
        # Early stopping hook depends on existence of events directory.
        eval_dir = os.path.join(FLAGS.train_dir, FLAGS.early_stopping_directory)
        tf.gfile.MakeDirs(eval_dir)

        plateau_decrease = True
        if FLAGS.early_stopping_metric_direction == 'increase':
          plateau_decrease = False

        early_stopping_hook = metrics_hook.EarlyStoppingHook(
            events_dir=eval_dir,
            tag=FLAGS.early_stopping_tag,
            num_plateau_steps=FLAGS.early_stopping_num_plateau_steps,
            plateau_delta=FLAGS.early_stopping_plateau_delta,
            plateau_decrease=plateau_decrease,
            every_n_steps=FLAGS.early_stopping_every_n_steps)

        training_hooks = [early_stopping_hook]

      estimator.train(
          input_fn=tf_dataset,
          max_steps=FLAGS.number_of_steps,
          hooks=training_hooks)


def parse_and_run():
  """Parse TF_CONFIG to cluster_spec and call run().

  TF_CONFIG environment variable is available when running using
  gcloud either locally or on cloud. It has all the information required
  to create a ClusterSpec which is important for running distributed code.

  Raises:
    ValueError: If flags are invalid.
  """
  tf_config = os.environ.get('TF_CONFIG')
  logging.info('TF_CONFIG %s', tf_config)

  for name in ['master', 'task', 'ps_tasks']:
    if getattr(FLAGS, name) and tf_config:
      raise ValueError(
          'Either the flag --%s or the environment variable TF_CONFIG can be'
          ' set but not both.' % name)

  # redacted
  #
  # If TF_CONFIG is not available we are either running locally in Cloud
  # or distributed inside Google. On Cloud the default values of
  # FLAGS.master and FLAGS.task correspond to running training locally.
  # Inside Google they will be set as needed to configure local or distributed
  # training. Inside Google we don't need to explicitly set worker_device
  # in replica_device_setter becaue this will be set automatically based
  # on various flags.
  if not tf_config:
    device_fn = tf.train.replica_device_setter(FLAGS.ps_tasks)
    # pylint: disable=g-long-ternary
    master = tf_utils.resolve_master(FLAGS.master, FLAGS.tpu_name,
                                     FLAGS.tpu_zone,
                                     FLAGS.gcp_project) if FLAGS.use_tpu else ''
    return run(
        master, FLAGS.task == 0, device_fn=device_fn, use_tpu=FLAGS.use_tpu)

  tf_config_json = json.loads(tf_config)

  cluster = tf_config_json.get('cluster')
  job_name = tf_config_json.get('task', {}).get('type')
  task_index = tf_config_json.get('task', {}).get('index')

  # If cluster information is empty run local
  if job_name is None or task_index is None:
    device_fn = tf.train.replica_device_setter(0)
    return run('', True, device_fn=device_fn, use_tpu=FLAGS.use_tpu)

  ps = cluster.get('ps', [])
  num_ps = len(ps)

  cluster_spec = tf.train.ClusterSpec(cluster)
  server = tf.train.Server(
      cluster_spec, job_name=job_name, task_index=task_index)

  if job_name == 'ps':
    server.join()
    return
  elif job_name in ['master', 'worker']:
    device_fn = tf.train.replica_device_setter(
        num_ps,
        worker_device='/job:%s/task:%d' % (job_name, task_index),
        cluster=cluster_spec)
    return run(
        server.target,
        job_name == 'master',
        device_fn=device_fn,
        use_tpu=FLAGS.use_tpu)


def main(_):
  """Run and handle retryable errors."""
  proto_utils.uses_fast_cpp_protos_or_die()

  logging_level.set_from_flag()

  if FLAGS.kmp_blocktime:
    os.environ['KMP_BLOCKTIME'] = FLAGS.kmp_blocktime
    logging.info('Set KMP_BLOCKTIME to %s', os.environ['KMP_BLOCKTIME'])

  for _ in range(FLAGS.num_retries + 1):
    try:
      parse_and_run()
      return
    except tf.errors.UnavailableError as e:
      # An UnavailableError indicates a gRPC error, typically this is
      # retryable.
      logging.error('Caught UnavailableError %s; will retry.', e)
    except tf.errors.InternalError as e:
      # Retry on an InternalError.
      logging.error('Caught InternalError %s; will retry.', e)


if __name__ == '__main__':
  tf.app.run()
