## FileDialogs.py
'''
This file contains a set of file dialog widgets for file paths for opening or 
saving.
Available widgets:
    SaveFileButton
    SelectFileButton
    SelectFilesButton
example:
Both SaveFileButton.file and SelectFileButton.file both are a string

    f = SaveFileButton()
    display(f)

    theFilePathSpecified = f.file

SelectFilesButton returns a list of file paths (strings) 
    f = SelectFilesButton()
    display(f)

    listSelectedFiles = f.files

Last modified: March 2018
Author: Vanessa Newey
Code adapted from https://gist.github.com/draperjames/90403fd013e332e4a14070aab3e3e7b0
'''

import os
import traitlets
from IPython.display import display
from ipywidgets import widgets
from tkinter import Tk, filedialog
'''
Code adapted from https://gist.github.com/draperjames/90403fd013e332e4a14070aab3e3e7b0
'''
class SaveFileButton(widgets.Button):
    """A file widget that leverages tkinter.filedialog."""

    def __init__(self, *args, **kwargs):
        """Initialize the SelectFilesButton class."""
        super(SaveFileButton, self).__init__(*args, **kwargs)
        # Add the selected_files trait
        self.add_traits(file=traitlets.traitlets.Unicode())
        # Create the button.
        self.file=""
        self.description = "Save File As"
        self.icon = "square-o"
        self.style.button_color = "orange"
        # Set on click behavior.
        self.on_click(self.select_file)

    @staticmethod
    def select_file(b):
        """Generate instance of tkinter.filedialog.

        Parameters
        ----------
        b : obj:
            An instance of ipywidgets.widgets.Button
        """
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected fileswill be set to b.value
        result = filedialog.asksaveasfilename()
        if len(result)>0:
            b.file=result
            b.description = "File Name Specified"
            b.icon = "check-square-o"
            b.style.button_color = "lightgreen"

class SelectFileButton(widgets.Button):
    """A file widget that leverages tkinter.filedialog."""

    def __init__(self, *args, **kwargs):
        """Initialize the SelectFileButton class."""
        super(SelectFileButton, self).__init__(*args, **kwargs)
        # Add the selected_files trait
        self.add_traits(files=traitlets.traitlets.Unicode())
        # Create the button.
        self.file=""
        self.description = "Select File"
        self.icon = "square-o"
        self.style.button_color = "orange"
        # Set on click behavior.
        self.on_click(self.select_file)

    @staticmethod
    def select_file(b):
        """Generate instance of tkinter.filedialog.

        Parameters
        ----------
        b : obj:
            An instance of ipywidgets.widgets.Button
        """
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected fileswill be set to b.value
        result = filedialog.askopenfilename(multiple=False)
        if len(result)>0:
            b.file = result
            b.description = "File Selected"
            b.icon = "check-square-o"
            b.style.button_color = "lightgreen"

class SelectFilesButton(widgets.Button):
    """A file widget that leverages tkinter.filedialog."""

    def __init__(self, *args, **kwargs):
        """Initialize the SelectFilesButton class. for selecting multiple files"""
        super(SelectFilesButton, self).__init__(*args, **kwargs)
        # Add the selected_files trait
        self.add_traits(files=traitlets.traitlets.List())
        # Create the button.
        self.description = "Select Files"
        self.icon = "square-o"
        self.style.button_color = "orange"
        # Set on click behavior.
        self.on_click(self.select_files)

    @staticmethod
    def select_files(b):
        """Generate instance of tkinter.filedialog.

        Parameters
        ----------
        b : obj:
            An instance of ipywidgets.widgets.Button
        """
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected fileswill be set to b.value
        b.files = [filedialog.askopenfilename(multiple=True)]
        if len(b.files)>0:
            if len(b.files[0])>0:
                b.description = "Files Selected"
                b.icon = "check-square-o"
                b.style.button_color = "lightgreen"



