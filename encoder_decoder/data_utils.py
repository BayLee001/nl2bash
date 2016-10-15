# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Utilities for tokenizing & generating vocabularies."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bashlex"))

import bash, data_tools, nast, normalizer

import tensorflow as tf

# Special vocabulary symbols - we always put them at the start.
_PAD = b"_PAD"
_EOS = b"_EOS"
_UNK = b"_UNK"
_ARG_UNK = b"ARGUMENT_UNK"
_UTL_UNK = b"HEADCOMMAND_UNK"
_FLAG_UNK = b"FLAG_UNK"

_SPACE = b"<SPACE>"

_H_NO_EXPAND = b"<H_NO_EXPAND>"
_V_NO_EXPAND = b"<V_NO_EXPAND>"

_GO = b"_GO"                    # seq2seq start symbol
_ROOT = b"ROOT_"                # seq2tree start symbol

_NUM = b"_NUM"

_START_VOCAB = [_PAD, _EOS, _UNK, _ARG_UNK, _UTL_UNK, _FLAG_UNK,
                _H_NO_EXPAND, _V_NO_EXPAND, _GO, _ROOT]

PAD_ID = 0
EOS_ID = 1
UNK_ID = 2
ARG_ID = 3
UTL_ID = 4
FLAG_ID = 5
H_NO_EXPAND_ID = 6
V_NO_EXPAND_ID = 7
GO_ID = 8
ROOT_ID = 9

# Regular expressions used to tokenize.
_DIGIT_RE = re.compile(br"\d")

def is_option(word):
    return word.startswith('-') or word.startswith("FLAG_")


def is_simple(ast):
    # Check if tree contains only high-frequency commands
    if ast.kind == "headcommand" and not ast.value in bash.head_commands:
        return False
    for child in ast.children:
        if not is_simple(child):
            return False
    return True


def clean_dir(dir):
    for f_name in os.listdir(dir):
        f_path = os.path.join(dir, f_name)
        try:
            if os.path.isfile(f_path):
                os.unlink(f_path)
        except Exception as e:
            print(e)


def create_vocabulary(vocabulary_path, data, max_vocabulary_size,
                      tokenizer=None, base_tokenizer=None,
                      normalize_digits=True, normalize_long_pattern=True,
                      min_word_frequency=2):
    """Create vocabulary file (if it does not exist yet) from data file.

    Data file is assumed to contain one sentence per line. Each sentence is
    tokenized and digits are normalized (if normalize_digits is set).
    Vocabulary contains the most-frequent tokens up to max_vocabulary_size.
    We write it to vocabulary_path in a one-token-per-line format, so that later
    token in the first line gets id=0, second line gets id=1, and so on.

    Args:
      vocabulary_path: path where the vocabulary will be created.
      data: list of lines each of which corresponds to a data point.
      max_vocabulary_size: limit on the size of the created vocabulary.
      tokenizer: a function to use to tokenize each data sentence;
        if None, basic_tokenizer will be used.
      base_tokenizer: base_tokenizer used for separating a string into chars.
      normalize_digits: Boolean; if true, all digits are replaced by 0s.
      min_word_frequency: word frequency threshold below which a word is
        goint to be marked as _UNK.
    """
    if not tf.gfile.Exists(vocabulary_path):
        print("Creating vocabulary %s from data (%d)" % (vocabulary_path,
                                                         len(data)))
        vocab = {}
        counter = 0
        for line in data:
            counter += 1
            if counter % 1000 == 0:
                print("  processing line %d" % counter)
            if type(line) is list:
                tokens = line
            else:
                if base_tokenizer:
                    tokens = tokenizer(line, base_tokenizer, normalize_digits=normalize_digits,
                                       normalize_long_pattern=normalize_long_pattern)
                else:
                    tokens = tokenizer(line, normalize_digits=normalize_digits,
                                       normalize_long_pattern=normalize_long_pattern)
            if not tokens:
                continue
            for word in tokens:
                if word in vocab:
                    vocab[word] += 1
                else:
                    vocab[word] = 1

        # Keep all training vocabulary in the commands
        if ".cm" in vocabulary_path:
            min_word_frequency = 0

        sorted_vocab = {}
        for v in vocab:
            if vocab[v] >= min_word_frequency:
                sorted_vocab[v] = vocab[v]
            else:
                print("Infrequent token: %s"  % v)
        sorted_vocab = sorted(sorted_vocab, key=vocab.get, reverse=True)
        vocab_list = list(_START_VOCAB)
        for v in sorted_vocab:
            if not v in _START_VOCAB:
                vocab_list.append(v)

        if len(vocab_list) > max_vocabulary_size:
            vocab_list = vocab_list[:max_vocabulary_size]
        with tf.gfile.GFile(vocabulary_path, mode="wb") as vocab_file:
            for w in vocab_list:
                try:
                    vocab_file.write(w + b"\n")
                except Exception:
                    vocab_file.write(w.encode('utf-8') + b"\n")
    else:
        print("Reading vocabulary %s from path" % vocabulary_path)


