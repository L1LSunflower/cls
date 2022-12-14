from __future__ import division, print_function, absolute_import
import os
import sys
import tensorflow as tf

from data_processing import *

tf.app.flags.DEFINE_integer('training_iteration', 50,
                            'number of training iterations.')
tf.app.flags.DEFINE_integer('model_version', 1, 'version number of the model.')
tf.app.flags.DEFINE_string('work_dir', '/tmp', 'Working directory.')
FLAGS = tf.app.flags.FLAGS

def main(_):
    if len(sys.argv) < 2 or sys.argv[-1].startswith('-'):
    	print('Usage: mnist_export.py [--training_iteration=x] '
    	  '[--model_version=y] export_dir')
    	sys.exit(-1)
    if FLAGS.training_iteration <= 0:
    	print('Please specify a positive value for training iteration.')
    	sys.exit(-1)
    if FLAGS.model_version <= 0:
    	print('Please specify a positive value for version number.')
    	sys.exit(-1)

    # Training Parameters
    learning_rate = 0.0001
    batch_size = 1
    display_step = 1

    # Network Parameters
    num_input = 784
    num_classes = 3
    dropout = 0.75 # Dropout, probability to keep units
    sess = tf.InteractiveSession() # InteractiveSession need to save model

    # Import correct data from script
    training_images = train_data_with_label()
    testing_images = test_data_with_label()
    tr_img_data = numpy.array([i[0] for i in training_images])
    tr_lbl_data = numpy.array([i[1] for i in training_images])
    tst_img_data = numpy.array([i[0] for i in testing_images])
    tst_lbl_data = numpy.array([i[1] for i in testing_images])
    print("DATA SHAPE: ", tr_img_data.shape)

    # tf Graph input
    X = tf.placeholder(tf.float32, [None, num_input], name="first_placeholder")
    Y = tf.placeholder(tf.float32, [None, num_classes], name="second_placeholder")
    keep_prob = tf.placeholder(tf.float32) # dropout (keep probability)


    # Create some wrappers for simplicity
    def conv2d(x, W, b, strides=1):
        # Conv2D wrapper, with bias and relu activation
        x = tf.nn.conv2d(x, W, strides=[1, strides, strides, 1], padding='SAME')
        x = tf.nn.bias_add(x, b)
        return tf.nn.relu(x)


    def maxpool2d(x, k=2):
        # MaxPool2D wrapper
        return tf.nn.max_pool(x, ksize=[1, k, k, 1], strides=[1, k, k, 1],
                              padding='SAME')


    # Create model
    def conv_net(x, weights, biases, dropout):
        # MNIST data input is a 1-D vector of 784 features (28*28 pixels)
        # Reshape to match picture format [Height x Width x Channel]
        # Tensor input become 4-D: [Batch Size, Height, Width, Channel]
        x = tf.reshape(x, shape=[-1, 28, 28, 1])

        # Convolution Layer
        conv1 = conv2d(x, weights['wc1'], biases['bc1'])
        # Max Pooling (down-sampling)
        conv1 = maxpool2d(conv1, k=2)

        # Convolution Layer
        conv2 = conv2d(conv1, weights['wc2'], biases['bc2'])
        # Max Pooling (down-sampling)
        conv2 = maxpool2d(conv2, k=2)

        # Fully connected layer
        # Reshape conv2 output to fit fully connected layer input
        fc1 = tf.reshape(conv2, [-1, weights['wd1'].get_shape().as_list()[0]])
        fc1 = tf.add(tf.matmul(fc1, weights['wd1']), biases['bd1'])
        fc1 = tf.nn.relu(fc1)
        # Apply Dropout
        fc1 = tf.nn.dropout(fc1, dropout)

        # Output, class prediction
        out = tf.add(tf.matmul(fc1, weights['out']), biases['out'])
        return out

    # Store layers weight & bias
    weights = {
        # 5x5 conv, 1 input, 32 outputs
        'wc1': tf.Variable(tf.random_normal([5, 5, 1, 32])),
        # 5x5 conv, 32 inputs, 64 outputs
        'wc2': tf.Variable(tf.random_normal([5, 5, 32, 64])),
        # fully connected, 7*7*64 inputs, 1024 outputs
        'wd1': tf.Variable(tf.random_normal([7*7*64, 1024])),
        # 1024 inputs, 10 outputs (class prediction)
        'out': tf.Variable(tf.random_normal([1024, num_classes]))
    }

    biases = {
        'bc1': tf.Variable(tf.random_normal([32])),
        'bc2': tf.Variable(tf.random_normal([64])),
        'bd1': tf.Variable(tf.random_normal([1024])),
        'out': tf.Variable(tf.random_normal([num_classes]))
    }

    # Construct model
    logits = conv_net(X, weights, biases, keep_prob)
    prediction = tf.nn.softmax(logits)
    # Define loss and optimizer
    loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
        logits=logits, labels=Y))
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
    train_op = optimizer.minimize(loss_op)


    # Evaluate model
    correct_pred = tf.equal(tf.argmax(prediction, 1), tf.argmax(Y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))
    #rofl = tf.argmax(prediction, 1)
    # Initialize the variables (i.e. assign their default value)
    init = tf.global_variables_initializer()
    # Initialize all variables
    sess.run(init)
    # Train model
    print('Training model...')
    # Start training

    for step in range(1, FLAGS.training_iteration+1):
        for iteration in range(len(tr_img_data)):
            if(iteration == len(tr_img_data)):
                iteration = 0
                break
            print(iteration)
            batch_x = tr_img_data[iteration,:].reshape(1, tr_img_data.shape[1])
            batch_y = tr_lbl_data[iteration,:].reshape(1, tr_lbl_data.shape[1])
            # Run optimization op (backprop)
            sess.run(train_op, feed_dict={X: batch_x, Y: batch_y, keep_prob: 0.8})
        if step % display_step == 0 or step == 1:
            # Calculate batch loss and accuracy
            loss, acc = sess.run([loss_op, accuracy], feed_dict={X: batch_x,
                                                                    Y: batch_y,
                                                                    keep_prob: 1.0})

        print("Step " + str(step) + ", Minibatch Loss= " + \
              "{:.4f}".format(loss) + ", Training Accuracy= " + \
              "{:.3f}".format(acc))

    print("Optimization Finished!")

    test_batch_x = tst_img_data[:, :]
    test_batch_y = tst_lbl_data[:, :]
    print("Testing Accuracy:", \
        sess.run(accuracy, feed_dict={X: test_batch_x,
                                      Y: test_batch_y,
                                      keep_prob: 0.8}))

    print("Testing Prediction:", sess.run(prediction, feed_dict={X: test_batch_x, keep_prob: 0.8}))
    probs = sess.run(logits, feed_dict={X: test_batch_x[0].reshape(1,-1), keep_prob: 0.8})
    probabilities = numpy.argmax(probs, 0)
    print(" Testing probabilities ",probs)

    # Path to save model
    export_path_base = sys.argv[-1]
    export_path = os.path.join(
    tf.compat.as_bytes(export_path_base),
    tf.compat.as_bytes(str(FLAGS.model_version)))
    print('Exporting trained model to', export_path)
    builder = tf.saved_model.builder.SavedModelBuilder(export_path)
    # Build the signature_def_map.
    classify_inputs = tf.saved_model.utils.build_tensor_info(X) # Save first_placeholder to take prediction
    classify_keep_prob = tf.saved_model.utils.build_tensor_info(keep_prob) # Probability
    classify_outputs_prediction = tf.saved_model.utils.build_tensor_info(prediction) # Save predcition function
    classify_signature = (
    tf.saved_model.signature_def_utils.build_signature_def(
    inputs={
        tf.saved_model.signature_constants.CLASSIFY_INPUTS:classify_inputs
    },
    outputs={
        tf.saved_model.signature_constants.CLASSIFY_OUTPUT_CLASSES:classify_outputs_prediction,
    },
    method_name=tf.saved_model.signature_constants.CLASSIFY_METHOD_NAME
    ))

    tensor_info_x = tf.saved_model.utils.build_tensor_info(X) # Save first_placeholder to take prediction
    tensor_keep_prob = tf.saved_model.utils.build_tensor_info(keep_prob)
    tensor_info_prediction = tf.saved_model.utils.build_tensor_info(prediction) # Save cost function
    tensor_info_logits = tf.saved_model.utils.build_tensor_info(logits) # Save cost function

    prediction_signature = (
    tf.saved_model.signature_def_utils.build_signature_def(
    inputs={'input':tensor_info_x,
            'prob': tensor_keep_prob},
    outputs={'output':tensor_info_prediction},
    method_name=tf.saved_model.signature_constants.PREDICT_METHOD_NAME))

    legacy_init_op = tf.group(tf.tables_initializer(), name='legacy_init_op')
    builder.add_meta_graph_and_variables(
    sess, [tf.saved_model.tag_constants.SERVING],
    signature_def_map={
        'predict':
            prediction_signature,
        tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY:
            classify_signature,
    },
    legacy_init_op = legacy_init_op)

    builder.save()
    print("Done exporting!")
    writer = tf.summary.FileWriter(export_path_base) # Path to save tensorboard file
    writer.add_graph(sess.graph) # Save tensorboard
    merged_summary = tf.summary.merge_all()

if __name__ == '__main__':
    tf.app.run()
