"""Extract bash templates that are paraphrases to each other."""

# builtin
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import os, sys
import sqlite3

if sys.version_info > (3, 0):
    from six.moves import xrange

from bashlex import data_tools, normalizer
from nlp_tools import tokenizer


def rewrite(ast, temp):
    """Rewrite an AST into an equivalent one using the given template."""
    arg_slots = normalizer.arg_slots(ast)

    def rewrite_fun(node):
        if node.kind == "argument" and not node.is_reserved():
            for i in xrange(len(arg_slots)):
                if not arg_slots[i][1] \
                        and arg_slots[i][0].arg_type == node.arg_type:
                    node.value = arg_slots[i][0].value
                    arg_slots[i][1] = True
                    break
        else:
            for child in node.children:
                rewrite_fun(child)

    # TODO: This is heuristically implemented in two steps.
    # Step 1 constructs an AST using the given template.
    # Step 2 fills the argument slots in the newly constructed AST using the
    # argument values from the original AST.
    ast2 = normalizer.normalize_ast(temp)
    if not ast2 is None:
        rewrite_fun(ast2)

    return ast2


class DBConnection(object):
    def __init__(self):
        self.conn = sqlite3.connect(os.path.join(
            os.path.dirname(__file__), "bash_rewrites.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False)
        self.cursor = self.conn.cursor()

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()

    def create_schema(self):
        c = self.cursor
        c.execute("CREATE TABLE IF NOT EXISTS Rewrites (s1 TEXT, s2 TEXT)")
        self.conn.commit()

    def add_rewrite(self, pair):
        c = self.cursor
        c.execute("INSERT INTO Rewrites (s1, s2) VALUES (?, ?)", pair)
        self.conn.commit()

    def clean_rewrites(self):
        c = self.cursor
        non_grammatical = []
        for s1, s2 in c.execute("SELECT s1, s2 FROM Rewrites"):
            ast = data_tools.bash_parser(s1)
            if not ast:
                non_grammatical.append(s1)
            ast2 = data_tools.bash_parser(s2)
            if not ast2:
                non_grammatical.append(s2)
        for s in non_grammatical:
            print("Removing %s from Rewrites" % s)
            c.execute("DELETE FROM Rewrites WHERE s1 = ?", (s,))
            c.execute("DELETE FROM Rewrites WHERE s2 = ?", (s,))

    def get_rewrite_templates(self, s1):
        rewrites = set([s1])
        c = self.cursor
        for s1, s2 in c.execute("SELECT s1, s2 FROM Rewrit7es WHERE s1 = ?",
                                (s1,)):
            rewrites.add(s2)
        return rewrites

    def get_rewrites(self, ast):
        rewrites = set([ast])
        s1 = data_tools.ast2template(ast, loose_constraints=True)
        c = self.cursor
        for s1, s2 in c.execute("SELECT s1, s2 FROM Rewrites WHERE s1 = ?",
                                (s1,)):
            rw = rewrite(ast, s2)
            if not rw is None:
                rewrites.add(rw)
        return rewrites

    def exist_rewrite(self, pair):
        s1, s2 = pair
        c = self.cursor
        for _ in c.execute("SELECT 1 FROM Rewrites WHERE s1 = ? AND s2 = ?",
                           (s1, s2)):
            return True
        return False


def clean_rewrites():
    with DBConnection() as db:
        db.create_schema()
        db.clean_rewrites()


def extract_rewrites(data):
    """Extract all pairs of rewrites from a parallel corpus."""
    nls, cms = data

    # Step 1: group pairs with the same natural language description.
    group_pairs_by_nl = collections.defaultdict(set)
    for nl, cm in zip(nls, cms):
        nl = nl.strip()
        cm = cm.strip()
        if nl.lower() == "na":
            continue
        if not nl:
            continue
        if not cm:
            continue
        nl_tokens, _ = tokenizer.ner_tokenizer(nl)
        nl_temp = ' '.join(nl_tokens)
        cm_temp = data_tools.cmd2template(cm)
        if not cm_temp in group_pairs_by_nl[nl_temp]:
            group_pairs_by_nl[nl_temp].add(cm_temp)

    # Step 2: cluster the commands with the same natural language explanations.
    merged = set()
    nls = group_pairs_by_nl.keys()
    for i in xrange(len(nls)):
        nl = nls[i]
        cm_temp_set = group_pairs_by_nl[nl]
        for j in xrange(i+1, len(nls)):
            nl2 = nls[j]
            cm_temp_set2 = group_pairs_by_nl[nl2]
            if len(cm_temp_set & cm_temp_set2) >= 2:
                for cm_temp in cm_temp_set:
                    if not cm_temp in group_pairs_by_nl[nl2]:
                        group_pairs_by_nl[nl2].add(cm_temp)
                merged.add(i)

    # Step 3: remove redundant clusters after merge.
    rewrites = {}
    for i in xrange(len(nls)):
        if not i in merged:
            rewrites[nls[i]] = group_pairs_by_nl[nls[i]]

    # Step 4: print extracted rewrites and store in database.
    with DBConnection() as db:
        db.create_schema()
        for nl, cm_temps in sorted(rewrites.items(), key=lambda x: len(x[1]),
                                   reverse=True)[:10]:
            if len(cm_temps) >= 2:
                for cm_temp1 in cm_temps:
                    for cm_temp2 in cm_temps:
                        if cm_temp1 == cm_temp2:
                            continue
                        if not db.exist_rewrite((cm_temp1, cm_temp2)):
                            db.add_rewrite((cm_temp1, cm_temp2))
                            print("* {} --> {}".format(cm_temp1, cm_temp2))
                print()


def test_rewrite(cmd):
    with DBConnection() as db:
        ast = data_tools.bash_parser(cmd)
        rewrites = list(db.get_rewrites(ast))
        for i in xrange(len(rewrites)):
            print("rewrite %d: %s" % (i, data_tools.ast2command(rewrites[i])))


if __name__ == "__main__":
    nl_path = sys.argv[1]
    cm_path = sys.argv[2]

    clean_rewrites()

    with open(nl_path) as f:
        nls = f.readlines()
    with open(cm_path) as f:
        cms = f.readlines()

    extract_rewrites((nls, cms))
    # while True:
    #     try:
    #         cmd = raw_input("> ")
    #         cmd = cmd.decode("utf-8")
    #         test_rewrite(cmd)
    #     except EOFError as ex:
    #         break
