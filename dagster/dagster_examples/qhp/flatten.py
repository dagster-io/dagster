import glob
import json
import math
import os
import os.path
import random
import sys
import time
import traceback
from collections import defaultdict

# import great_expectations as ge
import numpy as np
import pandas as pd

DISCONNECTED_SUBTREE = -99999.12345


def summarize_json_tree_recursive_iterator(obj, prefix):
    """
    Return a generator that traverses the object tree, returning (prefix, type, value) tuples

    Note: This syntax assumes that only lists (not dicts) are iterable objects.
    """
    if isinstance(obj, dict):
        yield (prefix, 'dict', None)
        for k, v in obj.items():
            for i in summarize_json_tree_recursive_iterator(v, prefix + "." + str(k)):
                yield i

    elif any(isinstance(obj, t) for t in (list, tuple)):
        yield (prefix, 'list', None)
        for item in obj:
            for i in summarize_json_tree_recursive_iterator(item, prefix + ".*"):
                yield i

    else:
        yield (prefix, str(type(obj)), obj)


# def summarize_json_tree(full_json):
#     count_nested_map = defaultdict(int)
#     set_nested_map = defaultdict(set)
#     type_map = defaultdict(set)
#     for key, type_, item in summarize_json_tree_recursive_iterator(full_json, "@"):
#         count_nested_map[key] += 1
#         set_nested_map[key].update([item])
#         type_map[key].update([type_])

#     field_summaries = []

#     total_occurrences = dict(count_nested_map)
#     unique_value_counts = dict([(k, len(v)) for k, v in set_nested_map.items()])

#     for k, v in total_occurrences.items():
#         if k == '@':
#             parent = None
#         # elif k.split('.')[-2] == '*':
#         #     parent = '.'.join(k.split('.')[:-2])
#         else:
#             parent = '.'.join(k.split('.')[:-1])

#         # print k, k.split('.')[-1], parent
#         field_summaries.append(
#             {
#                 'field': k,
#                 'depth': len(str(k).split('.')),
#                 'parent': parent,
#                 'data_types': type_map[k],
#                 'total_touch_count': v,
#                 'parent_touch_count': total_occurrences[parent] if parent != None else None,
#                 'unique_value_counts': unique_value_counts[k],
#             }
#         )

#     df = ge.dataset.PandasDataSet(field_summaries)
#     df.sort_values(['depth', 'field'], ascending=True)
#     return df


def derive_features_from_summary(summary_df):
    df = summary_df.copy()
    df['children_count'] = df['field'].map(lambda x: (df['parent'] == x).sum())
    df['children_touch_count'
       ] = df['field'].map(lambda x: df['total_touch_count'][df['parent'] == x].sum())
    df['occ_ratio'] = df.total_touch_count / df.parent_touch_count
    df['uniq_ratio'] = df.unique_value_counts / df.total_touch_count
    # df['table_score_z'] =     1.0*(df.occ_ratio>1) +     2.0*(df.occ_ratio>2) +     3.0*(df.occ_ratio>3) +     4.0*(df.occ_ratio>5) +     5.0*(df.occ_ratio>10) +     6.0*df.data_types.map(lambda x: str(x)=="set(['list'])") +     3.0*df.data_types.map(lambda x: str(x)=="set(['dict'])")
    df['table_score_z'] = df.children_touch_count + 6.0 * df.data_types.map(
        lambda x: str(x) == "set(['list'])"
    ) + 3.0 * df.data_types.map(lambda x: str(x) == "set(['dict'])")

    df['table_score_p'] = df['table_score_z'].map(lambda z: 1 / (1 + np.exp((10 - z))))

    # df.sort_values(['table_score_p', 'field'], ascending=False)[['depth', 'field', 'table_score_p']]
    return df


class Flattener(object):
    def __init__(self, full_json, table_fields):
        """
        NB: I don't love using this kind of stateful function, but it's the cleanest way I've found to handle this tree traversal operation
        """
        self.json_obj = full_json

        self.table_fields = table_fields
        self.json_list_dict = dict([(f, []) for f in table_fields])

        self.traverse_tree(self.json_obj, "@", None, None)

        self.df_dict = {}
        for k, v in self.json_list_dict.items():
            # print json.dumps(v, indent=2)
            self.df_dict[k] = pd.DataFrame(v)

    def get_df_dict(self):
        return self.df_dict

    def traverse_tree(self, json_obj, prefix, ancestor_prefix, ancestor_id):

        parent_prefix = '.'.join(prefix.split('.')[:-1])
        is_disconnected_list = False

        if prefix in self.table_fields:
            id_ = len(self.json_list_dict[prefix]) + 1
            new_ancestor_prefix = prefix
            new_ancestor_id = id_
        else:
            new_ancestor_prefix = ancestor_prefix
            new_ancestor_id = ancestor_id

        if isinstance(json_obj, dict):
            rval = {}
            for k, v in json_obj.items():
                child_obj = self.traverse_tree(
                    v, prefix + "." + str(k), new_ancestor_prefix, new_ancestor_id
                )

                if child_obj != DISCONNECTED_SUBTREE:
                    rval[k] = child_obj

        elif any(isinstance(json_obj, t) for t in (list, tuple)):
            is_disconnected_list = True

            rval = []
            for i, item in enumerate(json_obj):
                child_obj = self.traverse_tree(
                    item, prefix + ".*", new_ancestor_prefix, new_ancestor_id
                )

                if child_obj != DISCONNECTED_SUBTREE:
                    rval.append(child_obj)
                    is_disconnected_list = False

        else:
            rval = json_obj

        if prefix in self.table_fields:
            if type(rval) != dict:
                rval = {"value": rval}
            # print rval, prefix
            rval["id_"] = id_

            if ancestor_id != None:
                rval["parent_id"] = ancestor_id

            self.json_list_dict[prefix].append(rval)

            return DISCONNECTED_SUBTREE

        elif is_disconnected_list:
            return DISCONNECTED_SUBTREE

        else:
            return rval


def flatten_json_to_dataframes(full_json, table_fields):
    flattener = Flattener(full_json, table_fields)
    return flattener.get_df_dict()
