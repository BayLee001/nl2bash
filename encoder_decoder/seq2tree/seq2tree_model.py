"""Sequence-to-tree model with an attention mechanism."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from encoder_decoder import EncoderDecoderModel
import encoder, tree_decoder


class Seq2TreeModel(EncoderDecoderModel):
    """Sequence-to-tree models.
    """
    def __init__(self, hyperparams, buckets=None, forward_only=False):
        """
        Create the model.
        :param hyperparams: learning hyperparameters
        :param buckets: if not None, train bucket model.
        :param forward_only: if set, we do not construct the backward pass.
        """
        super(Seq2TreeModel, self).__init__(hyperparams, buckets, forward_only)


    def define_encoder(self):
        """Construct sequence encoders."""
        if self.encoder_topology == "rnn":
            self.encoder = encoder.RNNEncoder(self.hyperparameters)
        elif self.encoder_topology == "birnn":
            self.encoder = encoder.BiRNNEncoder(self.hyperparameters)
        else:
            raise ValueError("Unrecognized encoder type.")


    def define_decoder(self):
        """Construct tree decoders."""
        if self.decoder_topology == "basic_tree":
            self.decoder = tree_decoder.BasicTreeDecoder(self.hyperparameters,
                                                         self.output_projection())
        else:
            raise ValueError("Unrecognized decoder topology: {}."
                             .format(self.decoder_topology))
