import collections
import json
import os

class ManPageLookUp(object):
    def __init__(self, path):
        self.table = load_syntax(path, verbose=False)

    def get_arg_types(self, cmd, verbose=False):
        try:
            return self.table[cmd]["arguments"]
        except KeyError, e:
            # TODO: This exception is not handled very well.
            if verbose:
                print("Error: command {} doesn't exist".format(cmd))
            return {"optional": ("Unknown", False), 
                    "non-optional": ("Unknown", False)}

    def get_flag_arg_type(self, cmd, flag, verbose=False):
        try:
            arg_type = self.table[cmd]["flags"][flag]
        except KeyError, e:
            # TODO: This exception is not handled very well.
            # This is mostly due to missing flags of commands in the grammar.
            if verbose:
                print("Error: {} is not a flag of {}".format(flag, cmd))
            return None
        if arg_type:
            return list(arg_type)[0]
        else:
            return None

# classes to build tree from json file
def load_syntax(json_files, verbose=True):
    manual_table = collections.defaultdict()
    counts = collections.defaultdict(int)
    for jsonfile in json_files:
        if verbose:
            print("loading from {}".format(jsonfile))
        with open(jsonfile, "r") as f:
            syntax = json.loads(f.read())
        for cmd in syntax:
            make_grammar_from_json_syntax(cmd, manual_table)
            counts[cmd["name"]] += 1
            if verbose:
                print(" > loaded {} ({})".format(cmd["name"],
                                                 counts[cmd["name"]]))
    return manual_table

def make_grammar_from_json_syntax(cmd, manual_table):
    if cmd["name"] in manual_table:
        command_table = manual_table[cmd["name"]]
    else:
        command_table = collections.defaultdict()
        command_table["flags"] = collections.defaultdict()
        command_table["arguments"] = {"optional": [],
                                      "non-optional": []}
        manual_table[cmd["name"]] = command_table
    if cmd["option"]["type"] == "compound_options":
        for o in cmd["option"]["commands"]:
            make_grammar_from_options(o, command_table)
    else:
        print("Unrecognized cmd_option type {}".format(cmd["option"]["type"]))

def make_grammar_from_options(x, command_table, optional=False, ):
    flag_table = command_table["flags"]
    arg_table = command_table["arguments"]

    if x["type"] == "compound_options":
        if x["commands"][0]["type"] == "flag_option" and \
            (len(x) == 2 and x["commands"][1]["type"] == "argument_option"):
                flag_name = "-" + x["commands"][0]["flag_name"]
                if not flag_name in flag_table:
                    flag_table[flag_name] = set()
                arg_type = x["commands"][1]["arg_type"]
                flag_table[flag_name].add(arg_type)
                if len(flag_table[flag_name]) > 1:
                    raise Exception("multiple argument types for {}".format(flag_name))
        else:
            for o in x["commands"]:
                make_grammar_from_options(o, command_table, optional)
    elif x["type"] == "optional_option":
        make_grammar_from_options(x["cmd"], command_table, optional=True)
    elif x["type"] == "exclusive_options":
        for o in x["commands"]:
            make_grammar_from_options(o, command_table, optional)
    elif x["type"] == "flag_option":
        flag_name = "-" + x["flag_name"]
        if not flag_name in flag_table:
            flag_table[flag_name] = set()
    elif x["type"] == "long_flag_option":
        flag_name = "--" + x["flag_name"]
        if not flag_name in flag_table:
            flag_table[flag_name] = set()
        if x["arg_exists"]:
            flag_table[flag_name].add(x["argument"]["arg_type"])
            if len(flag_table[flag_name]) > 1:
                raise Exception("multiple argument types for {}".format(flag_name))
    elif x["type"] == "argument_option":
        if optional:
            arg_table["optional"].append([x["arg_type"], x["isList"], False])
        else:
            arg_table["non-optional"].append([x["arg_type"], x["isList"], False])
    else:
        raise Exception("unknown type: {}".format(x["type"]))

if __name__ == "__main__":
    man_lookup = ManPageLookUp([os.path.join(os.path.dirname(__file__),
                                             "primitive_cmds_grammar.json")])
    print(man_lookup.get_arg_types("find"))
    while True:
        try:
            cmd = raw_input("> Command:")
            flag = raw_input("> Flag:")
            print(man_lookup.get_flag_arg_type(cmd, flag))
        except EOFError as ex:
            break
