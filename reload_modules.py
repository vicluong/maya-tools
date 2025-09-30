"""Reload any modules found within a specified directory

To ensure that Maya is utilising the latest version of a module rather than its
cached version, the main function of this file finds a specified directory,
which is the location of this file be default, and reload it.

reload_modules is the main function to use.
"""
import sys
import os.path
import inspect


def reload_modules(given_dir: str = "") -> None:
    """Reload any modules found within a specified directory.

    Args:
        given_dir: The directory containing modules to reload. 
            Defaults to an empty string.
    """
    reload_directory = get_directory_to_reload(given_dir)
    print(f"Directory to reload: {reload_directory}")

    delete_modules(reload_directory)

    print("Reload complete!")


def get_directory_to_reload(given_dir) -> str:
    """Get the directory that needs to be reloaded

    Either tries to reload a given directory or, if nothing is provided, 
    reloads the script's current directory

    Args:
        given_dir: Directory given to reload

    Raises:
        NotADirectoryError: If unable to retrive the script's directory
        NotADirectoryError: If the given_dir is not a directory

    Returns:
        The path of the directory to be reloaded
    """
    if not given_dir:
        script_path = inspect.getfile(inspect.currentframe()) # type: ignore
        script_dir = os.path.dirname(os.path.abspath(script_path))
        if not script_dir:
            raise NotADirectoryError("Error retrieving directory")
        else:
            reload_directory = script_dir
    elif os.path.isdir(given_dir):
        reload_directory = given_dir
    else:
        raise NotADirectoryError("Select a directory")

    return os.path.normcase(reload_directory)


def delete_modules(reload_directory: str) -> None:
    """Delete all modules from the reload_directory from Maya's module cache

    Args:
        reload_directory: Directory that all modules need to be deleted/reloaded
    """
    
    to_delete = []
    for key, module in sys.modules.items():
        module_path = getattr(module, "__file__", None)

        if module_path:
            module_dir = os.path.normcase(os.path.dirname(module_path))
            if module_dir == reload_directory:
                to_delete.append(key)

    for del_module in to_delete:
        print(f"Module reloaded: {del_module}")
        del (sys.modules[del_module])
