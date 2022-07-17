""" POC module to yield media files from configs for the `cld sync` routine tests
"""
import os
import csv
import piexif
import shutil
import logging
import hashlib
from pathlib import Path

class CONFIG:
    '''Defines module configuration'''
    root_dir = Path(__file__).parent.resolve()
    media_template = Path.joinpath(root_dir,"default_asset_file.jpg")


class CONFIG_FIELDS:
    '''Defines field names in test configuration file.'''
    asset_path = 'asset_rel_path'

def read_config(config_file_path):
    '''Reads config file.

    Config file is assumed to be a CSV file having at least a `CONFIG_FIELDS.asset_path` column

    Parameters
    ----------
    config_file_path: str
        Path to the configuration file

    Yields
    -------
    dict
        Config record.
    '''
    with open(config_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for config_record in reader:
            yield config_record

def yield_files_from_config(config_file_path, root_folder):
    '''Yields new files at the specified location according to config

    Parameters
    ----------
    config_file_path: str
        Path to the configuration file
    root_folder: str
        Root folder path to yield new files under
    '''
    for config_record in read_config(config_file_path):
        try:
            new_file_rel_path = config_record[CONFIG_FIELDS.asset_path]
            new_file_abs_path = yield_local_media_file(
                root_folder              = root_folder,
                relative_file_path       = new_file_rel_path,
                template_media_file_path = CONFIG.media_template)
            with open(new_file_abs_path, 'rb') as new_file:
                md5_digest = hashlib.md5(new_file.read()).hexdigest()
            logging.info(f"NEW: MD5:'{md5_digest}' -- '{new_file_abs_path}'")
        except:
            logging.exception(f"Failed to instantiate '{new_file_rel_path}' from config file '{config_file_path}'")


def add_exif_comment(media_file_path, value):
    '''Adds file path as the UserComment EXIF property to the media file. 
    
    The media file is assumed to be in the format that supports EXIF properties
    https://en.wikipedia.org/wiki/Exif
    
    Parameters
    ----------
    media_file_path : str
        Path to the media file.
    value : str
        Value to be set for the UserComment Exif property
    '''
    exif_dict = piexif.load(media_file_path)
    exif_dict['Exif'][piexif.ExifIFD.UserComment] = value.encode()
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, media_file_path)

def yield_local_media_file(root_folder, relative_file_path, template_media_file_path):
    '''Yields a media file at a given path by copying the template file and modifying a copy.
    
    Parameters
    ----------
    root_folder : str
        Root folder to create files under.
    relative_file_path : str
        File path for the new file to create (relative to the `root_folder`).
    template_media_file_path: str
        Full path to the media file used as a template.

    Returns
    -------
    str
        Absolute path of the newly created file
    '''
    src_file_pathobj = Path(template_media_file_path).resolve()
    dest_file_pathobj = Path(root_folder).joinpath(relative_file_path).resolve()

    # Python <= 3.7 support https://stackoverflow.com/questions/33625931/copy-file-with-pathlib-in-python
    src_file_path = str(src_file_pathobj)
    dest_file_path = str(dest_file_pathobj)
    dest_folder_path = str(dest_file_pathobj.parent)

    os.makedirs(dest_folder_path, exist_ok=True)
    shutil.copy(src_file_path, dest_file_path)

    add_exif_comment(
        media_file_path=dest_file_path, 
        value=relative_file_path)

    return dest_file_path