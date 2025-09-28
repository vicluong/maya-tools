"""Creates a UI for creating multiple windows within a wall

Allows for the user to specify an amount of windows to create along the
width and height of a wall, given that the user is currently selecting the
edge borders of the window and wall and that there is an empty space between
them.

MultipleWindowsDialog is the class to utilise in order to create the UI.
"""
try:
    from PySide6 import QtCore
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance
except:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance

import sys
from functools import partial

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from . import create_multiple_windows_helpers as cmwh


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class MultipleWindowsDialog(QtWidgets.QDialog):
    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = MultipleWindowsDialog()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(MultipleWindowsDialog, self).__init__(parent)

        self.setWindowTitle("Create Multiple Windows")
        
        size = maya_main_window().screen().size()
        screen_w = size.width()
        self.resize(int(screen_w * 0.15), int(screen_w * 0.06))

        self.input_width = int(screen_w * 0.017)
        
        # On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        """Create all widgets for the UI"""
        # Number of windows heightwise input/slider
        height_widgets = self.create_input_slider_widgets()
        self.height_input = height_widgets[0]
        self.height_slider = height_widgets[1]

        # Number of windows widthwise input/slider
        width_widgets = self.create_input_slider_widgets()
        self.width_input = width_widgets[0]
        self.width_slider = width_widgets[1]

        self.bridge_all_checkbox = QtWidgets.QCheckBox()
        self.bridge_all_checkbox.setChecked(True)

        self.create_windows_btn = QtWidgets.QPushButton("Create Windows")
        self.apply_btn = QtWidgets.QPushButton("Apply")
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_input_slider_widgets(self) -> tuple[QtWidgets.QDoubleSpinBox, 
                                                   QtWidgets.QSlider]:
        """Create a pair of widgets that are a DoubleSpinBox and a Slider

        Returns:
            Tuple of QDoubleSpinBox and QSlider
        """
        input = QtWidgets.QSpinBox()
        input.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        input.setFixedWidth(self.input_width)
        input.setSingleStep(1)
        input.setMinimum(1)
        input.setMaximum(15)
        input.setValue(3)
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(15)
        slider.setValue(3)

        return (input, slider)

    def create_layout(self):
        """Create all layouts and add widgets to them"""
        height_layout = QtWidgets.QHBoxLayout()
        height_layout.addWidget(self.height_input)
        height_layout.addWidget(self.height_slider)

        width_layout = QtWidgets.QHBoxLayout()
        width_layout.addWidget(self.width_input)
        width_layout.addWidget(self.width_slider)

        bridge_all_layout = QtWidgets.QHBoxLayout()
        bridge_all_layout.addWidget(self.bridge_all_checkbox)

        form_num_windows_layout = QtWidgets.QFormLayout()
        form_num_windows_layout.addRow("Height amount: ", height_layout)
        form_num_windows_layout.addRow("Width amount: ", width_layout)
        form_num_windows_layout.addRow("Connect everything: ", bridge_all_layout)

        button_grp = QtWidgets.QHBoxLayout()
        button_grp.addWidget(self.create_windows_btn)
        button_grp.addWidget(self.apply_btn)
        button_grp.addWidget(self.close_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_num_windows_layout)

        main_layout.addStretch()
        main_layout.addLayout(button_grp)

    def create_connections(self):
        """Create all connections for the UI"""
        self.height_slider.valueChanged.connect(
            partial(self.change_input, self.height_input)
        )
        self.height_input.valueChanged.connect(
            partial(self.change_slider, self.height_slider)
        )
        self.width_slider.valueChanged.connect(
            partial(self.change_input, self.width_input)
        )
        self.width_input.valueChanged.connect(
            partial(self.change_slider, self.width_slider)
        )

        self.create_windows_btn.clicked.connect(self.create_windows)
        self.create_windows_btn.clicked.connect(self.hide)
        self.apply_btn.clicked.connect(self.create_windows)
        self.close_btn.clicked.connect(self.hide)

    def change_input(self, input, value):
        """When the slider changes, change the value of its input counterpart"""
        input.setValue(value)

    def change_slider(self, slider, value):
        """When the input changes, change the value of its slider counterpart"""
        slider.setValue(value)

    def create_windows(self):
        """Create multiple windows from the UI values"""
        height = self.height_input.value()
        width = self.width_input.value()
        bridge_all = self.bridge_all_checkbox.isChecked()

        cmds.undoInfo(openChunk=True)
        try:
            cmwh.create_multiple_windows(height, width, bridge_all)
        finally:
            cmds.undoInfo(closeChunk=True)