def initialize_vocabulary(vocabulary_path):
    """Initialize vocabulary from file.

    We assume the vocabulary is stored one-item-per-line, so a file:
      dog
      cat
    will result in a vocabulary {"dog": 0, "cat": 1}, and this function will
    also return the reversed-vocabulary ["dog", "cat"].

    Args:
      vocabulary_path: path to the file containing the vocabulary.

    Returns:
      a pair: the vocabulary (a dictionary mapping string to integers), and
      the reversed vocabulary (a list, which reverses the vocabulary mapping).

    Raises:
      ValueError: if the provided vocabulary_path does not exist.
    """
    if tf.gfile.Exists(vocabulary_path):
        rev_vocab = []
        with tf.gfile.GFile(vocabulary_path, mode="rb") as f:
            rev_vocab.extend(f.readlines())
        rev_vocab = [line.strip() for line in rev_vocab]
        vocab = dict([(x, y) for (y, x) in enumerate(rev_vocab)])
        return vocab, rev_vocab
    else:
        raise ValueError("Vocabulary file %s not found.", vocabulary_path)


def token_ids_to_sentences(inputs, rev_vocab, head_appended=False, char_model=False):
    batch_size = len(inputs[0])
    sentences = []
    for i in xrange(batch_size):
        if head_appended:
            outputs = [decoder_input[i] for decoder_input in inputs[1:]]
        else:
            outputs = [decoder_input[i] for decoder_input in inputs]
        # If there is an EOS symbol in outputs, cut them at that point.
        if EOS_ID in outputs:
            outputs = outputs[:outputs.index(EOS_ID)]
        # If there is a PAD symbol in outputs, cut them at that point.
        if PAD_ID in outputs:
            outputs = outputs[:outputs.index(PAD_ID)]
        # Print out command corresponding to outputs.
        if char_model:
            sentences.append("".join([tf.compat.as_str(rev_vocab[output])
                             for output in outputs]).replace(_UNK, ' '))
        else:
            sentences.append(" ".join([tf.compat.as_str(rev_vocab[output])
                                   for output in outputs]))
    return sentences


def sentence_to_token_ids(sentence, vocabulary,
                          tokenizer, base_tokenizer,
                          normalize_digits=True,
                          normalize_long_pattern=True,
                          with_arg_type=False):
    """Convert a string to list of integers representing token-ids.

    For example, a sentence "I have a dog" may become tokenized into
    ["I", "have", "a", "dog"] and with vocabulary {"I": 1, "have": 2,
    "a": 4, "dog": 7"} this function will return [1, 2, 4, 7].

    Args:
      sentence: the sentence in bytes format to convert to token-ids.
      vocabulary: a dictionary mapping tokens to integers.
      tokenizer: a function to use to tokenize each sentence;
        if None, basic_tokenizer will be used.
      normalize_digits: Boolean; if true, all digits are replaced by 0s.

    Returns:
      a list of integers, the token-ids for the sentence.
    """
    if type(sentence) is list:
        words = sentence
        with_arg_type = True
    else:
        if base_tokenizer:
            words = tokenizer(sentence, base_tokenizer, normalize_digits=normalize_digits,
                              normalize_long_pattern=normalize_long_pattern)
        else:
            words = tokenizer(sentence, normalize_digits=normalize_digits,
                              normalize_long_pattern=normalize_long_pattern)

    token_ids = []
    for w in words:
        if w in vocabulary:
            token_ids.append(vocabulary[w])
        else:
            if with_arg_type:
                kind = w.split('_')[0].lower()
                if kind == "flag":
                    token_ids.append(FLAG_ID)
                elif kind == "headcommand":
                    token_ids.append(UTL_ID)
                else:
                    token_ids.append(ARG_ID)
            else:
                token_ids.append(UNK_ID)
            if w.startswith("FLAG_"):
                print(w, sentence)

    return token_ids


