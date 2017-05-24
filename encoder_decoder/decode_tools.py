from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, sys
if sys.version_info > (3, 0):
    from six.moves import xrange
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import datetime, time
import numpy as np
import shutil

from encoder_decoder import classifiers, data_utils
from bashlex import data_tools
from nlp_tools import constants, slot_filling, tokenizer


APOLOGY_MSG = \
    "Sorry, I don't know how to translate this command at the moment."


def demo(sess, model, FLAGS):
    """
    Simple command line decoding interface.
    """
    slot_filling_classifier = None
    if FLAGS.fill_argument_slots:
        # create slot filling classifier
        mapping_param_dir = os.path.join(
            FLAGS.model_dir, 'train.mappings.X.Y.npz')
        train_X, train_Y = \
            data_utils.load_slot_filling_data(mapping_param_dir)
        slot_filling_classifier = classifiers.KNearestNeighborModel(
            FLAGS.num_nn_slot_filling, train_X, train_Y)
        print('Slot filling classifier parameters loaded.')

    # Decode from standard input.
    sys.stdout.write("> ")
    sys.stdout.flush()
    sentence = sys.stdin.readline()

    vocabs = data_utils.load_vocab(FLAGS)

    while sentence:
        batch_outputs, output_logits = translate_fun(sentence, sess, model,
            vocabs, FLAGS, slot_filling_classifier=slot_filling_classifier)

        if FLAGS.token_decoding_algorithm == "greedy":
            tree, pred_cmd, outputs = batch_outputs[0]
            score = output_logits[0]
            print("{} ({})".format(pred_cmd, score))
        elif FLAGS.token_decoding_algorithm == "beam_search":
            if batch_outputs:
                top_k_predictions = batch_outputs[0]
                top_k_scores = output_logits[0]
                for j in xrange(min(FLAGS.beam_size, 10, len(batch_outputs[0]))):
                    if len(top_k_predictions) <= j:
                        break
                    top_k_pred_tree, top_k_pred_cmd, top_k_outputs = \
                        top_k_predictions[j]
                    print("Prediction {}: {} ({}) ".format(
                        j+1, top_k_pred_cmd, top_k_scores[j]))
                print()
            else:
                print(APOLOGY_MSG)
        print("> ", end="")
        sys.stdout.flush()
        sentence = sys.stdin.readline()


def translate_fun(data_point, sess, model, vocabs, FLAGS,
                  slot_filling_classifier=None):
    if type(data_point) is str:
        sc_ids, sc_full_ids, sc_copy_full_ids, sc_fillers = \
            vectorize_query(input, vocabs, FLAGS)
        tg_ids = [data_utils.ROOT_ID]
        tg_full_ids = [data_utils.ROOT_ID]
        pointer_targets = None
    else:
        sc_ids = data_point[0].sc_ids
        sc_full_ids = data_point[0].sc_full_ids
        sc_copy_full_ids = data_point[0].sc_copy_full_ids
        tg_ids = data_point[0].tg_ids
        tg_full_ids = data_point[0].tg_full_ids
        pointer_targets = data_point[0].pointer_targets
        if FLAGS.fill_argument_slots:
            _, entities = tokenizer.ner_tokenizer(data_point[0].sc_txt)
            sc_fillers = entities[0]
        else:
            sc_fillers = None
 
    # Which bucket does it belong to?
    bucket_id = min([b for b in xrange(len(model.buckets))
                    if model.buckets[b][0] > len(sc_ids)])

    # Get a 1-element batch to feed the sentence to the model.
    formatted_example = model.format_example(
        [[sc_ids], [sc_full_ids], [sc_copy_full_ids]], [[tg_ids], [tg_full_ids]],
        bucket_id=bucket_id)

    # Compute neural network decoding output
    model_outputs = model.step(
        sess, formatted_example, bucket_id, forward_only=True)
    output_logits = model_outputs.output_logits

    decoded_outputs = decode(formatted_example.encoder_full_inputs, model_outputs, 
                             FLAGS, vocabs, sc_fillers, slot_filling_classifier)

    return decoded_outputs, output_logits


