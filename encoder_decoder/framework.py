"""Encoder-decoder model with attention mechanism."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
if sys.version_info > (3, 0):
    from six.moves import xrange

import random
import numpy as np

import tensorflow as tf

from encoder_decoder import data_utils, graph_utils
from encoder_decoder.seq2seq import rnn_decoder


class EncoderDecoderModel(graph_utils.NNModel):

    def __init__(self, hyperparams, buckets=None, forward_only=False):
        """Create the model.

        Hyperparameters:
          source_vocab_size: size of the source vocabulary.
          target_vocab_size: size of the target vocabulary.
          buckets: a list of pairs (I, O), where I specifies maximum input length
            that will be processed in that bucket, and O specifies maximum output
            length. Training instances that have inputs longer than I or outputs
            longer than O will be pushed to the next bucket and padded accordingly.
            We assume that the list is sorted, e.g., [(2, 4), (8, 16)].
          size: number of units in each layer of the model.
          num_layers: number of layers in the model.
          max_gradient_norm: gradients will be clipped to maximally this norm.
          batch_size: the size of the batches used during training;
            the model construction is independent of batch_size, so it can be
            changed after initialization if this is convenient, e.g., for decoding.
          learning_rate: learning rate to start with.
          learning_rate_decay_factor: decay learning rate by this much when needed.
          use_lstm: if true, we use LSTM cells instead of GRU cells.
          num_samples: number of samples for sampled softmax.
          forward_only: if set, we do not construct the backward pass in the model.
          use_attention: if set, use attention model.
        """
        super(EncoderDecoderModel, self).__init__(hyperparams, buckets)
        self.learning_rate = tf.Variable(float(hyperparams["learning_rate"]),
                                         trainable=False)
        self.learning_rate_decay_op = self.learning_rate.assign(
            self.learning_rate * hyperparams["learning_rate_decay_factor"])

        self.global_epoch = tf.Variable(0, trainable=False)

        # Encoder.
        self.define_encoder(self.sc_input_keep, self.sc_output_keep)

        # Decoder.
        self.define_decoder(self.encoder.output_dim, self.tg_token_use_attention,
                            self.tg_token_attn_fun, self.tg_input_keep,
                            self.tg_output_keep)

        # Character Decoder.
        if self.tg_char:
            self.define_char_decoder(self.decoder.dim, False,
                    self.tg_char_rnn_input_keep, self.tg_char_rnn_output_keep)

        self.define_graph(forward_only)


    def define_graph(self, forward_only):
        self.debug_vars = []

        # Feeds for inputs.
        self.encoder_inputs = []        # encoder inputs.
        self.encoder_attn_masks = []    # mask out PAD symbols in the encoder
        self.decoder_inputs = []        # decoder inputs (always start with "_GO").
        self.target_weights = []        # weights at each position of the target sequence.
        self.pointer_targets = None

        for i in xrange(self.max_source_length):
            self.encoder_inputs.append(
                tf.placeholder(tf.int32, shape=[None],
                               name="encoder{0}".format(i)))
            self.encoder_attn_masks.append(
                tf.placeholder(tf.float32, shape=[None],
                               name="attn_alignment{0}".format(i)))
        self.encoder_channel_inputs = [self.encoder_inputs]
        if self.sc_char:
            self.char_encoder_inputs = []
            for i in xrange(self.max_source_length):
                self.char_encoder_inputs.append(
                    tf.placeholder(tf.int32,
                                   shape=[None, self.max_target_token_size],
                                   name="char_encoder{0}".format(i)))
            self.encoder_channel_inputs.append(self.char_encoder_inputs)
        for i in xrange(self.max_target_length + 1):
            self.decoder_inputs.append(
                tf.placeholder(tf.int32, shape=[None],
                               name="decoder{0}".format(i)))
            self.target_weights.append(
                tf.placeholder(tf.float32, shape=[None],
                               name="weight{0}".format(i)))
        # Our targets are decoder inputs shifted by one.
        self.targets = [self.decoder_inputs[i + 1]
                        for i in xrange(self.max_target_length)]
        if self.tg_char:
            # inputs for character generation
            self.char_decoder_inputs = []   # decoder inputs (always start with "_CGO")
                                            # [batch_size*max_target_token_size, dim]
            self.char_target_weights = []   # weights at each position of the target sequence
            for i in xrange(self.max_target_length):
                self.char_decoder_inputs.append(
                    tf.placeholder(tf.int32, shape=[None, self.max_target_token_size + 2],
                                   name="char_decoder{0}".format(i)))
                self.char_target_weights.append(
                    tf.placeholder(tf.float32, shape=[None, self.max_target_token_size + 1],
                                   name="char_target_weight{0}".format(i)))
            self.char_targets = [self.char_decoder_inputs[i][:, 1:]
                                 for i in xrange(self.max_target_length)]

        if self.use_copy:
            for i in xrange(self.max_target_length):
                self.pointer_targets = \
                    tf.placeholder(tf.int32, shape=[None, None, None],
                                   name="pointer_targets")

        # Compute training outputs and losses in the forward direction.
        if self.buckets:
            self.output_symbols = []
            self.output_logits = []
            self.losses = []
            self.attn_alignments = []
            self.pointers = []
            if self.tg_char:
                self.char_output_symbols = []
                self.char_output_logits = []
            for bucket_id, bucket in enumerate(self.buckets):
                print("creating bucket {} ({}, {})...".format(
                        bucket_id, bucket[0], bucket[1]))
                if bucket_id > 0:
                    tf.get_variable_scope().reuse_variables()
                encode_decode_outputs = \
                    self.encode_decode(
                        [channel_input[:bucket[0]] \
                         for channel_input in self.encoder_channel_inputs],
                        self.encoder_attn_masks[:bucket[0]],
                        self.decoder_inputs[:bucket[1]],
                        self.targets[:bucket[1]],
                        self.target_weights[:bucket[1]],
                        forward_only=forward_only
                    )
                bucket_output_symbols, bucket_output_logits, bucket_losses, \
                    batch_attn_alignments = encode_decode_outputs[:4]
                self.output_symbols.append(bucket_output_symbols)
                self.output_logits.append(bucket_output_logits)
                self.losses.append(bucket_losses)
                self.attn_alignments.append(batch_attn_alignments)
                if forward_only and self.tg_char:
                    bucket_char_output_symbols, bucket_char_output_logits = \
                        encode_decode_outputs[4:6]
                    self.char_output_symbols.append(
                        tf.reshape(bucket_char_output_symbols,
                                   [self.max_target_length,
                                    self.batch_size, self.beam_size,
                                    self.max_target_token_size + 1]))
                    self.char_output_logits.append(
                        tf.reshape(bucket_char_output_logits,
                                   [self.max_target_length,
                                    self.batch_size, self.beam_size]))
                if self.use_copy:
                    self.pointers.append(encode_decode_outputs[-1])
        else:
            encode_decode_outputs = self.encode_decode(
                                        self.encoder_channel_inputs,
                                        self.encoder_attn_masks,
                                        self.decoder_inputs,
                                        self.targets,
                                        self.target_weights,
                                        forward_only=forward_only
                                    )
            self.output_symbols, self.output_logits, self.losses, \
                self.attn_alignments = encode_decode_outputs[:4]
            if self.tg_char:
                char_output_symbols, char_output_logits = \
                    encode_decode_outputs[4:6]
                self.char_output_symbols = tf.reshape(char_output_symbols,
                                   [self.batch_size, self.beam_size,
                                    self.max_target_length,
                                    self.max_target_token_size])
                self.char_output_logits = tf.reshape(char_output_logits,
                                   [self.batch_size, self.beam_size,
                                    self.max_target_length])
            if forward_only and self.use_copy:
                self.pointers = encode_decode_outputs[-1]


        # Gradients and SGD updates in the backward direction.
        if not forward_only:
            params = tf.trainable_variables()
            if self.optimizer == "sgd":
                opt = tf.train.GradientDescentOptimizer(self.learning_rate)
            elif self.optimizer == "adam":
                opt = tf.train.AdamOptimizer(self.learning_rate, beta1=0.9,
                                             beta2=0.999, epsilon=1e-08)
            else:
                raise ValueError("Unrecognized optimizer type.")

            if self.buckets:
                self.gradient_norms = []
                self.updates = []
                for bucket_id, _ in enumerate(self.buckets):
                    gradients = tf.gradients(self.losses[bucket_id], params)
                    clipped_gradients, norm = tf.clip_by_global_norm(
                        gradients, self.max_gradient_norm)
                    self.gradient_norms.append(norm)
                    self.updates.append(opt.apply_gradients(
                        zip(clipped_gradients, params)))
            else:
                gradients = tf.gradients(self.losses, params)
                clipped_gradients, norm = tf.clip_by_global_norm(
                    gradients, self.max_gradient_norm)
                self.gradient_norms = norm
                self.updates = opt.apply_gradients(zip(clipped_gradients, params))

        self.saver = tf.train.Saver(tf.global_variables())


    def encode_decode(self, encoder_channel_inputs, encoder_attn_masks,
                      decoder_inputs, targets, target_weights, forward_only):

        encoder_outputs, encoder_state = \
            self.encoder.define_graph(encoder_channel_inputs)
        if self.tg_token_use_attention:
            top_states = [tf.reshape(e, [-1, 1, self.encoder.output_dim])
                          for e in encoder_outputs]
            attention_states = tf.concat(1, top_states)
        else:
            attention_states = None
        
        # Losses.
        num_heads = 2 if (self.tg_token_use_attention and self.use_copy) else 1

        output_symbols, output_logits, outputs, states, attn_alignments, \
            pointers = self.decoder.define_graph(
                        encoder_state, decoder_inputs, encoder_attn_masks,
                        attention_states, num_heads=num_heads,
                        forward_only=forward_only)
        if forward_only or self.training_algorithm == "standard":
            encoder_decoder_token_loss = self.sequence_loss(
                       outputs, targets, target_weights,
                       graph_utils.softmax_loss(
                           self.decoder.token_output_projection,
                           self.num_samples,
                           self.target_vocab_size))
        else:
            raise AttributeError("Unrecognized training algorithm.")

        attention_reg = self.attention_regularization(attn_alignments) \
            if self.tg_token_use_attention else 0
        if forward_only and self.token_decoding_algorithm == 'beam_search':
            pointer_targets = self.decoder.beam_decoder.wrap_input(
                                self.pointer_targets)
        else:
            pointer_targets = self.pointer_targets
        copy_loss = self.copy_loss(pointers, pointer_targets) if self.use_copy else 0

        if self.tg_char:
            # re-arrange character inputs
            char_decoder_inputs = [tf.squeeze(x, 1)
                            for x in tf.split(1, self.max_target_token_size + 2,
                            tf.concat(0, self.char_decoder_inputs))]
            char_targets = [tf.squeeze(x, 1) for x in
                            tf.split(1, self.max_target_token_size + 1,
                                     tf.concat(0, self.char_targets))]
            char_target_weights = [tf.squeeze(x, 1) for x in
                            tf.split(1, self.max_target_token_size + 1,
                                     tf.concat(0, self.char_target_weights))]
            if forward_only and self.token_decoding_algorithm == 'beam_search':
                char_decoder_inputs = graph_utils.wrap_inputs(
                    self.decoder.beam_decoder, char_decoder_inputs)
                char_targets = graph_utils.wrap_inputs(
                    self.decoder.beam_decoder, char_targets)
                char_target_weights = graph_utils.wrap_inputs(
                    self.decoder.beam_decoder, char_target_weights)
            # get initial state from decoder output
            char_decoder_init_state = tf.concat(
                0, [tf.reshape(d_o, [-1, self.decoder.dim]) for d_o in states])
            char_output_symbols, char_output_logits, char_outputs, _, _ = \
                self.char_decoder.define_graph(char_decoder_init_state,
                                               char_decoder_inputs,
                                               forward_only=forward_only)
            encoder_decoder_char_loss = self.sequence_loss(
                char_outputs, char_targets, char_target_weights,
                graph_utils.softmax_loss(
                    self.char_decoder.token_output_projection,
                    self.tg_char_vocab_size,
                    self.tg_char_vocab_size))
        else:
            encoder_decoder_char_loss = 0
       
        losses = encoder_decoder_token_loss + \
                 self.gamma * encoder_decoder_char_loss + \
                 self.chi * copy_loss + \
                 self.beta * attention_reg
        # losses = self.beta * attention_reg
        # losses = encoder_decoder_token_loss
        # losses = self.chi * copy_loss

        # store encoder/decoder output states
        self.encoder_hidden_states = tf.concat(
            1, [tf.reshape(e_o, [-1, 1, self.encoder.output_dim])
                for e_o in encoder_outputs])
        self.decoder_hidden_states = tf.concat(
            1, [tf.reshape(d_o, [-1, 1, self.decoder.dim])
                for d_o in states])

        O = [output_symbols, output_logits, losses, attn_alignments]
        if self.tg_char:
            O.append(char_output_symbols)
            O.append(char_output_logits)
        if self.use_copy:
            O.append(pointers_targets)
        return O


    # Loss functions.
    def sequence_loss(self, logits, targets, target_weights, loss_function):
        targets = targets[:len(logits)]
        weights = target_weights[:len(logits)]

        with tf.variable_scope("sequence_loss"):
            log_perp_list = []
            for logit, target, weight in zip(logits, targets, weights):
                crossent = loss_function(logit, target)
                log_perp_list.append(crossent * weight)
            log_perps = tf.add_n(log_perp_list)
            total_size = tf.add_n(weights)
            total_size += 1e-12     # Just to avoid division by 0 for all-0 weights.
            log_perps /= total_size

        avg_log_perps = tf.reduce_mean(log_perps)

        return avg_log_perps


    def copy_loss(self, pointers, pointer_targets):
        raw_loss = tf.reshape(
                tf.nn.softmax_cross_entropy_with_logits(
                     tf.reshape(pointers, [-1, self.max_source_length]), 
                     tf.reshape(pointer_targets, [-1, self.max_source_length])),
                [-1, self.max_target_length])
        copy_positions = tf.reduce_sum(pointer_targets, 2)
        return tf.reduce_mean(tf.reduce_sum(
                    tf.mul(tf.cast(copy_positions, tf.float32), raw_loss), 1))


    def attention_regularization(self, attn_alignments):
        """Entropy regularization term.

        :param attn_alignments: [batch_size, decoder_size, encoder_size]
        """
        # P_unnorm = tf.reduce_sum(attn_alignments, 1)
        # Z = tf.reduce_sum(P_unnorm, 1, keep_dims=True)
        # P = P_unnorm / Z
        # return tf.reduce_mean(tf.reduce_sum(P * tf.log(P), 1))

        P = tf.reduce_sum(attn_alignments, 1)
        P_exp = tf.exp(P)
        Z = tf.reduce_sum(P_exp, 1, keep_dims=True)
        return tf.reduce_mean(tf.reduce_sum(P_exp / Z * (P - tf.log(Z)), 1))


    def define_encoder(self, input_keep, output_keep):
        """Placeholder function."""
        self.encoder = None


    def define_decoder(self, dim, use_attention, attention_function,
                       input_keep, output_keep):
        """Placeholder function."""
        self.decoder = None

    def define_char_decoder(self, dim, use_attention, input_keep, output_keep):
        """
        Define the decoder which does character-level generation of a token.
        """
        if self.tg_char_composition == 'rnn':
            self.char_decoder = rnn_decoder.RNNDecoder(self.hyperparams,
                "char_decoder", self.tg_char_vocab_size, dim,
                use_attention, input_keep, output_keep,
                self.char_decoding_algorithm)
        else:
            raise ValueError("Unrecognized target character composition: {}."
                             .format(self.tg_char_composition))

    def format_example(self, encoder_channel_inputs, decoder_channel_inputs,
                       pointer_targets=None, bucket_id=-1):
        """
        Prepare the data to be fed into the neural model.

        :param encoder_channel_inputs: list of (batch of) sequence
            indices for different encoder channels [[...], [...], ...]
        :param decoder_channel_inputs: list of (batch of) sequence
            indices for different decoder channels [[...], [...], ...]
        :param pointer_targets: batch of copying index matrices
            [[...], [...] ...] if use_copy is true.
        :param bucket_id: bucket id of the current batch

        Returns:
            batch_encoder_channel_inputs: list of input indices
            (batched, padded and reversed) for different encoder channels
            batch_encoder_input_masks: encoder input masks
            (mask out padding symbols, batched)
            batch_decoder_inputs: decoder input indices
            (batched, padded)
            batch_decoder_input_masks: decoder input masks
            (mask out padding symbols, batched)
        """
        def load_channel(inputs, input_size, encoder_channel=True):
            # Encoder inputs are padded and then reversed
            # Decoder inputs are padded but not reversed
            padded_inputs = []
            batch_inputs = []
            for batch_idx in xrange(batch_size):
                input = inputs[batch_idx]
                paddings = [data_utils.PAD_ID] * (input_size - len(input))
                if encoder_channel:
                    padded_inputs.append(list(reversed(input + paddings)))
                else:
                    padded_inputs.append(input + paddings)
            for length_idx in xrange(input_size):
                batch_inputs.append(
                    np.array([padded_inputs[batch_idx][length_idx]
                          for batch_idx in xrange(batch_size)], dtype=np.int32))
            return batch_inputs

        if bucket_id >= 0:
            encoder_size, decoder_size = self.buckets[bucket_id]
        else:
            encoder_size, decoder_size = self.max_source_length, \
                                         self.max_target_length

        batch_size = len(encoder_channel_inputs[0])
        # create batch-major vectors
        batch_encoder_inputs = load_channel(
            encoder_channel_inputs[0], encoder_size, encoder_channel=True)
        if len(encoder_channel_inputs) > 1:
            batch_encoder_full_inputs = load_channel(
                encoder_channel_inputs[1], encoder_size, encoder_channel=True)
        batch_decoder_inputs = load_channel(
            decoder_channel_inputs[0], decoder_size, encoder_channel=False)
        if len(decoder_channel_inputs) > 1:
            batch_decoder_full_inputs = load_channel(
                decoder_channel_inputs[1], decoder_size, encoder_channel=False)
        
        batch_encoder_input_masks = []
        batch_decoder_input_masks = []
        # Batch encoder inputs are just re-indexed encoder_inputs.
        for length_idx in xrange(encoder_size):
            batch_encoder_input_mask = np.ones(batch_size, dtype=np.float32)
            for batch_idx in xrange(batch_size):
                source = batch_encoder_inputs[length_idx][batch_idx]
                if source == data_utils.PAD_ID:
                    batch_encoder_input_mask[batch_idx] = 0.0
            batch_encoder_input_masks.append(batch_encoder_input_mask)
        # Batch decoder inputs are re-indexed decoder_inputs.
        for length_idx in xrange(decoder_size):
            # Create target_weights to be 0 for targets that are padding.
            batch_decoder_input_mask = np.ones(batch_size, dtype=np.float32)
            for batch_idx in xrange(batch_size):
                # We set weight to 0 if the corresponding target is a PAD symbol.
                # The corresponding target is decoder_input shifted by 1 forward.
                if length_idx < decoder_size - 1:
                    target = batch_decoder_inputs[length_idx+1][batch_idx]
                if length_idx == decoder_size - 1 or target == data_utils.PAD_ID:
                    batch_decoder_input_mask[batch_idx] = 0.0
            batch_decoder_input_masks.append(batch_decoder_input_mask)

        E = Example()
        E.encoder_inputs = batch_encoder_inputs
        E.encoder_attn_masks = batch_encoder_input_masks
        E.decoder_inputs = batch_decoder_inputs
        E.target_weights = batch_decoder_input_masks

        if self.sc_char:
            sc_char_features = np.load(self.sc_char_features_path)
            batch_char_encoder_inputs = []
            for input in batch_encoder_full_inputs:
                batch_char_encoder_input = sc_char_features[input]
                batch_char_encoder_inputs.append(batch_char_encoder_input)
            E.char_encoder_inputs = batch_char_encoder_inputs
        if self.tg_char:
            tg_char_features = np.load(self.tg_char_features_path)
            tg_char_features = np.concatenate([np.expand_dims(
                np.array([data_utils.CGO_ID] * tg_char_features.shape[0]), 1),
                tg_char_features], 1)
            batch_char_decoder_inputs = []
            batch_char_target_weights = []
            for input in batch_decoder_full_inputs[1:]:
                batch_char_decoder_input = tg_char_features[input]
                batch_char_decoder_inputs.append(batch_char_decoder_input)
                batch_char_target_weights.append(np.array(
                    batch_char_decoder_input[:, 1:] != data_utils.CPAD_ID,
                    dtype=np.int64))
            # apply a dummy final char decoder input
            batch_char_decoder_inputs.append(
                np.ones(batch_char_decoder_input.shape) * data_utils.CPAD_ID)
            batch_char_target_weights.append(
                np.zeros(batch_char_decoder_input[:, 1:].shape))
            assert(len(batch_char_decoder_inputs) == decoder_size)
            assert(batch_char_decoder_input.shape[0] == self.batch_size)
            assert(batch_char_decoder_input.shape[1] == self.max_target_token_size + 2)
            assert(batch_char_target_weights[0].shape[0] == self.batch_size)
            assert(batch_char_target_weights[0].shape[1] == self.max_target_token_size + 1)
            E.char_decoder_inputs = batch_char_decoder_inputs
            E.char_target_weights = batch_char_target_weights
        if self.use_copy:
            # if len(pointer_targets) == 1:
            #     E.pointer_targets = pointer_targets[:, :decoder_size, :encoder_size]
            # else:
            E.pointer_targets = np.concatenate(pointer_targets, 0)[:, 
                :decoder_size, :encoder_size]

        return E


    def get_batch(self, data, bucket_id):
        """Get a random batch of data from the specified bucket, prepare for step.

        To feed data in step(..) it must be a list of batch-major vectors, while
        data here contains single length-major cases. So the main logic of this
        function is to re-index data cases to be in the proper format for feeding.

        Args:
          data: a tuple of size len(self.buckets) in which each element contains
            lists of pairs of input and output data that we use to create a batch.
          bucket_id: integer, which bucket to get the batch for.
          add_extra_go: if set to True, add an extra "GO" symbol to decoder inputs.
        Returns:
          The triple (encoder_inputs, decoder_inputs, target_weights) for
          the constructed batch that has the proper format to call step(...) later.
        """
        encoder_inputs, encoder_full_inputs, decoder_inputs, \
            decoder_full_inputs = [], [], [], []
        pointer_targets = []

        # Get a random batch of encoder and decoder inputs from data,
        # pad them if needed, reverse encoder inputs and add GO to decoder.
        for _ in xrange(self.batch_size):
            random_example = random.choice(data[bucket_id])
            encoder_inputs.append(random_example[2])
            encoder_full_inputs.append(random_example[4])
            decoder_inputs.append(random_example[3])
            decoder_full_inputs.append(random_example[5])

            if self.use_copy:
                pointer_targets.append(random_example[-1])

        return self.format_example([encoder_inputs, encoder_full_inputs],
                                   [decoder_inputs, decoder_full_inputs],
                                   pointer_targets=pointer_targets,
                                   bucket_id=bucket_id)


    def get_bucket(self, data, bucket_id):
        """Get all data points from the specified bucket, prepare for step.
        """
        encoder_inputs, encoder_full_inputs, decoder_inputs, \
            decoder_full_inputs = [], [], [], []
        pointer_targets = []

        for i in xrange(len(data[bucket_id])):
            encoder_inputs.append(data[bucket_id][i][2])
            encoder_full_inputs.append(data[bucket_id][i][4])
            decoder_inputs.append(data[bucket_id][i][3])
            decoder_full_inputs.append(data[bucket_id][i][5])
            if self.use_copy:
                pointer_targets.append(data[bucket_id][i][-1])

        return self.format_example([encoder_inputs, encoder_full_inputs],
                                   [decoder_inputs, decoder_full_inputs],
                                   pointer_targets=pointer_targets,
                                   bucket_id=bucket_id)


    def feed_input(self, E):
        """
        Assign the data vectors to the corresponding neural network variables.
        """
        encoder_size, decoder_size = len(E.encoder_inputs), \
                                     len(E.decoder_inputs)

        input_feed = {}
        for l in xrange(encoder_size):
            input_feed[self.encoder_inputs[l].name] = E.encoder_inputs[l]
            if self.sc_char:
                input_feed[self.char_encoder_inputs[l].name] = E.char_encoder_inputs[l]
            input_feed[self.encoder_attn_masks[l].name] = E.encoder_attn_masks[l]
        # print("Second E.decoder_inputs: {}".format(E.decoder_inputs[1]))
        for l in xrange(decoder_size):
            input_feed[self.decoder_inputs[l].name] = E.decoder_inputs[l]
            input_feed[self.target_weights[l].name] = E.target_weights[l]
        # Since our targets are decoder inputs shifted by one, we need one more.
        last_target = self.decoder_inputs[decoder_size].name
        input_feed[last_target] = np.zeros(E.decoder_inputs[0].shape, dtype=np.int32)

        if self.tg_char:
            for l in xrange(decoder_size):
                input_feed[self.char_decoder_inputs[l].name] = \
                    E.char_decoder_inputs[l]
                input_feed[self.char_target_weights[l].name] = \
                    E.char_target_weights[l]

        if self.use_copy:
            input_feed[self.pointer_targets.name] = E.pointer_targets

        return input_feed


    def step(self, session, formatted_example, bucket_id=-1, forward_only=False,
             return_rnn_hidden_states=False):
        """Run a step of the model feeding the given inputs.
        :param session: tensorflow session to use.
        :param encoder_inputs: list of numpy int vectors to feed as encoder inputs.
        :param attn_alignments: list of numpy int vectors to feed as the mask over inputs
            about which tokens to attend to.
        :param decoder_inputs: list of numpy int vectors to feed as decoder inputs.
        :param target_weights: list of numpy float vectors to feed as target weights.
        :param bucket_id: which bucket of the model to use.
        :param forward_only: whether to do the backward step or only forward.
        :param return_rnn_hidden_states: if set to True, return the hidden states of the
            two RNNs.
        :return (gradient_norm, average_perplexity, outputs)
        """

        # Input feed: encoder inputs, decoder inputs, target_weights, as provided.
        input_feed = self.feed_input(formatted_example)

        # Output feed: depends on whether we do a backward step or not.
        if not forward_only:
            if bucket_id == -1:
                output_feed = {
                    'updates': self.updates,                    # Update Op that does SGD.
                    'gradient_norms': self.gradient_norms,      # Gradient norm.
                    'losses': self.losses}                      # Loss for this batch.
            else:
                output_feed = {
                    'updates': self.updates[bucket_id],         # Update Op that does SGD.
                    'gradient_norms': self.gradient_norms[bucket_id],  # Gradient norm.
                    'losses': self.losses[bucket_id]}           # Loss for this batch.
        else:
            if bucket_id == -1:
                output_feed = {
                    'output_symbols': self.output_symbols,      # Loss for this batch.
                    'output_logits': self.output_logits,        # Batch output sequence
                    'losses': self.losses}                      # Batch output scores
            else:
                output_feed = {
                    'output_symbols': self.output_symbols[bucket_id], # Loss for this batch.
                    'output_logits': self.output_logits[bucket_id],   # Batch output sequence
                    'losses': self.losses[bucket_id]}           # Batch output logits
        
        if self.tg_token_use_attention:
            if bucket_id == -1:
                output_feed['attn_alignments'] = self.attn_alignments
            else:
                output_feed['attn_alignments'] = self.attn_alignments[bucket_id]

        output_feed['encoder_hidden_states'] = self.encoder_hidden_states
        output_feed['decoder_hidden_states'] = self.decoder_hidden_states
        
        if forward_only and self.tg_char:
            if bucket_id == -1:
                output_feed['char_output_symbols'] = self.char_output_symbols
                output_feed['char_output_logits'] = self.char_output_logits
            else:
                output_feed['char_output_symbols'] = \
                    self.char_output_symbols[bucket_id]
                output_feed['char_output_logits'] = \
                    self.char_output_logits[bucket_id]

        if self.use_copy:
            if bucket_id == -1:
                output_feed['pointers'] = self.pointers
            else:
                output_feed['pointers'] = self.pointers[bucket_id]

        outputs = session.run(output_feed, input_feed)

        O = Output()
        if not forward_only:
            # Gradient norm, loss, no outputs
            O.gradient_norms = outputs['gradient_norms']
            O.losses = outputs['losses']
        else:
            # No gradient loss, output_symbols, output_logits
            O.output_symbols = outputs['output_symbols']
            O.output_logits = outputs['output_logits']
            O.losses = outputs['losses']
        # [attention_masks]
        if self.tg_token_use_attention:
            O.attn_alignments = outputs['attn_alignments']

        O.encoder_hidden_states = outputs['encoder_hidden_states']
        O.decoder_hidden_states = outputs['decoder_hidden_states']

        if self.tg_char:
            O.char_output_symbols = outputs['char_output_symbols']
            O.char_output_logits = outputs['char_output_logits']

        if self.use_copy:
            O.pointers = outputs['pointers']

        return O


class Example(object):
    """
    Input data to the neural network (batched when mini-batch training is used).
    """
    def __init__(self):
        self.encoder_inputs = None
        self.encoder_attn_masks = None
        self.decoder_inputs = None
        self.target_weights = None
        self.char_decoder_inputs = None
        self.char_target_weights = None
        self.pointer_targets = None


class Output(object):
    """
    Data output from the neural network (batched when mini-batch training is
    used).
    """
    def __init__(self):
        self.updates = None
        self.gradient_norms = None
        self.losses = None
        self.output_symbols = None
        self.output_logits = None
        self.attn_alignments = None
        self.encoder_hidden_states = None
        self.decoder_hidden_states = None
        self.char_output_symbols = None
        self.char_output_logits = None