def data_to_token_ids(data, target_path, vocabulary_path,
                      tokenizer=None, base_tokenizer=None,
                      normalize_digits=True, normalize_long_pattern=True,
                      with_arg_types=False):
    """Tokenize data file and turn into token-ids using given vocabulary file.

    This function loads data line-by-line from data_path, calls the above
    sentence_to_token_ids, and saves the result to target_path. See comment
    for sentence_to_token_ids on the details of token-ids format.

    Args:
      data: list of lines each of which corresponds to a data point.
      target_path: path where the file with token-ids will be created.
      vocabulary_path: path to the vocabulary file.
      tokenizer: a function to use to tokenize each sentence;
        if None, basic_tokenizer will be used.
      base_tokenizer: base tokenizer used for splitting strings into characters.
      normalize_digits: Boolean; if true, all digits are replaced by 0s.
    """
    max_token_num = 0
    if not tf.gfile.Exists(target_path):
        print("Tokenizing data (%d)" % len(data))
        vocab, _ = initialize_vocabulary(vocabulary_path)
        tokens_file = tf.gfile.GFile(target_path, mode="w")
        counter = 0
        for line in data:
            counter += 1
            if counter % 1000 == 0:
                print("  tokenizing line %d" % counter)
            token_ids = sentence_to_token_ids(line, vocab, tokenizer, base_tokenizer,
                                              normalize_digits, normalize_long_pattern,
                                              with_arg_types)
            if len(token_ids) > max_token_num:
                max_token_num = len(token_ids)
            tokens_file.write(" ".join([str(tok) for tok in token_ids])
                              + "\n")
        tokens_file.close()
    return max_token_num


def bucket_grouped_data(grouped_dataset, buckets):
    batch_nl_strs = [[] for _ in buckets]
    batch_cm_strs = [[] for _ in buckets]
    batch_nls = [[] for _ in buckets]
    batch_cmds = [[] for _ in buckets]

    for nl_temp in grouped_dataset:
        nl_strs, cm_strs, nls, cmds = grouped_dataset[nl_temp]

        # Which bucket does it belong to?
        bucket_id = min([b for b in xrange(len(buckets))
                        if buckets[b][0] > len(nls[0])])

        batch_nl_strs[bucket_id].append(nl_strs[0])
        batch_cm_strs[bucket_id].append(cm_strs)
        batch_nls[bucket_id].append(nls[0])
        batch_cmds[bucket_id].append([ROOT_ID])

    return batch_nl_strs, batch_cm_strs, batch_nls, batch_cmds


def group_data_by_nl(dataset, use_bucket=False):
    if use_bucket:
        dataset = reduce(lambda x,y: x + y, dataset)
    grouped_dataset = {}
    for i in xrange(len(dataset)):
        nl_str, cm_str, nl, search_history = dataset[i]
        nl_template = " ".join(data_tools.basic_tokenizer(nl_str.decode("utf-8")))
        if nl_template in grouped_dataset:
            grouped_dataset[nl_template][0].append(nl_str)
            grouped_dataset[nl_template][1].append(cm_str)
            grouped_dataset[nl_template][2].append(nl)
            grouped_dataset[nl_template][3].append(search_history)
        else:
            grouped_dataset[nl_template] = [[nl_str], [cm_str], [nl], [search_history]]

    return grouped_dataset


def group_data_by_cm(dataset, use_bucket=False):
    if use_bucket:
        dataset = reduce(lambda x,y: x + y, dataset)
    grouped_dataset = {}
    for i in xrange(len(dataset)):
        nl_str, cm_str, nl, search_history = dataset[i]
        cm_template = data_tools.cmd2template(cm_str)
        if cm_template in grouped_dataset:
            grouped_dataset[cm_template][0].append(nl_str)
            grouped_dataset[cm_template][1].append(cm_str)
            grouped_dataset[cm_template][2].append(nl)
            grouped_dataset[cm_template][3].append(search_history)
        else:
            grouped_dataset[cm_template] = [[nl_str], [cm_str], [nl], [search_history]]

    return grouped_dataset


