from plugins.BasePlugins import BaseUploadPlugin
from core.utils import utils
from pathlib import Path
from db.db import Entity
import shutil

class file(BaseUploadPlugin):
    name = 'base.file'
    format = 'path=%;type=%'
    works = 'entity'
    category = 'base'
    
    def run(self, args=None):
        path = args.get('path')
        type = args.get('type') # copy || move

        if path == None:
            raise AttributeError("Path was not passed")
        
        input_path = Path(path)
        if input_path.exists() == False:
            raise FileNotFoundError("File was not found")
        
        if input_path.is_dir() == True:
            raise ValueError("Path is directory")
        
        input_file_name = input_path.name
        input_file_ext = input_path.suffix[1:] # remove dot
        collection_dir = self.temp_dir
        move_result_path = Path(collection_dir + '\\' + input_file_name)

        # Creating entity
        
        if type == 'copy':
            print('Copied file')
            shutil.copy2(input_path, move_result_path)
        else:
            print('Moved file')
            shutil.move(input_path, move_result_path)
        
        return {
            'format': str(input_file_ext),
            'original_name': input_file_name,
            'filesize': input_path.stat().st_size
        }
