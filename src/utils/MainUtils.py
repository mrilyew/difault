import secrets, os, platform, sys, random, json, mimetypes, wget, zipfile
from contextlib import contextmanager
from resources.Consts import consts
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import urlencode
import re

def parse_args():
    '''
    Parses sys.argv to dict.
    '''
    args = sys.argv
    parsed_args = {}
    key = None
    for arg in args[1:]:
        if arg.startswith('--'):
            if key:
                parsed_args[key] = True
            key = arg[2:]
            parsed_args[key] = True
        #elif arg.startswith('-'):
        #    if key:
        #        parsed_args[key] = True
        #    key = arg[1:]
        #    parsed_args[key] = True
        else:
            if key:
                parsed_args[key] = arg
                key = None
            else:
                pass

    return parsed_args

def parse_params(input_data):
    '''
    Parses url params.
    '''
    params = {}
    params_arr = input_data.split('&')
    for param in params_arr:
        try:
            _spl = param.split('=')
            params[_spl[0]] = _spl[1]
        except IndexError:
            pass
    
    return params

def random_int(min, max):
    '''
    Makes random integer.

    Params: min, max
    '''
    return random.randint(min, max)

def parse_json(text):
    '''
    Parses JSON from text
    '''
    return json.loads(text)
    
def dump_json(obj, indent=None):
    '''
    Serializes JSON object to text
    '''
    return json.dumps(obj,ensure_ascii=False,indent=indent)

def remove_protocol(link):
    '''
    Removes protocol from link.
    '''
    protocols = ["https", "http", "ftp"]
    final_link = link
    for protocol in protocols:
        if final_link.startswith(protocol):
            final_link.replace(f"{protocol}://", "")

    return final_link

# УГАДАЙ ОТКУДА :)
def proc_strtr(text: str, length: int = 0, multipoint: bool = True):
    '''
    Cuts string to "length".
    '''
    newString = text[:length]

    if multipoint == False:
        return newString
    
    return newString + ("..." if text != newString else "")

def parse_db_entities(i, allowed_entities = ['cu', 'su']):
    '''
    Recieves contentunits and storageunits by string.
    '''
    from db.ContentUnit import ContentUnit
    from db.StorageUnit import StorageUnit

    out = []
    els = [] # сразу не понял
    if type(i) == str:
        els = i.split(',')
    else:
        els = i

    for el in els:
        interm_out = None
        el_type, el_id = el.split('_')
        if el_type not in allowed_entities:
            continue

        match(el_type):
            case 'cu' | 'contentunit' | 'conuni':
                interm_out = ContentUnit.get(el_id)
            case 'su' | 'storageunit' | 'stouni':
                interm_out = StorageUnit.get(el_id)

        out.append(interm_out)

    return out

def extract_metadata_to_dict(mtdd):
    metadata_dict = defaultdict(list)

    for line in mtdd:
        key_value = line.split(": ", 1)
        if key_value[0].startswith('- '):
            key = key_value[0][2:]
            metadata_dict[key].append(key_value[1])

    return dict(metadata_dict)

def json_values_to_string(data, separator = ''):
    result = []

    if isinstance(data, dict):
        for value in data.values():
            result.append(json_values_to_string(value))

    elif isinstance(data, list):
        for item in data:
            result.append(json_values_to_string(item))

    else:
        return str(data)

    return separator.join(filter(None, result))

def get_mime_type(filename: str):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type

def get_ext(filename: str):
    file_splitted_array = filename.split('.')
    file_output_ext = ''
    if len(file_splitted_array) > 1:
        file_output_ext = file_splitted_array[-1]

    return file_output_ext

def get_random_hash(__bytes: int = 32):
    return secrets.token_urlsafe(__bytes)

def clear_json(__json):
    if isinstance(__json, dict):
        return {key: clear_json(value) for key, value in __json.items() if isinstance(value, (dict, list, str))}
    elif isinstance(__json, list):
        return [clear_json(item) for item in __json if isinstance(item, (dict, list, str))]
    elif isinstance(__json, str):
        if __json.startswith("https://") == False and __json.startswith("http://") == False:
            return __json
    elif isinstance(__json, int):
        return __json
    else:
        return None
    
def name_from_url(input_url):
    parsed_url = urlparse(input_url)
    path = parsed_url.path

    if path.endswith('/') or path == "":
        return "index", "html"
    
    filename = os.path.basename(path)
    OUTPUT_NAME, OUTPUT_NAME_EXT = os.path.splitext(filename)
    if not OUTPUT_NAME_EXT:
        OUTPUT_NAME_EXT = ""
    else:
        OUTPUT_NAME_EXT = OUTPUT_NAME_EXT[1:]
    
    return OUTPUT_NAME, OUTPUT_NAME_EXT

@contextmanager
def override_db(__classes = [], __db = None):
    '''
    Overrides entity db
    '''
    old_db = None
    for __class in __classes:
        old_db = __class._meta.database
        __class._meta.database = __db
    
    yield

    for __class in __classes:
        __class._meta.database = old_db

def valid_name(text):
    '''
    Creates saveable name (removes forbidden characters in NTFS)
    '''
    safe_filename = re.sub(r'[\\/*?:"<>| ]', '_', text)
    safe_filename = re.sub(r'_+', '_', safe_filename)
    safe_filename = safe_filename.strip('_')
    if not safe_filename:
        return "unnamed"

    return safe_filename

def replace_link_gaps(input_data, link_to_linked_files, recurse_level = 0):
    if isinstance(input_data, dict):
        return {key: replace_link_gaps(value, link_to_linked_files) for key, value in input_data.items()}
    elif isinstance(input_data, list):
        return [replace_link_gaps(item, link_to_linked_files) for item in input_data]
    elif isinstance(input_data, str):
        try:
            if "__$|cu_" in input_data:
                got_id = int(input_data.replace("__$|cu_", ""))
                for linked in link_to_linked_files:
                    if linked.id == got_id and linked.self_name == "ContentUnit":
                        return linked.getFormattedInfo(recursive=True,recurse_level=recurse_level+1)
                    else:
                        return input_data
            elif "__$|su_" in input_data:
                got_id = int(input_data.replace("__$|su_", ""))
                for linked in link_to_linked_files:
                    if linked.id == got_id and linked.self_name == "StorageUnit":
                        return linked.getFormattedInfo(recursive=True,recurse_level=recurse_level+1)
                    else:
                        return input_data
            else:
                return input_data
        except Exception as __e:
            return input_data
    else:
        return input_data

def replace_cwd(input_string: str):
    return input_string.replace("?cwd?", str(consts.get("cwd")))

def replace_src(input_string: str):
    return input_string.replace("\\src", "")

def list_conversation(i_list):
    if type(i_list) == dict:
        return [i_list]
    
    return i_list

def resolve_lang(translation_dict: dict, lang_code: str):
    return translation_dict.get(lang_code)

def entity_sign(unit):
    return f"__$|{unit.short_name}_{unit.id}"

def entity_link(dict_link: dict, key_name: str, unit):
    dict_link[key_name] = f"__$|{entity_sign(unit)}"