def load_vocab(FLAGS):
    if FLAGS.decoder_topology in ['rnn']:
        nl_vocab_path = os.path.join(FLAGS.data_dir,
                                         "vocab%d.nl" % FLAGS.nl_vocab_size)
        if FLAGS.canonical:
            cm_vocab_path = os.path.join(FLAGS.data_dir,
                                        "vocab%d.cm.norm" % FLAGS.cm_vocab_size)
        elif FLAGS.normalized:
            cm_vocab_path = os.path.join(FLAGS.data_dir,
                                        "vocab%d.cm.norm" % FLAGS.cm_vocab_size)
        else:
            cm_vocab_path = os.path.join(FLAGS.data_dir,
                                        "vocab%d.cm" % FLAGS.cm_vocab_size)
    elif FLAGS.decoder_topology in ['basic_tree']:
        nl_vocab_path = os.path.join(FLAGS.data_dir,
                                         "vocab%d.nl" % FLAGS.nl_vocab_size)
        if FLAGS.canonical:
            cm_vocab_path = os.path.join(FLAGS.data_dir,
                                        "vocab%d.cm.ast.norm" % FLAGS.cm_vocab_size)
        elif FLAGS.normalized:
            cm_vocab_path = os.path.join(FLAGS.data_dir,
                                        "vocab%d.cm.ast.norm" % FLAGS.cm_vocab_size)
        else:
            cm_vocab_path = os.path.join(FLAGS.data_dir,
                                        "vocab%d.cm.ast" % FLAGS.cm_vocab_size)
    else:
        raise ValueError("Unrecognized decoder topology: {}."
                         .format(FLAGS.decoder_topology))
    nl_vocab, rev_nl_vocab = initialize_vocabulary(nl_vocab_path)
    cm_vocab, rev_cm_vocab = initialize_vocabulary(cm_vocab_path)
    return nl_vocab, rev_nl_vocab, cm_vocab, rev_cm_vocab


def load_data(FLAGS, buckets):
    print("Loading data from %s" % FLAGS.data_dir)

    data_dir = FLAGS.data_dir

    if FLAGS.char:
        nl_extention = ".cids%d.nl" % FLAGS.nl_vocab_size
        cm_extension = ".cids%d.cm" % FLAGS.cm_vocab_size
        append_head_token = True
        append_end_token = True
    elif FLAGS.decoder_topology in ["rnn"]:
        nl_extention = ".ids%d.nl" % FLAGS.nl_vocab_size
        if FLAGS.canonical:
            cm_extension = ".ids%d.cm.norm.order" % FLAGS.cm_vocab_size
        elif FLAGS.normalized:
            cm_extension = ".ids%d.cm.norm" % FLAGS.cm_vocab_size
        else:
            cm_extension = ".ids%d.cm" % FLAGS.cm_vocab_size
        append_head_token = True
        append_end_token = True
    elif FLAGS.decoder_topology in ["basic_tree"]:
        nl_extention = ".ids%d.nl" % FLAGS.nl_vocab_size
        if FLAGS.canonical:
            cm_extension = ".seq%d.cm.norm.order" % FLAGS.cm_vocab_size
        elif FLAGS.normalized:
            cm_extension = ".seq%d.cm.norm" % FLAGS.cm_vocab_size
        else:
            cm_extension = ".seq%d.cm" % FLAGS.cm_vocab_size
        append_head_token = False
        append_end_token = False

    train_path = os.path.join(data_dir, "train")
    dev_path = os.path.join(data_dir, "dev")
    test_path = os.path.join(data_dir, "test")

    nl_txt_train = train_path + ".nl"
    cm_txt_train = train_path + ".cm"
    nl_txt_dev = dev_path + ".nl"
    cm_txt_dev = dev_path + ".cm"
    nl_txt_test = test_path + ".nl"
    cm_txt_test = test_path + ".cm"

    nl_train = train_path + nl_extention
    cm_train = train_path + cm_extension
    nl_dev = dev_path + nl_extention
    cm_dev = dev_path + cm_extension
    nl_test = test_path + nl_extention
    cm_test = test_path + cm_extension

    train_set = read_data(nl_txt_train, cm_txt_train, nl_train, cm_train,
                          buckets, FLAGS.max_train_data_size,
                          append_head_token=append_head_token,
                          append_end_token=append_end_token)
    dev_set = read_data(nl_txt_dev, cm_txt_dev, nl_dev, cm_dev, buckets,
                        append_head_token=append_head_token,
                        append_end_token=append_end_token)
    test_set = read_data(nl_txt_test, cm_txt_test, nl_test, cm_test, buckets,
                         append_head_token=append_head_token,
                         append_end_token=append_end_token)

    return train_set, dev_set, test_set