def vectorize_query(sentence, vocabs, FLAGS):
    """
    Vectorize an input query.
    """
    sc_vocab = vocabs.sc_vocab
    tg_vocab = vocabs.tg_vocab

    if FLAGS.char:
        sc_ids, _ = data_utils.sentence_to_token_ids(sentence,
            sc_vocab, data_tools.char_tokenizer, tokenizer.basic_tokenizer)
        sc_full_ids, _ = data_utils.sentence_to_token_ids(sentence,
            sc_vocab, data_tools.char_tokenizer, tokenizer.basic_tokenizer,
            use_unk=False)
        sc_copy_full_ids = []
    else:
        if FLAGS.explain:
            sentence = data_tools.bash_tokenizer(
                sentence, arg_type_only=FLAGS.normalized)
            sc_tokenizer = None
            sc_full_tokenizer = None
        else:
            if FLAGS.dataset.startswith("bash"):
                sc_tokenizer = tokenizer.ner_tokenizer \
                    if FLAGS.normalized else tokenizer.basic_tokenizer
                sc_full_tokenizer = tokenizer.basic_tokenizer
            else:
                sc_tokenizer = tokenizer.space_tokenizer
                sc_full_tokenizer = tokenizer.space_tokenizer
        sc_ids, entities = data_utils.sentence_to_token_ids(
            sentence, sc_vocab, sc_tokenizer, None)
        sc_full_ids, _ = data_utils.sentence_to_token_ids(
            sentence, sc_vocab,sc_full_tokenizer, None, use_unk=False)
        sc_copy_full_ids, _ = data_utils.sentence_to_token_ids(sentence,
            tg_vocab, sc_full_tokenizer, None, use_unk=False,
            use_dummy_indices=True, parallel_vocab_size=FLAGS.tg_vocab_size)

    # Decode the output for this 1-element batch and apply output filtering.
    sc_fillers = entities[0] if FLAGS.fill_argument_slots else None

    # Note that we only perform source word filtering when translating from
    # natural language to bash
    if not (FLAGS.dataset.startswith('bash') or FLAGS.dataset == 'regex-turk'
            and not FLAGS.explain):
        sc_ids = sc_full_ids

    return sc_ids, sc_full_ids, sc_copy_full_ids, sc_fillers


