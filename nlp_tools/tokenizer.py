#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Natural language input tokenizer.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re, sys
if sys.version_info > (3, 0):
    from six.moves import xrange

from . import constants, ner
from .spellcheck import spell_check as spc

# from nltk.stem.wordnet import WordNetLemmatizer
# lmtzr = WordNetLemmatizer()
from nltk.stem import SnowballStemmer
stemmer = SnowballStemmer("english")


def clean_sentence(sentence):
    """
    Fix punctuation errors and extract main content of a sentence.
    """

    # remove content in parentheses
    _PAREN_REMOVE = re.compile('\([^)]*\)')
    sentence = re.sub(_PAREN_REMOVE, '', sentence)

    try:
        sentence = sentence.replace("“", '"')
        sentence = sentence.replace("”", '"')
        sentence = sentence.replace('‘', '\'')
        sentence = sentence.replace('’', '\'')
    except UnicodeDecodeError:
        sentence = sentence.replace("“".decode('utf-8'), '"')
        sentence = sentence.replace("”".decode('utf-8'), '"')
        sentence = sentence.replace('‘'.decode('utf-8'), '\'')
        sentence = sentence.replace('’'.decode('utf-8'), '\'')
    sentence = sentence.replace('`\'', '"') \
            .replace('``', '"') \
            .replace("''", '"') \
            .replace(' \'', ' "') \
            .replace('\' ', '" ') \
            .replace('`', '"') \
            .replace('(', ' ( ') \
            .replace(')', ' ) ')
            # .replace('[', '[ ') \
            # .replace('{', '{ ') \
            # .replace(']', ' ]') \
            # .replace('}', ' }') \
            # .replace('<', '< ') \
            # .replace('>', ' >')
    sentence = re.sub('^\'', '"', sentence)
    sentence = re.sub('\'$', '"', sentence)

    sentence = re.sub('(,\s+)|(,$)', ' ', sentence)
    sentence = re.sub('(;\s+)|(;$)', ' ', sentence)
    sentence = re.sub('(:\s+)|(:$)', ' ', sentence)
    sentence = re.sub('(\.\s+)|(\.$)', ' ', sentence)

    # convert abbreviation writings and negations
    sentence = re.sub('\'s', ' \'s', sentence)
    sentence = re.sub('\'re', ' \'re', sentence)
    sentence = re.sub('\'ve', ' \'ve', sentence)
    sentence = re.sub('\'d', ' \'d', sentence)
    sentence = re.sub('\'t', ' \'t', sentence)

    sentence = re.sub("^[T|t]o ", '', sentence)
    sentence = re.sub('\$\{HOME\}', '\$HOME', sentence)
    sentence = re.sub('"?normal\/regular"?', 'regular', sentence)
    sentence = re.sub('"?regular\/normal"?', 'regular', sentence)
    sentence = re.sub('"?normal/regualar"?', 'regular', sentence)
    sentence = re.sub(
        '"?file\/directory"?', 'file or directory', sentence)
    sentence = re.sub(
        '"?files\/directories"?', 'files and directories', sentence)
    sentence = re.sub('"?name\/path"?', 'name or path', sentence)
    sentence = re.sub('"?names\/paths"?', 'name or path', sentence)

    return sentence


def basic_tokenizer(sentence, lower_case=True, lemmatization=True,
                    remove_stop_words=True, correct_spell=True, verbose=False):
    """Very basic English tokenizer."""
    sentence = clean_sentence(sentence)
    print(sentence)
    words = [x[0] for x in re.findall(constants._WORD_SPLIT_RESPECT_QUOTES, sentence)]
    print(words)

    normalized_words = []
    for i in xrange(len(words)):
        print(words[i])
        word = words[i].strip()
        # remove unnecessary upper cases
        if lower_case:
            # if i == 0 and word[0].isupper() \
            #         and len(word) > 1 and word[1:].islower():
            #     word = word.lower()
            if len(word) > 1 and constants.is_english_word(word) \
                    and not constants.with_quotation(word):
                word = word.lower()

        # spelling correction
        if correct_spell:
            if word.isalpha() and word.islower() and len(word) > 2:
                old_w = word
                word = spc.correction(word)
                if word != old_w:
                    if verbose:
                        print("spell correction: {} -> {}".format(old_w, word))

        # remove English stopwords
        if remove_stop_words:
            if word in constants.ENGLISH_STOPWORDS:
                continue

        # covert number words into numbers
        if word in constants.word2num:
            word = str(constants.word2num[word])

        # lemmatization
        if lemmatization:
            if not re.match(constants._SPECIAL_SYMBOL_RE, word):
                try:
                    word = stemmer.stem(word.decode('utf-8'))
                except AttributeError:
                    word = stemmer.stem(word)

        # remove empty words
        if not word.strip():
            continue

        normalized_words.append(word)

    return normalized_words


def ner_tokenizer(sentence, lower_case=True, lemmatization=True,
                  remove_stop_words=True, correct_spell=True):
    words = basic_tokenizer(sentence, lower_case=lower_case,
                            lemmatization=lemmatization,
                            remove_stop_words=remove_stop_words,
                            correct_spell=correct_spell)
    return ner.annotate(words)

# --- Utility functions --- #

def test_nl_tokenizer():
    while True:
        nl = raw_input("> ")
        tokens, ners = ner_tokenizer(nl)
        print(tokens, ners[0])


if __name__ == '__main__':
    test_nl_tokenizer()