def read_data(source_txt_path, target_txt_path, source_path, target_path,
              buckets=None, max_num_examples=None,
              append_head_token=False, append_end_token=False):
    """Read data from source and target files and put into buckets.
    :param source_txt_path: path to the file containing the original source
    strings.
    :param target_txt_path: path to the file containing the original target
    strings.
    :param source_path: path to the file with token-ids for the source language.
    :param target_path: path to the file with token-ids for the target language.
    :param buckets: bucket sizes for training.
    :param max_num_examples: maximum number of lines to read. Read complete data files if
        this entry is 0 or None.
    """
    if buckets:
        data_set = [[] for _ in buckets]
    else:
        data_set = []

    with tf.gfile.GFile(source_txt_path, mode="r") as source_txt_file:
        with tf.gfile.GFile(target_txt_path, mode="r") as target_txt_file:
            with tf.gfile.GFile(source_path, mode="r") as source_file:
                with tf.gfile.GFile(target_path, mode="r") as target_file:
                    source_txt, target_txt = source_txt_file.readline(), target_txt_file.readline()
                    source, target = source_file.readline(), target_file.readline()
                    counter = 0
                    while source:
                        assert(target)
                        if max_num_examples and counter < max_num_examples:
                            break
                        counter += 1
                        if counter % 1000 == 0:
                            print("  reading data line %d" % counter)
                            sys.stdout.flush()
                        source_ids = [int(x) for x in source.split()]
                        target_ids = [int(x) for x in target.split()]
                        if append_head_token:
                            target_ids.insert(0, ROOT_ID)
                        if append_end_token:
                            target_ids.append(EOS_ID)
                        if buckets:
                            for bucket_id, (source_size, target_size) in enumerate(buckets):
                                if len(source_ids) < source_size and len(target_ids) < target_size:
                                    data_set[bucket_id].append(
                                        [source_txt, target_txt, source_ids, target_ids])
                                    break   
                        else:
                            data_set.append([source_txt, target_txt, source_ids, target_ids])

                        source_txt, target_txt = \
                            source_txt_file.readline(), target_txt_file.readline()
                        source, target = source_file.readline(), target_file.readline()
    print("  %d data points read." % len(data_set))
    return data_set


def parse_brackets(line):
    """A very simple algorithm for parsing data with parentheses."""
    if not line.startswith("("):
        line = "( " + line
    if not line.endswith(")"):
        line = line + " )"
    words = line.strip().split()

    root = nast.Node(kind="root", value="root")
    stack = []

    i = 0
    while i < len(words):
        word = words[i]
        if word == "(":
            if stack:
                # creates non-terminal
                node = nast.Node(kind="nt", value="<n>")
                stack[-1].add_child(node)
                node.parent = stack[-1]
                stack.append(node)
            else:
                stack.append(root)
        elif word == ")":
            if stack:
                stack.pop()
        else:
            node = nast.Node(kind="t", value=word)
            stack[-1].add_child(node)
            node.parent = stack[-1]
        i += 1
        if len(stack) == 0:
            break;

    return root

class Dataset(object):
    def __init__(self):
        self.train = []
        self.dev = []
        self.test = []


def read_raw_data(data_dir):
    nl_list = Dataset()
    cm_list = Dataset()
    train_path = os.path.join(data_dir, "train")
    dev_path = os.path.join(data_dir, "dev")
    test_path = os.path.join(data_dir, "test")
    with open(train_path + ".nl") as f:
        nl_list.train = [line.strip() for line in f.readlines()]
    with open(train_path + ".cm") as f:
        cm_list.train = [line.strip() for line in f.readlines()]
    with open(dev_path + ".nl") as f:
        nl_list.dev = [line.strip() for line in f.readlines()]
    with open(dev_path + ".cm") as f:
        cm_list.dev = [line.strip() for line in f.readlines()]
    if os.path.exists(test_path + ".nl"):
        with open(test_path + ".nl") as f:
            nl_list.test = [line.strip() for line in f.readlines()]
    if os.path.exists(test_path + ".cm"):
        with open(test_path + ".cm") as f:
            cm_list.test = [line.strip() for line in f.readlines()]
    if not nl_list.test:
        nl_list.test = nl_list.dev
        cm_list.test = cm_list.dev
    return nl_list, cm_list


