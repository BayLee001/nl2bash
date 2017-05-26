#!/bin/sh

# Set up path to CUDA library
source ~/.profile

export PYTHONPATH=`pwd`'/..'

ARGS=${@:1}

python3 -m encoder_decoder.translate \
    --nl_known_vocab_size 700 \
    --cm_known_vocab_size 400 \
    --nl_vocab_size 3100 \
    --cm_vocab_size 3400 \
    --encoder_topology birnn \
    --batch_size 32 \
    --num_epochs 100 \
    --num_samples 256 \
    --token_decoding_algorithm beam_search \
    --beam_size 100 \
    --alpha 1.0 \
    --num_nn_slot_filling 5 \
    ${ARGS}

