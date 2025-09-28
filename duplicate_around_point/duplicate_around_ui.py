"""Creates a UI for cduplicating an object around a point

This UI allows for the duplication of an object around a point when selecting 
two vertices that are on the opposite ends of a mesh but along the same axis.
The amount of objects made can be specified in addition to if they should be 
connected or not. 

Furthermore, in order to know how to duplicate the object, options to specify 
the direction that the centre of the group should be and the axis that it 
should be rotated around are given.

DuplicateAroundDialog is the class to utilise in order to create the UI.
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

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from . import duplicate_around_helpers as dah


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class DuplicateAroundDialog(QtWidgets.QDialog):
    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = DuplicateAroundDialog()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(DuplicateAroundDialog, self).__init__(parent)

        self.setWindowTitle("Duplicate Around")

        size = maya_main_window().screen().size()
        screen_w = size.width()
        self.resize(int(screen_w * 0.14), int(screen_w * 0.1))

        self.INPUT_WIDTH = int(screen_w * 0.012)
        
        # On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        """Create all widgets for the UI"""
        # Number of sides input/slider
        self.sides_input = QtWidgets.QSpinBox()
        self.sides_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.sides_input.setFixedWidth(self.INPUT_WIDTH)
        self.sides_input.setSingleStep(0)
        self.sides_input.setMinimum(3)
        self.sides_input.setMaximum(99)
        self.sides_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sides_slider.setMinimum(3)
        self.sides_slider.setMaximum(99)

        # Axis to rotate around buttons
        self.axis_x_btn = QtWidgets.QRadioButton("X")
        self.axis_y_btn = QtWidgets.QRadioButton("Y")
        self.axis_z_btn = QtWidgets.QRadioButton("Z")
        
        self.axis_btn_grp = QtWidgets.QButtonGroup()
        self.axis_btn_grp.addButton(self.axis_x_btn)
        self.axis_btn_grp.addButton(self.axis_y_btn)
        self.axis_btn_grp.addButton(self.axis_z_btn)
        
        # Centre position buttons
        self.centre_x_btn = QtWidgets.QRadioButton("X")
        self.centre_y_btn = QtWidgets.QRadioButton("Y")
        self.centre_z_btn = QtWidgets.QRadioButton("Z")

        self.centre_btn_grp = QtWidgets.QButtonGroup()
        self.centre_btn_grp.addButton(self.centre_x_btn)
        self.centre_btn_grp.addButton(self.centre_y_btn)
        self.centre_btn_grp.addButton(self.centre_z_btn)
        
        self.axis_x_btn.setEnabled(False)
        self.axis_y_btn.setChecked(True)

        self.centre_x_btn.setChecked(True)
        self.centre_y_btn.setEnabled(False)

        # Centre position direction combo box
        self.centre_dir_combo_box = QtWidgets.QComboBox()
        self.centre_dir_combo_box.addItem("+")
        self.centre_dir_combo_box.addItem("-")

        self.merge_thres_checkbox = QtWidgets.QCheckBox()
        self.merge_thres_checkbox.setChecked(True)

        self.dup_around_btn = QtWidgets.QPushButton("Duplicate Around")
        self.apply_btn = QtWidgets.QPushButton("Apply")
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layout(self):
        """Create all layouts and add widgets to them"""
        num_of_sides_layout = QtWidgets.QHBoxLayout()
        num_of_sides_layout.addWidget(self.sides_input)
        num_of_sides_layout.addWidget(self.sides_slider)

        form_num_sides_layout = QtWidgets.QFormLayout()
        form_num_sides_layout.addRow("Number of Sides: ", num_of_sides_layout)

        axis_rot_layout = QtWidgets.QHBoxLayout()
        axis_rot_layout.addWidget(self.axis_x_btn)
        axis_rot_layout.addWidget(self.axis_y_btn)
        axis_rot_layout.addWidget(self.axis_z_btn)
        axis_rot_layout.addStretch()
        
        centre_pos_layout = QtWidgets.QHBoxLayout()
        centre_pos_layout.addWidget(self.centre_x_btn)
        centre_pos_layout.addWidget(self.centre_y_btn)
        centre_pos_layout.addWidget(self.centre_z_btn)
        centre_pos_layout.addStretch()
 
        centre_dir_layout = QtWidgets.QHBoxLayout()
        centre_dir_layout.addWidget(self.centre_dir_combo_box)

        merge_thres_layout = QtWidgets.QHBoxLayout()
        merge_thres_layout.addWidget(self.merge_thres_checkbox)

        centre_pos_form_layout = QtWidgets.QFormLayout()
        centre_pos_form_layout.addRow("Axis to Rotate Around: ", axis_rot_layout)
        centre_pos_form_layout.addRow("Centre Position: ", centre_pos_layout)
        centre_pos_form_layout.addRow("Centre Position Direction: ", centre_dir_layout)

        form_merge_thres_layout = QtWidgets.QFormLayout()
        form_merge_thres_layout.addRow("Connect and Merge: ", merge_thres_layout)

        centre_pos_grp = QtWidgets.QGroupBox("Centre Positioning")
        centre_pos_grp.setLayout(centre_pos_form_layout)

        button_grp = QtWidgets.QHBoxLayout()
        button_grp.addWidget(self.dup_around_btn)
        button_grp.addWidget(self.apply_btn)
        button_grp.addWidget(self.close_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_num_sides_layout)
        main_layout.addWidget(centre_pos_grp)
        main_layout.addLayout(form_merge_thres_layout)
        main_layout.addStretch()
        main_layout.addLayout(button_grp)

    def create_connections(self):
        """Create all connections for the UI"""
        self.sides_slider.valueChanged.connect(self.change_sides_input)
        self.sides_input.valueChanged.connect(self.change_sides_slider)

        self.axis_btn_grp.buttonToggled.connect(self.prevent_axis_button_overlap)
        self.centre_btn_grp.buttonToggled.connect(self.prevent_axis_button_overlap)

        self.apply_btn.clicked.connect(self.duplicate_around)
        self.dup_around_btn.clicked.connect(self.duplicate_around)
        self.dup_around_btn.clicked.connect(self.hide)
        self.close_btn.clicked.connect(self.hide)

    def change_sides_input(self):
        self.sides_input.setValue(self.sides_slider.value())

    def change_sides_slider(self):
        self.sides_slider.setValue(self.sides_input.value())

    def prevent_axis_button_overlap(self, button, checked):
        """Prevents buttons for the axis and centre pos groups overlapping

        To ensure that the axis of rotation and centre position never have
        the same axis, when an axis is selected in one group, it disables that
        axis for the other group.

        Args:
            button: Button being toggled
            checked: Checked state of the button being toggled
        """
        if button in self.axis_btn_grp.buttons():
            for centre_btn in self.centre_btn_grp.buttons():
                if centre_btn.text() == button.text():
                    centre_btn.setEnabled(not checked)
        elif button in self.centre_btn_grp.buttons():
            for axis_btn in self.axis_btn_grp.buttons():
                if axis_btn.text() == button.text():
                    axis_btn.setEnabled(not checked)

    def duplicate_around(self):
        """Duplicate mesh around a point a specified amount times"""
        amount = self.sides_input.value()
        axis_rot = self.axis_btn_grp.checkedButton().text().lower()
        centre_dir = self.centre_dir_combo_box.currentText()
        centre_axis = self.centre_btn_grp.checkedButton().text().lower()
        merged = self.merge_thres_checkbox.isChecked()

        cmds.undoInfo(openChunk=True)
        try:
            dah.duplicate_around_point(amount, axis_rot, 
                                    centre_dir + centre_axis, merged)
        finally:
            cmds.undoInfo(closeChunk=True)
