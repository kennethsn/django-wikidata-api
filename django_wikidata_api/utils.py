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