def prepare_dataset(data, data_dir, suffix, vocab_size, vocab_path,
                    normalize_digits=True, normalize_long_pattern=True):
    max_len = 0
    for d in data.train:
        if len(d) > max_len:
            max_len = len(d)

    if type(data.train[0]) is not basestring:
        create_vocabulary(vocab_path, data.train, vocab_size,
                      normalize_digits=normalize_digits,
                      normalize_long_pattern=normalize_long_pattern)

    train_path = os.path.join(data_dir, "train")
    dev_path = os.path.join(data_dir, "dev")
    test_path = os.path.join(data_dir, "test")

    if type(data.train[0]) is basestring:
        with open(train_path + suffix, 'w') as o_f:
            for line in data.train:
                o_f.write(line.strip() + '\n')
        with open(dev_path + suffix, 'w') as o_f:
            for line in data.dev:
                o_f.write(line.strip() + '\n')
        with open(test_path + suffix, 'w') as o_f:
            for line in data.test:
                o_f.write(line.strip() + '\n')
    else:
        data_to_token_ids(data.train, train_path + suffix, vocab_path,
                          normalize_digits=normalize_digits,
                          normalize_long_pattern=normalize_long_pattern)
        data_to_token_ids(data.dev, dev_path + suffix, vocab_path,
                          normalize_digits=normalize_digits,
                          normalize_long_pattern=normalize_long_pattern)
        data_to_token_ids(data.test, test_path + suffix, vocab_path,
                          normalize_digits=normalize_digits,
                          normalize_long_pattern=normalize_long_pattern)

    return max_len


def prepare_jobs(data_dir, nl_vocab_size, cm_vocab_size):
    def add_to_set(nl_list, cm_list, split):
        for nl, cm in zip(getattr(nl_list, split), getattr(cm_list, split)):
            nl_tokens = nl.split()
            cm_tokens = cm.split()
            getattr(nl_list, split).append(nl)
            getattr(cm_list, split).append(cm)
            getattr(nl_token_list, split).append(nl_tokens)
            getattr(cm_token_list, split).append(cm_tokens)

    # unfiltered data
    nl_data, cm_data = read_raw_data(data_dir)

    nl_list = Dataset()
    cm_list = Dataset()
    nl_token_list = Dataset()
    cm_token_list = Dataset()

    add_to_set(nl_data, cm_data, "train")
    add_to_set(nl_data, cm_data, "dev")
    add_to_set(nl_data, cm_data, "test")

    nl_vocab_path = os.path.join(data_dir, "vocab%d.nl" % nl_vocab_size)
    cm_vocab_path = os.path.join(data_dir, "vocab%d.cm" % cm_vocab_size)

    nl_token_suffix = ".ids%d.nl" % nl_vocab_size
    cm_token_suffix = ".ids%d.cm" % cm_vocab_size

    max_nl_token_len = prepare_dataset(nl_token_list, data_dir, nl_token_suffix, nl_vocab_size,
                                       nl_vocab_path, normalize_digits=False,
                                       normalize_long_pattern=False)
    max_cm_token_len = prepare_dataset(cm_token_list, data_dir, cm_token_suffix, cm_vocab_size,
                                       cm_vocab_path, normalize_digits=False,
                                       normalize_long_pattern=False)

    print("maximum num tokens in description = %d" % max_nl_token_len)
    print("maximum num tokens in command = %d" % max_cm_token_len)