def decode(encoder_inputs, model_outputs, FLAGS, vocabs, sc_fillers=None,
           slot_filling_classifier=None):
    """
    Transform the neural network output into readable strings and apply output
    filtering (if any).
    :param encoder_inputs:
    :param model_outputs:
    :param FLAGS:
    :param vocabs:
    :param sc_fillers:
    :param slot_filling_classifier:
    :return:
    """
    rev_sc_vocab = vocabs.rev_sc_vocab
    rev_tg_vocab = vocabs.rev_tg_vocab
    rev_tg_char_vocab = vocabs.rev_tg_char_vocab

    encoder_outputs = model_outputs.encoder_hidden_states
    decoder_outputs = model_outputs.decoder_hidden_states

    if FLAGS.fill_argument_slots:
        assert(sc_fillers is not None)
        assert(slot_filling_classifier is not None)
        assert(encoder_outputs is not None)
        assert(decoder_outputs is not None)

    output_symbols = model_outputs.output_symbols
    batch_size = len(output_symbols)
    batch_outputs = []
    num_output_examples = 0

    # Prepare copied indices if the model is trained with explicit copy
    # alignments.
    if FLAGS.use_copy and FLAGS.copy_fun == 'supervised':
        pointers = model_outputs.pointers
        sc_length = pointers.shape[1]
        tg_length = pointers.shape[2]
        if FLAGS.token_decoding_algorithm == 'greedy':
            batch_pointers = np.reshape(pointers,
                [batch_size, 1, sc_length, tg_length])
        else:
            batch_pointers = np.reshape(pointers,
                [batch_size, FLAGS.beam_size, sc_length, tg_length])

    for batch_id in xrange(batch_size):
        def as_str(output):
            if output < FLAGS.target_vocab_size:
                token = rev_tg_vocab[output]
            else:
                token = rev_sc_vocab[
                    encoder_inputs[batch_id][output - FLAGS.target_vocab_size]]
            return token

        top_k_predictions = output_symbols[batch_id]
        if FLAGS.token_decoding_algorithm == "beam_search":
            assert(len(top_k_predictions) == FLAGS.beam_size)
            beam_outputs = []
        else:
            # pack greedy decoding results into size-1 beam
            top_k_predictions = [top_k_predictions]

        for beam_id in xrange(len(top_k_predictions)):
            # Step 1: transform the neural network output into readable strings
            prediction = top_k_predictions[beam_id]
            outputs = [int(pred) for pred in prediction]
            
            # If there is an EOS symbol in outputs, cut them at that point.
            if data_utils.EOS_ID in outputs:
                outputs = outputs[:outputs.index(data_utils.EOS_ID)]

            if FLAGS.fill_argument_slots:
                tg_slots = {}

            tree, output_tokens = None, []
            if FLAGS.char:
                tg = "".join([as_str(output) for output in outputs])\
                    .replace(data_utils._UNK, ' ')
            else:
                for token_id in xrange(len(outputs)):
                    output = outputs[token_id]
                    if output < len(rev_tg_vocab):
                        pred_token = rev_tg_vocab[output]
                        if "@@" in pred_token:
                            pred_token = pred_token.split("@@")[-1]
                        if pred_token.startswith('__LF__'):
                            pred_token = pred_token[len('__LF__'):]
                        if FLAGS.fill_argument_slots:
                            # process argument slots
                            if pred_token in constants._ENTITIES:
                                pred_token_type = pred_token
                                tg_slots[token_id] = (pred_token, pred_token_type)
                    else:
                        if FLAGS.use_copy and FLAGS.copy_fun != 'supervised':
                            pred_token = rev_sc_vocab[
                                encoder_inputs[len(encoder_inputs) - 1
                                    - (output - FLAGS.tg_vocab_size)][batch_id]]
                            if pred_token.startswith('__LF__'):
                                pred_token = pred_token[len('__LF__'):]
                        else:
                            pred_token = data_utils._UNK
                    output_tokens.append(pred_token)

                if FLAGS.partial_token:
                    # process partial-token outputs
                    merged_output_tokens = []
                    buffer = ''
                    load_buffer = False
                    for token in output_tokens:
                        if load_buffer:
                            if token == data_utils._ARG_END:
                                merged_output_tokens.append(buffer)
                                load_buffer = False
                                buffer = ''
                            else:
                                buffer += token
                        else:
                            if token == data_utils._ARG_START:
                                load_buffer = True
                            else:
                                merged_output_tokens.append(token)
                    output_tokens = merged_output_tokens

                tg = " ".join(output_tokens)
            
            # Step 2: check if the predicted command template is grammatical
            if (FLAGS.grammatical_only or FLAGS.fill_argument_slots) \
                    and not FLAGS.explain:
                if FLAGS.dataset.startswith("bash"):
                    tg = re.sub('( ;\s+)|( ;$)', ' \\; ', tg)
                    tree = data_tools.bash_parser(tg)
                elif FLAGS.dataset.startswith("regex"):
                    # TODO: check if a predicted regular expression is legal
                    tree = ''
                else:
                    tree = data_tools.paren_parser(tg)
                # filter out non-grammatical output
                if tree is None:
                    continue

            # Step 3: check if the predicted command templates have enough
            # slots to hold the fillers (to rule out templates that are
            # trivially unqualified)
            output_example = False
            if FLAGS.explain or \
                    not FLAGS.dataset.startswith("bash") or sc_fillers is None:
                temp = tg
                output_example = True
            else:
                # Step 3: match the fillers to the argument slots
                batch_sc_fillers = sc_fillers[batch_id]
                if FLAGS.use_copy and FLAGS.copy_fun == 'supervised':
                    tree2, temp, _ = slot_filling.stable_slot_filling(
                        output_tokens, batch_sc_fillers, tg_slots,
                        batch_pointers[batch_id, beam_id, :, :],
                        None, None, None, verbose=False)
                elif FLAGS.fill_argument_slots:
                    if len(tg_slots) > len(sc_fillers):
                        tree2, temp, _ = slot_filling.stable_slot_filling(
                            output_tokens, batch_sc_fillers, tg_slots, None,
                            encoder_outputs[batch_id],
                            decoder_outputs[batch_id*FLAGS.beam_size+beam_id],
                            slot_filling_classifier, verbose=False)
                    else:
                        temp = None
                if temp is not None:
                    output_example = True
                    tree = tree2
            if output_example:
                if FLAGS.token_decoding_algorithm == "greedy":
                    batch_outputs.append((tree, temp, outputs))
                else:
                    beam_outputs.append((tree, temp, outputs))
                num_output_examples += 1

            # The threshold is used to increase decoding speed
            if num_output_examples == 20:
                break

        if FLAGS.token_decoding_algorithm == "beam_search":
            if beam_outputs:
                batch_outputs.append(beam_outputs)

    # Step 4: apply character decoding
    if FLAGS.tg_char:
        char_output_symbols = model_outputs.char_output_symbols
        sentence_length = char_output_symbols.shape[0]
        batch_char_outputs = []
        batch_char_predictions = \
            [np.transpose(np.reshape(x, [sentence_length, FLAGS.beam_size,
                                         FLAGS.max_tg_token_size + 1]),
                          (1, 0, 2))
             for x in np.split(char_output_symbols, batch_size, 1)]
        for batch_id in xrange(len(batch_char_predictions)):
            beam_char_outputs = []
            top_k_char_predictions = batch_char_predictions[batch_id]
            for k in xrange(len(top_k_char_predictions)):
                top_k_char_prediction = top_k_char_predictions[k]
                sent = []
                for i in xrange(sentence_length):
                    word = ''
                    for j in xrange(FLAGS.max_tg_token_size):
                        char_prediction = top_k_char_prediction[i, j]
                        if char_prediction == data_utils.CEOS_ID or \
                            char_prediction == data_utils.CPAD_ID:
                            break
                        elif char_prediction in rev_tg_char_vocab:
                            word += rev_tg_char_vocab[char_prediction]
                        else:
                            word += data_utils._CUNK
                    sent.append(word)
                if data_utils._CATOM in sent:
                    sent = sent[:sent[:].index(data_utils._CATOM)]
                beam_char_outputs.append(' '.join(sent))
            batch_char_outputs.append(beam_char_outputs)
        return batch_outputs, batch_char_outputs
    else:
        return batch_outputs


