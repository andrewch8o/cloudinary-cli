""" POC module to yield media files from configs for the `cld sync` routine tests
"""
import csv
from pathlib import Path

class CONFIG:
    '''Defines module configuration'''
    root_dir = Path(__file__).resolve()
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
    pass

def add_exif_comment(media_file_path):
    '''Adds file path as the UserComment EXIF property to the media file. 
    
    The media file is assumed to be in the format that supports EXIF properties
    https://en.wikipedia.org/wiki/Exif
    
    Parameters
    ----------
    media_file_path : str
        Path to the media file.
    '''
    pass

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
    '''
    pass