def prepare_bash(data_dir, nl_vocab_size, cm_vocab_size):

    def add_to_set(nl_list, cm_list, split):
        with_parent = False
        for nl, cm in zip(getattr(nl_list, split), getattr(cm_list, split)):
            ast = data_tools.bash_parser(cm)
            if ast:
                if is_simple(ast):
                    nl_chars = data_tools.char_tokenizer(nl, data_tools.basic_tokenizer,
                                                         normalize_digits=False,
                                                         normalize_long_pattern=False)
                    cm_chars = data_tools.char_tokenizer(cm, data_tools.bash_tokenizer,
                                                         normalize_digits=False,
                                                         normalize_long_pattern=False)
                    nl_tokens = data_tools.basic_tokenizer(nl)
                    cm_tokens = data_tools.ast2tokens(ast, with_parent=with_parent)
                    cm_seq = data_tools.ast2list(ast, list=[], with_parent=with_parent)
                    pruned_ast = normalizer.prune_ast(ast)
                    cm_pruned_tokens = data_tools.ast2tokens(
                        pruned_ast, loose_constraints=True, with_parent=with_parent)
                    cm_pruned_seq = data_tools.ast2list(
                        pruned_ast, list=[], with_parent=with_parent)
                    cm_normalized_tokens = data_tools.ast2tokens(
                        ast, loose_constraints=True, arg_type_only=True, with_parent=with_parent)
                    cm_normalized_seq = data_tools.ast2list(
                        ast, arg_type_only=True, list=[], with_parent=with_parent)
                    cm_canonical_tokens = data_tools.ast2tokens(
                        ast, loose_constraints=True, arg_type_only=True, ignore_flag_order=True,
                        with_parent=with_parent)
                    cm_canonical_seq = data_tools.ast2list(
                        ast, arg_type_only=True, ignore_flag_order=True, list=[],
                        with_parent=with_parent)
                    getattr(nl_list, split).append(nl)
                    getattr(cm_list, split).append(cm)
                    getattr(nl_char_list, split).append(nl_chars)
                    getattr(nl_token_list, split).append(nl_tokens)
                    getattr(cm_char_list, split).append(cm_chars)
                    getattr(cm_token_list, split).append(cm_tokens)
                    getattr(cm_seq_list, split).append(cm_seq)
                    getattr(cm_pruned_token_list, split).append(cm_pruned_tokens)
                    getattr(cm_pruned_seq_list, split).append(cm_pruned_seq)
                    getattr(cm_normalized_token_list, split).append(cm_normalized_tokens)
                    getattr(cm_normalized_seq_list, split).append(cm_normalized_seq)
                    getattr(cm_canonical_token_list, split).append(cm_canonical_tokens)
                    getattr(cm_canonical_seq_list, split).append(cm_canonical_seq)
                else:
                    print("Rare command: " + cm.encode('utf-8'))

    # unfiltered data
    nl_data, cm_data = read_raw_data(data_dir)

    nl_list = Dataset()
    cm_list = Dataset()
    nl_char_list = Dataset()
    nl_token_list = Dataset()
    cm_char_list = Dataset()
    cm_token_list = Dataset()
    cm_seq_list = Dataset()
    cm_pruned_token_list = Dataset()
    cm_pruned_seq_list = Dataset()
    cm_normalized_token_list = Dataset()
    cm_normalized_seq_list = Dataset()
    cm_canonical_token_list = Dataset()
    cm_canonical_seq_list = Dataset()

    add_to_set(nl_data, cm_data, "train")
    add_to_set(nl_data, cm_data, "dev")
    add_to_set(nl_data, cm_data, "test")

    # Create vocabularies of the appropriate sizes.
    nl_char_vocab_path = os.path.join(data_dir, "vocab%d.nl.char" % nl_vocab_size)
    cm_char_vocab_path = os.path.join(data_dir, "vocab%d.cm.char" % cm_vocab_size)
    nl_vocab_path = os.path.join(data_dir, "vocab%d.nl" % nl_vocab_size)
    cm_vocab_path = os.path.join(data_dir, "vocab%d.cm" % cm_vocab_size)
    cm_norm_vocab_path = os.path.join(data_dir, "vocab%d.cm.norm" % cm_vocab_size)
    cm_ast_vocab_path = os.path.join(data_dir, "vocab%d.cm.ast" % cm_vocab_size)
    cm_ast_norm_vocab_path = os.path.join(data_dir, "vocab%d.cm.ast.norm" %
                                          cm_vocab_size)

    nl_suffix = ".%d.nl" % nl_vocab_size
    cm_suffix = ".%d.cm" % cm_vocab_size
    nl_char_suffix = ".cids%d.nl" % nl_vocab_size
    cm_char_suffix = ".cids%d.cm" % cm_vocab_size
    nl_token_suffix = ".ids%d.nl" % nl_vocab_size
    cm_token_suffix = ".ids%d.cm" % cm_vocab_size
    cm_token_norm_suffix = ".ids%d.cm.norm" % cm_vocab_size
    cm_token_norm_order_suffix = ".ids%d.cm.norm.order" % cm_vocab_size
    cm_token_pruned_suffix = ".ids%d.cm.pruned" % cm_vocab_size
    cm_seq_suffix = ".seq%d.cm" % cm_vocab_size
    cm_seq_norm_suffix = ".seq%d.cm.norm" % cm_vocab_size
    cm_seq_norm_order_suffix = ".seq%d.cm.norm.order" % cm_vocab_size
    cm_seq_pruned_suffix = ".seq%d.cm.pruned" % cm_vocab_size

    _ = prepare_dataset(nl_list, data_dir, nl_suffix, nl_vocab_size, None)
    _ = prepare_dataset(cm_list, data_dir, cm_suffix, cm_vocab_size, None)
    max_nl_char_len = prepare_dataset(nl_char_list, data_dir, nl_char_suffix, nl_vocab_size,
                                      nl_char_vocab_path)
    max_cm_char_len = prepare_dataset(cm_char_list, data_dir, cm_char_suffix, cm_vocab_size,
                                      cm_char_vocab_path)
    max_nl_token_len = prepare_dataset(nl_token_list, data_dir, nl_token_suffix, nl_vocab_size,
                                       nl_vocab_path)
    max_cm_token_len = prepare_dataset(cm_token_list, data_dir, cm_token_suffix, cm_vocab_size,
                                       cm_vocab_path)
    max_cm_token_norm_len = prepare_dataset(cm_normalized_token_list, data_dir, cm_token_norm_suffix,
                                            cm_vocab_size, cm_norm_vocab_path)
    max_cm_token_norm_order_len = prepare_dataset(cm_canonical_token_list, data_dir,
                                                  cm_token_norm_order_suffix, cm_vocab_size, cm_norm_vocab_path)
    max_cm_token_pruned_len = prepare_dataset(cm_pruned_token_list, data_dir, cm_token_pruned_suffix,
                                              cm_vocab_size, cm_vocab_path)
    max_cm_seq_len = prepare_dataset(cm_seq_list, data_dir, cm_seq_suffix, cm_vocab_size,
                                     cm_ast_vocab_path)
    max_cm_seq_norm_len = prepare_dataset(cm_normalized_seq_list, data_dir, cm_seq_norm_suffix,
                                          cm_vocab_size, cm_ast_norm_vocab_path)
    max_cm_seq_norm_order_len = prepare_dataset(cm_canonical_seq_list, data_dir, cm_seq_norm_order_suffix,
                                                cm_vocab_size, cm_ast_norm_vocab_path)
    max_cm_seq_pruned_len = prepare_dataset(cm_pruned_seq_list, data_dir, cm_seq_pruned_suffix,
                                            cm_vocab_size, cm_ast_vocab_path)


    print("maximum num chars in description = %d" % max_nl_char_len)
    print("maximum num tokens in description = %d" % max_nl_token_len)
    print("maximum num chars in command = %d" % max_cm_char_len)
    print("maximum num tokens in command = %d" % max_cm_token_len)
    print("maximum num AST search steps = %d" % max_cm_seq_len)
    print("maximum num tokens in normalized command = %d" %
          max_cm_token_norm_len)
    print("maximum num normalized AST search steps = %d" %
          max_cm_seq_norm_len)
    print("maximum num tokens in canonical command = %d" %
          max_cm_token_norm_order_len)
    print("maximum num canonical AST search steps = %d" %
          max_cm_seq_norm_order_len)
    print("maximum num tokens in pruned command = %d" % max_cm_token_pruned_len)
    print("maximum num pruned AST search steps = %d" % max_cm_seq_pruned_len)


