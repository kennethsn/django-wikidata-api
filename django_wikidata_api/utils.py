# coding=utf-8
""" utility functions needed for django-wikidata-api. """
import re


def get_wikidata_field(wikidata_response_dict, key, default=None):
    # TODO: create a wikidata response object and move this to its instance method
    try:
        return wikidata_response_dict[key].get('value', default)
    except (KeyError, ValueError):
        return default


def get_wikidata_concat_list(wikidata_response_dict, key, default=None, separator='|'):
    if not default:
        default = []
    field = get_wikidata_field(wikidata_response_dict, key, default)
    return field.split(separator) if field else default


def dict_has_substring(haystack, needle):
    return all(token in str(haystack.values()).lower() for token in str(needle).lower().split())


def set_kwargs(obj, kwargs):
    for key, value in kwargs.items():
        setattr(obj, key, value)


def is_private_name(name_string):
    """
    Check if this string is written in a private/protected reference python convention
    Args:
        name_string (str):

    Returns (Bool): True if variable begins with "_", False otherwise

    Examples:
        >>> is_private_name("_some_var_name")
        True
        >>> is_private_name("some_var_name")
        False
    """
    return name_string.startswith("_")


def extract_from_string_by_regex(regex, search_string, default=None):
    """
    Get a matched value from a string based on a regular expression.

    Args:
        regex (str):
        search_string (str):
        default (Optional): Return value if not found

    Returns (Optional[str]):
    """
    match = re.search(regex, search_string)
    return match.group() if match else default
