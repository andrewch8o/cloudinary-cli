""" POC module to yield media files from configs for the `cld sync` routine tests
"""

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