import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bashlex"))

import data_tools, nast
import zss
from extract_rewrites import DBConnection

def ignore_differences(cmd):
    cmd = cmd.replace('-ls', '')
    cmd = cmd.replace('-print', '')
    cmd = cmd.replace('-print0', '')
    cmd = cmd.replace('-name', '-iname')
    cmd = cmd.replace('-regex', '-iregex')
    return cmd

def local_dist(s1, s2, skip_argument=False):
    score_list = {
        "FLAG_-ls:::":0,
        ":::FLAG_-ls":0,
        "FLAG_-print:::":0,
        ":::FLAG_-print":0,
        "FLAG_-print0:::":0,
        ":::FLAG_-print0":0,
        "FLAG_-name:::FLAG_-iname":0,
        "FLAG_-iname:::FLAG_-name":0,
        "FLAG_-regex:::FLAG_-iregex":0,
        "FLAG_-iregex:::FLAG_-regex":0,
        "FLAG_-name:::FLAG_-regex":0,
        "FLAG_-regex:::FLAG_-name":0,
        "FLAG_-name:::FLAG_-iregex":0,
        "FLAG_-iregex:::FLAG_-name":0,
        "FLAG_-iname:::FLAG_-regex":0,
        "FLAG_-regex:::FLAG_-iname":0,
        "FLAG_-iname:::FLAG_-iregex":0,
        "FLAG_-iregex:::FLAG_-iname":0
    }

    pair_key = ":::".join((s1, s2))
    if pair_key in score_list:
        return score_list[pair_key]
    else:
        if s1 == s2:
            return 0
        else:
            if s1.startswith("ARGUMENT_") and s2.startswith("ARGUMENT_") \
                    and skip_argument:
                return 0
            else:
                return 1

def str_local_dist(s1, s2):
    return local_dist(s1, s2)

def temp_local_dist(s1, s2):
    return local_dist(s1, s2, skip_argument=True)

def str_dist(ast1, ast2):
    return zss.simple_distance(ast1, ast2, nast.Node.get_children,
                               nast.Node.get_label, str_local_dist)

def temp_dist(ast1, ast2):
    return zss.simple_distance(ast1, ast2, nast.Node.get_children,
                               nast.Node.get_label, temp_local_dist)

def get_rewrite_templates(temps, db):
    rewrites = set()
    for temp in temps:
        rewrites |= db.get_rewrite_templates(temp)
    return rewrites

def get_rewrites(asts, db):
    rewrites = set()
    for ast in asts:
        rewrites |= db.get_rewrites(ast)
    return rewrites

def min_dist(asts, ast2, rewrite=True, ignore_arg_value=False):
    # tolerate ungrammatical predictions
    if not ast2:
        ast2 = data_tools.bash_parser("find")

    if rewrite:
        with DBConnection() as db:
            ast_rewrites = get_rewrites(asts, db)
    else:
        ast_rewrites = asts

    min_dist = sys.maxint
    for ast1 in ast_rewrites:
        dist = temp_dist(ast1, ast2) if ignore_arg_value else \
               str_dist(ast1, ast2)
        if dist < min_dist:
            min_dist = dist

    return min_dist

def one_match(asts, ast2, rewrite=True, ignore_arg_value=False):
    data_tools.pretty_print(asts[0])
    if rewrite:
        with DBConnection() as db:
            ast_rewrites = get_rewrites(asts, db)
    else:
        ast_rewrites = asts

    cmd2 = ignore_differences(data_tools.ast2template(
        ast2, loose_constraints=True, arg_type_only=ignore_arg_value))
    print("cmd2: " + cmd2)
    for ast1 in ast_rewrites:
        cmd1 = data_tools.ast2template(
            ast1, loose_constraints=True, arg_type_only=ignore_arg_value)
        print("cmd1: " + cmd1)
        cmd1 = ignore_differences(cmd1)
        if cmd1 == cmd2:
            return True
    return False

def template_match(ast1, ast2):
    temp1 = ignore_differences(
        data_tools.ast2template(ast1, loose_constraints=True))
    temp2 = ignore_differences(
        data_tools.ast2template(ast2, loose_constraints=True))
    return temp1 == temp2

def string_match(ast1, ast2):
    str1 = ignore_differences(
        data_tools.ast2template(ast1, loose_constraints=True, arg_type_only=False))
    str2 = ignore_differences(
        data_tools.ast2template(ast2, loose_constraints=True, arg_type_only=False))
    return str1 == str2
