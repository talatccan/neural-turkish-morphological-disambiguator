
import codecs

from collections import defaultdict as dd

from keras.utils.np_utils import to_categorical


def read_datafile(path):
    word = []
    sentences = []
    # label2ids = {'surface_form': dd(int),
    #              'morph_token': dd(int)}
    label_classes = ['surface_form',
                     'root',
                     'morph_token',
                     'character']
    label2ids = {label: dd(int) for label in label_classes +
                 [label_class + "_count" for label_class in label_classes] +
                 [label_class + "_unique_count" for label_class in label_classes]}

    characters_seen = set()

    max_sentence_length = 0
    max_surface_form_length = 0
    max_word_root_length = 0
    max_n_analysis = 0
    max_analysis_length = 0

    def _encode_label(dictionary_name, label, label2ids):
        """
        record label
        :param dictionary_name:
        :param label: string
        :param label2ids: should be a dictionary of (string,defaultdict)
        :return:
        """
        label2ids[dictionary_name + "_count"]['value'] += 1
        if label in label2ids[dictionary_name]:
            pass
        else:
            label2ids[dictionary_name + "_unique_count"]['value'] += 1
            label2ids[dictionary_name][label] = label2ids[dictionary_name + "_unique_count"][
                'value']

    def encode_label(dictionary_name, label):
        """
        record label
        :param dictionary_name:
        :param label: string
        :param label2ids: should be a dictionary of (string,defaultdict)
        :return:
        """
        _encode_label(dictionary_name, label, label2ids)

    with codecs.open(path, mode="r") as f:
        line = f.readline()
        while line:
            tokens = line.split(" ")
            surface_form = tokens[0].decode('utf-8')
            encode_label('surface_form', surface_form)
            analyses = [t.decode('utf-8') for t in tokens[1:]]
            if surface_form in ["<DOC>", "<TITLE>", "</DOC>", "</TITLE>"]:
                pass # do nothing, skip line
            elif surface_form == "<S>":
                sentence = [] # prepare the sentence variable
            elif surface_form == "</S>":
                # record the sentence
                assert len(sentence) > 0, "sentence with length 0?"
                roots = []
                morph_tokens = []
                for w in sentence:
                    w_roots = []
                    w_affixes = []
                    for analysis in w[1:]:
                        w_roots.append(analysis[0])
                        w_affixes.append(analysis[1:])
                    roots.append(w_roots)
                    morph_tokens.append(w_affixes)
                processed_sentence = {'sentence_length': len(sentence),
                             'surface_forms': [w[0] for w in sentence],
                             'surface_form_lengths': [len(w[0]) for w in sentence],
                             'roots': roots,
                             'root_lengths': [[len(root) for root in word] for word in roots],
                             'morph_tokens': morph_tokens,
                             'morph_token_lengths': [[len(morph_tokens) for morph_tokens in word] for word in morph_tokens]}
                if len(sentence) > max_sentence_length:
                    max_sentence_length = len(sentence)
                if max([len(w[0]) for w in sentence]) > max_surface_form_length:
                    max_surface_form_length = max([len(w[0]) for w in sentence])
                if max([max(root_lengths) for root_lengths in processed_sentence['root_lengths']]) > max_word_root_length:
                    max_word_root_length = max([max(root_lengths) for root_lengths in processed_sentence['root_lengths']])
                if max([len(w[1:]) for w in sentence]) > max_n_analysis:
                    max_n_analysis = max([len(w[1:]) for w in sentence])
                if max([len(analysis[1:]) for w in sentence for analysis in w[1:]]) > max_analysis_length:
                    max_analysis_length = max([len(analysis[1:]) for w in sentence for analysis in w[1:]])
                # print processed_sentence
                sentences.append(processed_sentence)
            else:
                # this is a legit surface form, extract morph. analyses
                encode_label('surface_form', surface_form)
                characters_seen = characters_seen.union(set(surface_form))
                word.append(surface_form)
                for morph_analysis in analyses:
                    morph_tokens = morph_analysis.split("+")
                    encode_label('root', morph_tokens[0])
                    for morph_token in morph_tokens[1:]:
                        encode_label('morph_token', morph_token)
                    root = morph_tokens[0]
                    morph_tokens = morph_tokens[1:]
                    word.append([root] + morph_tokens)
                # print word
                sentence.append(word)
                word = []
            line = f.readline()

    for c in characters_seen:
        encode_label("character", c)

    for m_str, m_value in [["max_sentence_length", max_sentence_length],
              ["max_surface_form_length", max_surface_form_length],
              ["max_word_root_length", max_word_root_length],
              ["max_n_analysis", max_n_analysis],
              ["max_analysis_length", max_analysis_length]]:
        label2ids[m_str] = m_value
    return sentences, label2ids

import numpy as np

def encode_sentence(sentence, label2ids):
    sentences_word_root_input = np.zeros(
        [label2ids["max_sentence_length"], label2ids["max_n_analysis"], label2ids["max_word_root_length"]],
        dtype=np.int32)

    sentences_analysis_input = np.zeros(
        [label2ids["max_sentence_length"], label2ids["max_n_analysis"], label2ids["max_analysis_length"]],
        dtype = np.int32)

    surface_form_input = np.zeros([label2ids["max_sentence_length"], label2ids["max_surface_form_length"]],
                                  dtype=np.int32)

    correct_tags_input = to_categorical(np.zeros([label2ids["max_sentence_length"]], dtype=np.int32),
                                        label2ids["max_n_analysis"])

    sentence_length = sentence['sentence_length']
    # word_roots
    for i, word in enumerate(sentence['roots']):
        for j, root in enumerate(word):
            # print root
            for k, c in enumerate(root):
                sentences_word_root_input[i, j, k] = label2ids["character"][c]

    # analyses
    for i, morph_tokens in enumerate(sentence['morph_tokens']):
        for j, morph_token in enumerate(morph_tokens):
            # print root
            for k, m in enumerate(morph_token):
                sentences_analysis_input[i, j, k] = label2ids["morph_token"][m]

    # surface forms
    for i, surface_form in enumerate(sentence['surface_forms']):
        for j, c in enumerate(surface_form):
            surface_form_input[i, j] = label2ids["character"][c]

    # print sentences_word_root_input
    return sentences_word_root_input, sentences_analysis_input, surface_form_input, correct_tags_input



if __name__ == "__main__":
    sentences, label2ids = read_datafile("sample.data")
    encode_sentence(sentences[0], label2ids)
    print sentences
    print label2ids
