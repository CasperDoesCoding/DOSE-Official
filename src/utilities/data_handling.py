from os import path, makedirs, walk
from typing import Dict

DEFAULT_RELATIVE_DATA_PATH: str = "data"

DEFAULT_FOLDERS = ["configuration", "logs"]

main_data_handler: "DataHandler" = None

class Folder:
    """
    Class that mimics a folder in the project.
    
    Attributes
    ----------
    parent_folder : Folder
        The parent folder of the folder.
    parent_folder_name : str
        The name of the parent folder of the folder.
    name : str
        The name of the folder.
    path : str
        The path of the folder.
    subfolders : list of Folder
        The subfolders of the folder.
        
    Notes
    -----
    This class is not meant to be used for creating folders. It is meant to be used for representing folders in the project.    
    """
    
    def __init__(self, folder_path: str) -> None:
        """
        Initializes the folder.
        
        Parameters
        ----------
        folder_path : str
            The path of the folder.
        """
        
        # check if the folder path is a valid folder
        if not path.isdir(folder_path):
            raise ValueError(f"folder_path '{folder_path}' is not a valid folder path.")
        
        # set the name and path of the folder
        self.parent_folder: Folder = self
        self.parent_folder_name: str = "ROOT"
        
        self.name: str = path.basename(folder_path)
        self.path: str = folder_path
        
        # get the subfolders and files
        self.subfolders: list[Folder] = []

        # get all the subfolders in the folder
        folders = next(walk(self.path))[1]

        for folder in folders:
            new_folder = Folder(path.join(self.path, folder))
            self.add_subfolder(new_folder)
    
    def get_file(self, file_name: str, create_if_none: bool = False):
        """
        Gets a file in the folder.
        
        Parameters
        ----------
        file_name : str
            The name of the file to get.
        
        Returns
        -------
        File
            The file with the given name. If the file does not exist, returns None unless create_if_none is True.
        """
        # get the folder
        file_path: str = path.join(self.path, file_name)
        
        # check if the file exists
        if path.isfile(file_path):
            return file_path

        elif create_if_none:
            # create new json file
            with open(path.join(self.path, file_name), "w") as new_file:
                new_file.write("{}")

            # get the new file
            return self.get_file(file_name)
    
    def add_subfolder(self, subfolder: "Folder") -> None:
        """
        Adds a subfolder to the folder and sets the parent folder of the subfolder.
        
        Parameters
        ----------
        subfolder : Folder
            The subfolder to add.
        
        Returns
        -------
        None
        """
        # add the subfolder to the list of subfolders
        self.subfolders.append(subfolder)

        # set the parent folder of the subfolder
        subfolder.parent_folder = self
        subfolder.parent_folder_name = self.name
        
        return None
    
    def get_subfolder(self, subfolder_name: str) -> "Folder":
        """
        Gets a subfolder of the folder.
        
        Parameters
        ----------
        subfolder_name : str
            The name of the subfolder to get.
        
        Returns
        -------
        Folder
            The subfolder with the given name. If the subfolder does not exist, returns None.
        """
        return next(
            (
                subfolder
                for subfolder in self.subfolders
                if subfolder.name == subfolder_name
            ),
            None,
        )
    
    def get_deep_str(self, depth: int = 0) -> str:
        """
        Gets a string representation of the folder and all of its subfolders.
        
        Parameters
        ----------
        depth : int, optional
            The depth of the folder. Defaults to 0.
        
        Returns
        -------
        str
            The string representation of the folder and all of its subfolders.
        """
        # set the string representation of the folder
        folder_str: str = f"{'  ' * depth}{self.name}\n"
        
        # get the string representation of the subfolders
        for subfolder in self.subfolders:
            folder_str += subfolder.get_deep_str(depth + 1)
        
        return folder_str

class DataHandler:
    """
    Class for handling data folders for the project. This class is meant to be used as a singleton.
    This is not meant to be manually initialized. Use the get_data_handler function instead.
    """
    
    # setup the paths
    relative_data_path: str = DEFAULT_RELATIVE_DATA_PATH
    absolute_data_path: str = path.abspath(relative_data_path)
    
    def __init__(self) -> None:
        """
        Initializes the data handler.
        """
        global main_data_handler
        main_data_handler = self

        # create the data folder
        self.create_data_folder()

        # create the default folders
        self.default_folders: Dict[str, Folder] = self.create_default_folders()

    def create_data_folder(self) -> None:
        """
        Creates the data folder for the project.
        
        Returns
        -------
        Folder
            The data folder for the project.
        """
        # make sure the data folder exists
        makedirs(self.absolute_data_path, exist_ok=True)
        
        # Create the main data folder object
        self.data_folder: Folder = Folder(self.absolute_data_path)
        
        return self.data_folder
    
    def create_default_folders(self) -> Dict[str, Folder]: 
        """
        Creates the default folders for the project.
        
        Parameters
        ----------
        data_handler : DataHandler
            The data handler for the project.
        """
        # create all the default folders and return them 
        return {
            folder_name: self.create_folder(folder_name, can_exist=True)
            for folder_name in DEFAULT_FOLDERS
        }
        
    def create_folder(self, folder_name: str, parent_folder: Folder = None, can_exist: bool = False) -> Folder:
        """
        Creates a folder in the project.
        
        Parameters
        ----------
        folder_name : str
            The name of the folder to create.
        parent_folder : Folder, optional
            The parent folder of the folder to create. Defaults to the data folder.
        can_exist : bool, optional
            Whether or not the folder can already exist. Defaults to False.
        """
        # make sure we have a parent folder
        if not parent_folder:
            parent_folder = self.data_folder

        # get the path of the new folder
        new_folder_path: str = path.join(parent_folder.path, folder_name)

        # check if the folder already exists
        if path.isdir(new_folder_path) and not can_exist:
            raise ValueError(f"Folder '{new_folder_path}' already exists.")

        # create the new folder
        makedirs(new_folder_path, exist_ok=can_exist)
        return Folder(folder_path=new_folder_path)

    def search_for_folder(self, folder_name: str, required_parent_name: str = None):
        """
        Searches for a folder in the project.
        
        Parameters
        ----------
        folder_name : str
            The name of the folder to search for.
        required_parent_name : str, optional
            The name of the parent folder of the folder to search for. Defaults to None.
        """
        # get the list of folders to search through
        folders_to_search: list[Folder] = [self.data_folder]

        # search through the folders
        while folders_to_search:
            # get the current folder
            current_folder: Folder = folders_to_search.pop()

            # check if the current folder is the folder we are looking for
            if current_folder.name == folder_name and (
                                required_parent_name
                                and current_folder.parent_folder_name == required_parent_name
                                or not required_parent_name
                            ):
                return current_folder
            # add the subfolders to the folders to search
            folders_to_search.extend(current_folder.subfolders)

        return None

def get_data_handler() -> DataHandler:
    """
    Gets the main data handler for the project.
    
    Returns
    -------
    DataHandler
        The main data handler for the project.
    """    
    return main_data_handler or DataHandler()

main_data_handler = DataHandler()