def prepare_data(FLAGS):
    """Get data into data_dir, create vocabularies and tokenize data.

    Args:
      data: { 'train': [cm_list, nl_list],
              'dev': [cm_list, nl_list],
              'test': [cm_list, nl_list] }.
      data_dir: directory in which the data sets will be stored.
      nl_vocabulary_size: size of the English vocabulary to create and use.
      cm_vocabulary_size: size of the Command vocabulary to create and use.

    Returns:
      A tuple of 8 elements:
        (1) path to the token-ids for English training data-set,
        (2) path to the token-ids for Command training data-set,
        (3) path to the token-ids for English development data-set,
        (4) path to the token-ids for Command development data-set,
        (5) path to the token-ids for English test data-set,
        (6) path to the token-ids for Command test data-set,
        (7) path to the English vocabulary file,
        (8) path to the Command vocabulary file.
    """

    if FLAGS.dataset == "bash":
        prepare_bash(FLAGS.data_dir, FLAGS.nl_vocab_size, FLAGS.cm_vocab_size)
    if FLAGS.dataset == "jobs":
        prepare_jobs(FLAGS.data_dir, FLAGS.nl_vocab_size, FLAGS.cm_vocab_size)
    if FLAGS.dataset == "geo":
        prepare_jobs(FLAGS.data_dir, FLAGS.nl_vocab_size, FLAGS.cm_vocab_size)
    if FLAGS.dataset == "atis":
        prepare_jobs(FLAGS.data_dir, FLAGS.nl_vocab_size, FLAGS.cm_vocab_size)


if __name__ == "__main__":
    parse_brackets(sys.argv[1])
