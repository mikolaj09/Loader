import queue
import threading
import pathlib
import json
import configparser
from arcade import Sprite
from typing import Callable, Any


THREAD = 1
QUEUE = 2


def queue_decorator(func: callable) -> callable:
    """Helper decorator which puts the returned values to the queue."""

    def wrapper(*args, **kwargs) -> queue.Queue:
        value_queue = kwargs['queue']
        kwargs.pop('queue')
        value_queue.put(func(*args, **kwargs))
        return value_queue

    return wrapper


class Loader:

    """Helper class used to load data from folders, JSON files, etc.
    It can also be used to save data to files."""

    def __init__(self):
        self.threads = []
        self.loaded_data = {}

    @property
    def is_finished(self) -> bool:
        """Checks if it has been finished."""

        for values in self.threads:
            if not self._is_finished_thread(values[THREAD].name):
                return False
        return True

    def _finish_loading(self) -> None:
        """Private method which assigns loaded data to self.loaded_data.
        Note: If the loading is not completed, a RuntimeError will be raised."""

        if self.is_finished:
            for values in self.threads:
                self.loaded_data[values[THREAD].name] = values[QUEUE].get()
        else:
            raise RuntimeError('Loading has not been finished yet')

    def get_loaded_data(self) -> dict[Any, ...] | None:
        """Returns loaded data.
        Note: If the loading is not completed, a RuntimeError will be raised."""

        self._finish_loading()
        return self.loaded_data

    def start_graphic_thread(self, folder: str, thread_name: str | None = None, scale: float = 1) -> None:
        """Starts a thread to load graphic data."""

        self._start_thread(Loader.load_folder_of_graphics, thread_name=thread_name if thread_name is not None else folder, folder=folder, scale=scale)

    def start_json_thread(self, file_name: str, thread_name: str | None = None) -> None:
        """Starts a thread to load JSON data."""

        self._start_thread(Loader.load_json_file, thread_name=thread_name if thread_name is not None else file_name, file_name=file_name)

    def start_ini_thread(self, file_name: str, thread_name: str | None = None) -> None:
        """Starts a thread to load ini data."""

        self._start_thread(Loader.load_ini_file, thread_name=thread_name if thread_name is not None else file_name, file_name=file_name)

    def _is_finished_thread(self, thread_nane: str) -> bool:
        """Private helper method which checks if queue is empty."""

        return not self._get_thread_queue(thread_nane).empty()

    def _start_thread(self, func: Callable, daemon=True, thread_name: str | None = None, *args, **kwargs) -> None:
        """Private general method which creates and starts a thread."""

        kwargs['queue'] = queue.Queue()
        new_thread = threading.Thread(target=queue_decorator(func), name=thread_name if thread_name is not None else f"Thread-{len(self.threads)}", daemon=daemon, args=args, kwargs=kwargs)
        new_thread.start()
        self.threads.append({THREAD: new_thread, QUEUE: kwargs['queue']})

    def _get_thread_queue(self, thread_name: str) -> queue.Queue:
        """Private method which returns a queue of values."""

        for values in self.threads:
            if values[THREAD].name == thread_name:
                return values[QUEUE]
        raise KeyError(f"There is no thread with name {thread_name}")

    @staticmethod
    def load_folder_of_graphics(folder: str, scale: float = 1) -> list:
        """Static method which loads graphics from folder without threading."""

        try:
            base = pathlib.Path(__file__).parent
        except NameError:
            base = pathlib.Path.cwd()

        graphics = base / folder
        sprites = []

        for image in graphics.iterdir():
            if not image.is_file():
                continue

            sprite = Sprite(path_or_texture=f'{folder}/{image.name}')
            sprite.multiply_scale(scale)
            sprites.append(sprite)

        return sprites

    @staticmethod
    def load_json_file(file_name: str) -> dict:
        """Static method which loads JSON file without threading."""

        with open(file_name, "r", encoding="utf-8") as file:
            data_file = json.load(file)

        data_dict = {}

        for name, data in data_file.items():
            data_dict[name] = data

        return data_dict

    @staticmethod
    def load_ini_file(file_name: str) -> dict:
        """Static method which loads ini file without threading."""

        config = configparser.ConfigParser()
        config.read(file_name)

        data_dict = {}

        for section in config.sections():
            section_dict = {}
            for key, value in config[section].items():
                section_dict[key] = value if not value.isnumeric() else int(value)

            data_dict[section] = section_dict

        return data_dict

    @staticmethod
    def save_json_file(data: dict, file_name: str) -> None:
        """Static method which saves JSON file."""

        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
