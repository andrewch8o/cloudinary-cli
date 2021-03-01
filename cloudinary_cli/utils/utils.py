#!/usr/bin/env python3
import builtins
import json
import os
from csv import DictWriter
from functools import reduce
from hashlib import md5
from inspect import signature, getfullargspec
from multiprocessing import pool

import cloudinary
from jinja2 import Environment

from cloudinary_cli.defaults import logger, TEMPLATE_FOLDER

not_callable = ('is_appengine_sandbox', 'call_tags_api', 'call_context_api', 'call_cacheable_api', 'call_api', 'text',
                'account_config', 'reset_config')

BLOCK_SIZE = 65536


def etag(fi):
    file_hash = md5()
    with open(fi, 'rb') as f:
        fb = f.read(BLOCK_SIZE)
        while len(fb) > 0:
            file_hash.update(fb)
            fb = f.read(BLOCK_SIZE)

    return file_hash.hexdigest()


def is_builtin_class_instance(obj):
    return type(obj).__name__ in dir(builtins)


def get_help_str(module, block_list=(), allow_list=()):
    funcs = list(filter(
        lambda f:
        callable(module.__dict__[f])
        and not is_builtin_class_instance(module.__dict__[f])
        and f[0].islower()
        and (f not in block_list and block_list)
        and (f in allow_list or not allow_list),
        module.__dict__.keys()))

    template = "{0:" + str(len(max(funcs, key=len)) + 1) + "}({1})"  # Gets the maximal length of the functions' names

    return '\n'.join([template.format(f, ", ".join(list(signature(module.__dict__[f]).parameters))) for f in funcs])


def print_help(api, block_list=not_callable, allow_list=()):
    logger.info(get_help_str(api, block_list=block_list, allow_list=allow_list))


def log_exception(e, message=None):
    message = f"{message}, error: {str(e)}" if message is not None else str(e)
    logger.debug(message, exc_info=True)
    logger.error(message)


def load_template(language, template_name):
    filepath = os.path.join(TEMPLATE_FOLDER, language, template_name)
    try:
        with open(filepath) as f:
            template = Environment().from_string(f.read())
    except IOError:
        logger.error(f"Failed loading template: '{template_name}' for language: '{language}'")
        raise
    return template.render(**cloudinary.config().__dict__)


def parse_option_value(value):
    if value == "True" or value == "true":
        return True
    elif value == "False" or value == "false":
        return False
    try:
        value = json.loads(value)
    except Exception:
        pass
    if isinstance(value, int):
        value = str(value)
    return value


def parse_args_kwargs(func, params):
    spec = getfullargspec(func)
    n_args = len(spec.args) if spec.args else 0
    n_defaults = len(spec.defaults) if spec.defaults else 0

    n_req = n_args - n_defaults
    if len(params) < n_req:
        raise Exception("Function '{}' requires {} arguments".format(func.__name__, n_req))
    args = [parse_option_value(x) for x in params[:n_req]]

    kwargs = {k: parse_option_value(v) for k, v in [x.split('=') for x in params[n_req:]]} if params[n_req:] else {}
    return args, kwargs


def remove_string_prefix(string, prefix):
    return string[string.startswith(prefix) and len(prefix):]


def invert_dict(d):
    inv_dict = {}
    for k, v in d.items():
        inv_dict[v] = k

    return inv_dict


def write_json_list_to_csv(json_list, filename, fields_to_keep=()):
    with open(f'{filename}.csv', 'w') as f:
        if not fields_to_keep:
            fields_to_keep = list(reduce(lambda x, y: set(y.keys()) | x, json_list, set()))

        writer = DictWriter(f, fieldnames=fields_to_keep)
        writer.writeheader()
        writer.writerows(json_list)


def run_tasks_concurrently(func, tasks, concurrent_workers):
    thread_pool = pool.ThreadPool(concurrent_workers)
    thread_pool.starmap(func, tasks)


def confirm_action(message="Continue? (y/N)"):
    """
    Confirms whether the user wants to continue.

    :param message: The message to the user.
    :type message: string

    :return: Boolean indicating whether user wants to continue.
    :rtype bool
    """
    return get_user_action(message, {"y": True, "default": False})


def get_user_action(message, options):
    """
    Reads user input and returns value specified in options.

    In case user specified unknown option, returns default value.
    If default value is not set, returns None

    :param message: The message for user.
    :type message: string
    :param options: Options mapping.
    :type options: dict

    :return: Value according to the user selection.
    """
    r = input(message).lower()
    return options.get(r, options.get("default"))


def get_command_params(
        params,
        optional_parameter,
        optional_parameter_parsed,
        module,
        module_name):
    method = params[0]
    if method not in module.__dict__:
        raise Exception(f"Method {params[0]} does not exist in {module_name.capitalize()}.")

    func = module.__dict__.get(method)

    if not callable(func):
        raise Exception(f"{params[0]} is not callable.")

    args, kwargs = parse_args_kwargs(func, params[1:]) if len(params) > 1 else ([], {})

    kwargs = {
        **kwargs,
        **{k: v for k, v in optional_parameter},
        **{k: parse_option_value(v) for k, v in optional_parameter_parsed},
    }

    return func, args, kwargs


def whitelist_keys(data, keys):
    """
    Iterates over a list of dictionaries and keeps only the keys that were specified.

    :param data: A list of dictionaries.
    :type data: list
    :param keys: a list of keys to keep in each dictionary.
    :type keys: list

    :return: The whitelisted list.
    :rtype list
    """
    # no whitelist when fields are not provided or on a list of non-dictionary items.
    if not keys or any(not isinstance(i, dict) for i in data):
        return data

    return list(
        map(lambda x: {
            k: x[k]
            for k in keys if k in x},
            data)
    )


def merge_responses(all_res, paginated_res, fields_to_keep=None, pagination_field=None):
    if not pagination_field:
        for key in all_res:
            if all_res[key] != paginated_res.get(key, 0) and type(all_res[key]) == list:
                pagination_field = key

        if not pagination_field:  # should not happen
            raise Exception("Failed to detect pagination_field")

        # whitelist fields of the initial response
        all_res[pagination_field] = whitelist_keys(all_res[pagination_field], fields_to_keep)

    all_res[pagination_field] += whitelist_keys(paginated_res[pagination_field], fields_to_keep)

    return all_res, pagination_field


def normalize_list_params(params):
    """
    Normalizes parameters that could be provided as strings separated by ','.

    >>> normalize_list_params(["f1,f2", "f3"])
    ["f1", "f2", "f3"]

    :param params: Params to normalize.
    :type params: list

    :return: A list of normalized params.
    :rtype list
    """
    normalized_params = []
    for f in list(params):
        if "," in f:
            normalized_params += f.split(",")
        else:
            normalized_params.append(f)

    return normalized_params