def decode_set(sess, model, dataset, top_k, FLAGS, verbose=True):
    """
    Compute top-k predictions on the dev/test dataset and write the predictions
    to disk.

    :param sess: A TensorFlow session.
    :param model: Prediction model object.
    :param top_k: Number of top predictions to compute.
    :param FLAGS: Training/testing hyperparameter settings.
    :param verbose: If set, also print decoding results to screen.
    """
    nl2bash = FLAGS.dataset.startswith('bash') and not FLAGS.explain

    grouped_dataset = data_utils.group_data(
        dataset, use_bucket=True, use_temp=FLAGS.normalized)
    vocabs = data_utils.load_vocab(FLAGS)
    rev_sc_vocab = vocabs.rev_sc_vocab

    if FLAGS.fill_argument_slots:
        # create slot filling classifier
        mapping_param_dir = os.path.join(
            FLAGS.model_dir, 'train.mappings.X.Y.npz')
        train_X, train_Y = data_utils.load_slot_filling_data(mapping_param_dir)
        slot_filling_classifier = classifiers.KNearestNeighborModel(
            FLAGS.num_nn_slot_filling, train_X, train_Y)
        print('Slot filling classifier parameters loaded.')
    else:
        slot_filling_classifier = None

    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
    pred_file_path = os.path.join(model.model_dir, 'predictions.{}.{}'.format(
        model.decode_sig, ts))
    pred_file = open(pred_file_path, 'w')
    for example_id in xrange(len(grouped_dataset)):
        key, data_group = grouped_dataset[example_id]

        sc_txt = data_group[0].sc_txt
        sc_temp = ' '.join([rev_sc_vocab[i] for i in data_group[0].sc_ids])
        if verbose:
            print("Example {}:".format(example_id))
            print("(Orig) Source: {}".format(sc_txt))
            print("Source: {}".format(sc_temp))
            for j in xrange(len(data_group)):
                print("GT Target {}: {}".format(j+1, data_group[j].tg_txt))

        batch_outputs, output_logits = translate_fun(data_group, sess, model,
            vocabs, FLAGS, slot_filling_classifier=slot_filling_classifier)
        if FLAGS.tg_char:
            batch_outputs, batch_char_outputs = batch_outputs

        if batch_outputs:
            if FLAGS.token_decoding_algorithm == "greedy":
                tree, pred_cmd, outputs = batch_outputs[0]
                if nl2bash:
                    pred_cmd = data_tools.ast2command(
                        tree, loose_constraints=True)
                score = output_logits[0]
                pred_file.write('{}\n'.format(pred_cmd))
                if verbose:
                    print("Prediction: {} ({})".format(pred_cmd, score))
            elif FLAGS.token_decoding_algorithm == "beam_search":
                top_k_predictions = batch_outputs[0]
                if FLAGS.tg_char:
                    top_k_char_predictions = batch_char_outputs[0]
                top_k_scores = output_logits[0]
                num_preds = min(FLAGS.beam_size, top_k, len(top_k_predictions))
                for j in xrange(num_preds):
                    top_k_pred_tree, top_k_pred_cmd, top_k_outputs = \
                        top_k_predictions[j]
                    if nl2bash:
                        pred_cmd = data_tools.ast2command(
                            top_k_pred_tree, loose_constraints=True)
                    else:
                        pred_cmd = top_k_pred_cmd
                    pred_file.write('{}|||'.format(pred_cmd))
                    if verbose:
                        print("Prediction {}: {} ({})".format(
                            j+1, pred_cmd, top_k_scores[j]))
                        if FLAGS.tg_char:
                            print("Character-based prediction {}: {}".format(
                                j+1, top_k_char_predictions[j]))
                pred_file.write('\n')
        else:
            print(APOLOGY_MSG)
    pred_file.close()
    shutil.copyfile(pred_file_path, os.path.join(FLAGS.model_dir,
        'predictions.{}.latest'.format(model.decode_sig)))


def visualize_attn_alignments(M, source, target, rev_sc_vocab,
                              rev_tg_vocab, output_path):
    target_length, source_length = M.shape

    nl = [rev_sc_vocab[x] for x in source]
    cm = []
    for i, x in enumerate(target):
        cm.append(rev_tg_vocab[x])
        if rev_tg_vocab[x] == data_utils._EOS:
            break

    plt.clf()
    if len(target) == 0:
        i = 0
    plt.imshow(M[:i+1, :], interpolation='nearest', cmap=plt.cm.Blues)

    pad_size = source_length - len(nl)
    plt.xticks(xrange(source_length),
               [x.replace("$$", "") for x in reversed(
                   nl + [data_utils._PAD] * pad_size)],
               rotation='vertical')
    plt.yticks(xrange(len(cm)), [x.replace("$$", "") for x in cm],
               rotation='horizontal')

    plt.colorbar()

    plt.savefig(output_path, bbox_inches='tight')
