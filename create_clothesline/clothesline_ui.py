"""Creates a UI for creating a clothesline given a selection of images

Provides the ability to select a series of images to then make as materials
for texturing polyPlanes to appear as if a clothesline has been made. The user
can specify how many clothes should be places, the order of which they are
placed and the length of each object.

ClotheslineDialog is the class to utilise in order to create the UI.
"""
try:
    from PySide6 import QtCore
    from PySide6 import QtGui
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance
except:
    from PySide2 import QtCore
    from PySide2 import QtGui
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance

import os
import sys
from functools import partial

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds

from . import clothesline_helpers as clh


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class ClotheslineDialog(QtWidgets.QDialog):
    FILE_FILTERS = "All Image Files (*.jpg *.jpeg *.png *.gif *.bmp);;All Files (*.*)"
    selected_filter = "All Image Files (*.jpg *.jpeg *.png *.gif *.bmp)"

    dlg_instance = None
    
    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = ClotheslineDialog()
            
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        """Initialise ClotheslineDialog"""
        super(ClotheslineDialog, self).__init__(parent)

        self.setWindowTitle("Clothesline Creation")

        size = maya_main_window().screen().size()
        screen_w, screen_h = size.width(), size.height()
        self.resize(int(screen_w * 0.19), int(screen_h * 0.5))

        self.thumbnail_height = int(screen_w * 0.044)
        self.input_width = int(screen_w * 0.035)
        self.checkbox_margin = int(screen_w * 0.004)
        
        # On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)

        self.mat_list = {}
        self.obj_list = []

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        """Create all widgets for the UI"""
        self.filepath_le = QtWidgets.QLineEdit()
        self.filepath_le.setReadOnly(True)
        
        self.select_file_path_btn = QtWidgets.QPushButton()
        self.select_file_path_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.add_btn = QtWidgets.QPushButton("Add")

        length_widgets = self.create_input_slider_widgets(5, 1, 99)
        self.length_input = length_widgets[0]
        self.length_slider = length_widgets[1]

        wire_rad_widgets = self.create_input_slider_widgets(0.02, 0.0001, 1)
        self.wire_rad_input = wire_rad_widgets[0]
        self.wire_rad_slider = wire_rad_widgets[1]

        curvature_widgets = self.create_input_slider_widgets(5, -180, 180)
        self.curvature_input = curvature_widgets[0]
        self.curvature_slider = curvature_widgets[1]

        self.randomise_checkbox = QtWidgets.QCheckBox()

        self.mat_table = QtWidgets.QTableWidget(0, 4)
        self.mat_table.setHorizontalHeaderLabels(["Thumbnail", "Material Name", "Add", "Remove"])
        self.mat_table.resizeColumnsToContents()
        self.mat_table.setColumnWidth(0, self.thumbnail_height)
        self.mat_table.setColumnWidth(1, self.thumbnail_height * 1.75)
        self.mat_table.verticalHeader().setDefaultSectionSize(self.thumbnail_height)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)

        self.obj_table = QtWidgets.QTableWidget(0, 4)
        self.obj_table.setHorizontalHeaderLabels(["Material Name", "Amount", "Length", "Remove"])
        self.obj_table.resizeColumnsToContents()
        
        self.create_btn = QtWidgets.QPushButton("Create Clothesline")
        self.apply_btn = QtWidgets.QPushButton("Apply")
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_input_slider_widgets(self, value: float, min: float, 
                                    max: float) -> tuple[QtWidgets.QDoubleSpinBox, 
                                                         QtWidgets.QSlider]:
        """Create a pair of widgets that are a DoubleSpinBox and a Slider

        Args:
            value: The default value upon creation
            min: The minimum value of the inputs
            max: The maximum value of the inputs

        Returns:
            Tuple of QDoubleSpinBox and QSlider
        """
        input = QtWidgets.QDoubleSpinBox()
        input.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        input.setFixedWidth(self.input_width)
        input.adjustSize()
        input.setDecimals(4)
        input.setMinimum(min)
        input.setMaximum(max)
        input.setValue(value)
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(min * 10000)
        slider.setMaximum(max * 10000)
        slider.setValue(value * 10000)

        return (input, slider)

    def create_layout(self):
        """Create all layouts and add widgets to them"""
        file_path_layout = QtWidgets.QHBoxLayout()
        file_path_layout.addWidget(self.filepath_le)
        file_path_layout.addWidget(self.select_file_path_btn)
        file_path_layout.addWidget(self.add_btn)

        length_input_layout = QtWidgets.QHBoxLayout()
        length_input_layout.addWidget(self.length_input)
        length_input_layout.addWidget(self.length_slider)

        wire_rad_layout = QtWidgets.QHBoxLayout()
        wire_rad_layout.addWidget(self.wire_rad_input)
        wire_rad_layout.addWidget(self.wire_rad_slider)

        curvature_layout = QtWidgets.QHBoxLayout()
        curvature_layout.addWidget(self.curvature_input)
        curvature_layout.addWidget(self.curvature_slider)

        randomise_layout = QtWidgets.QHBoxLayout()
        randomise_layout.addWidget(self.randomise_checkbox)
        randomise_layout.setContentsMargins(self.checkbox_margin, self.checkbox_margin, 
                                            self.checkbox_margin, self.checkbox_margin)

        file_layout = QtWidgets.QFormLayout()
        file_layout.addRow("File Path:", file_path_layout)

        mat_form_layout = QtWidgets.QVBoxLayout()
        mat_form_layout.addWidget(self.mat_table)
        mat_grp = QtWidgets.QGroupBox("Materials")
        mat_grp.setLayout(mat_form_layout)

        objects_form_layout = QtWidgets.QVBoxLayout()
        objects_form_layout.addWidget(self.obj_table)
        objects_grp = QtWidgets.QGroupBox("Objects")
        objects_grp.setLayout(objects_form_layout)

        self.splitter.addWidget(mat_grp)
        self.splitter.addWidget(objects_grp)

        attribute_layout = QtWidgets.QFormLayout()
        attribute_layout.addRow("Length:", length_input_layout)
        attribute_layout.addRow("Wire Radius:", wire_rad_layout)
        attribute_layout.addRow("Curvature:", curvature_layout)
        attribute_layout.addRow("Randomise\nPlacement:", randomise_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.close_btn)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.splitter)
        main_layout.addLayout(attribute_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        """Create all connections for the UI"""
        self.select_file_path_btn.clicked.connect(self.show_file_select_dialog)
        
        self.add_btn.clicked.connect(self.add_material)

        self.length_slider.valueChanged.connect(
            partial(self.change_input, self.length_input)
        )
        self.length_input.valueChanged.connect(
            partial(self.change_slider, self.length_slider)
        )
        self.wire_rad_slider.valueChanged.connect(
            partial(self.change_input, self.wire_rad_input)
        )
        self.wire_rad_input.valueChanged.connect(
            partial(self.change_slider, self.wire_rad_slider)
        )
        self.curvature_slider.valueChanged.connect(
            partial(self.change_input, self.curvature_input)
        )
        self.curvature_input.valueChanged.connect(
            partial(self.change_slider, self.curvature_slider)
        )

        self.create_btn.clicked.connect(self.submit_clothesline_data)
        self.create_btn.clicked.connect(self.close)
        self.apply_btn.clicked.connect(self.submit_clothesline_data)
        self.close_btn.clicked.connect(self.close)

    def change_input(self, input, value):
        """When the slider changes, change the value of its input counterpart"""
        input.setValue(value / 10000)

    def change_slider(self, slider, value):
        """When the input changes, change the value of its slider counterpart"""
        slider.setValue(value * 10000)

    def show_file_select_dialog(self):
        """Create the dialog for file selection"""
        file_path = self.filepath_le.text()

        if not file_path:
            file_path = cmds.workspace(rootDirectory=True, q=True) + "/sourceimages"
            
        file_path, self.selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", file_path, self.FILE_FILTERS, self.selected_filter)
        if file_path:
            self.filepath_le.setText(file_path)

    def get_file(self):
        """Get the file path from the LineEdit"""
        file_path = self.filepath_le.text()
        
        if not file_path:
            om.MGlobal.displayWarning("Select a file.")
            return

        file_info = QtCore.QFileInfo(file_path)

        if not file_info.exists():
            om.MGlobal.displayWarning("Select a valid file.")
            return
        else:
            return file_path

    def add_material(self):
        """Add material to material table and data set"""
        file_path = self.get_file()

        if not file_path:
            return

        if file_path and file_path in self.mat_list:
            om.MGlobal.displayWarning("Item for file exists already.")
        elif file_path:
            file_name = os.path.basename(file_path)
            mat_name = os.path.splitext(file_name)[0]

            index = self.mat_table.rowCount()
            self.mat_table.setRowCount(index + 1)

            image = QtGui.QImage(file_path)
            pixmap = QtGui.QPixmap.fromImage(image)

            target_size = QtCore.QSize(self.thumbnail_height, self.thumbnail_height) 

            scaled_pixmap = pixmap.scaled(
                target_size,                     
                QtCore.Qt.KeepAspectRatio,    
            )

            thumbnail = QtWidgets.QLabel()
            thumbnail.setPixmap(scaled_pixmap)
            thumbnail.setAlignment(QtCore.Qt.AlignCenter)
            self.mat_table.setCellWidget(index, 0, thumbnail)

            mat_name_le = QtWidgets.QLineEdit()
            mat_name_le.setText(mat_name)
            mat_name_le.editingFinished.connect(
                partial(self.change_mat_name, file_path, mat_name_le)
            )
            self.mat_table.setCellWidget(index, 1, mat_name_le)

            add_button = QtWidgets.QPushButton()
            add_button.setIcon(QtGui.QIcon(":addClip.png"))
            self.mat_table.setCellWidget(index, 2, add_button)
            add_button.clicked.connect(
                partial(self.add_obj, file_path, mat_name_le)
            )

            remove_button = QtWidgets.QPushButton()
            remove_button.setIcon(QtGui.QIcon(":trash.png"))
            self.mat_table.setCellWidget(index, 3, remove_button)
            remove_button.clicked.connect(
                partial(self.remove_mat, file_path, mat_name, remove_button)
            )

            self.mat_list[file_path] = mat_name

    def change_mat_name(self, file_path: str, widget: QtWidgets.QLineEdit) -> None:
        """Change the name of the material

        Args:
            file_path: String of the texture's file path for the material
            widget: LineEdit of where the material's name is changing
            new_name: New name of the material
        """
        old_name = self.mat_list[file_path]
        new_name = widget.text()

        # If new_name is already one of the other materials' names, revert text
        if new_name in self.mat_list.values():
            widget.setText(old_name)
            om.MGlobal.displayWarning("Name for that material is already being used.")
            return

        self.mat_list[file_path] = new_name

        for row in range(self.obj_table.rowCount()):
            cellWidget = self.obj_table.cellWidget(row, 0)
            if cellWidget.text() == old_name:
                cellWidget.setText(new_name)
                self.obj_list[row]["mat_name"] = new_name
        
    def remove_mat(self, file_path: str, mat_name: str, 
                   widget: QtWidgets.QPushButton) -> None:
        """Remove material from material table, object table and datasets

        Args:
            file_path: String of the texture's file path for the material
            mat_name: Name of the material
            widget: PushButton on the same row of the material
        """
        mat_index = self.find_mat_index(widget, 3)

        del self.mat_list[file_path]
        self.mat_table.removeRow(mat_index)

        for row in reversed(range(self.obj_table.rowCount())):
            cellWidget = self.obj_table.cellWidget(row, 0)
            if cellWidget.text() == mat_name:
                self.obj_list.pop(row)
                self.obj_table.removeRow(row)

    def add_obj(self, file_path: str, mat_name_le: QtWidgets.QLineEdit) -> None:
        """Add object to object table and data set

        Args:
            file_path: String of the texture's file path for the material
            mat_name_le: QLineEdit containing material name 
        """
        if file_path:
            mat_name = mat_name_le.text()

            index = self.obj_table.rowCount()
            self.obj_table.setRowCount(index + 1)

            mat_name_le = QtWidgets.QLabel()
            mat_name_le.setText(mat_name)
            self.obj_table.setCellWidget(index, 0, mat_name_le)

            amount_input = self.create_cell_input()
            amount_input.valueChanged.connect(
                partial(self.change_amount, amount_input)
            )
            self.obj_table.setCellWidget(index, 1, amount_input)

            length_input = self.create_cell_float_input()
            length_input.valueChanged.connect(
                partial(self.change_length, length_input)
            )
            self.obj_table.setCellWidget(index, 2, length_input)

            remove_button = QtWidgets.QPushButton()
            remove_button.setIcon(QtGui.QIcon(":trash.png"))
            self.obj_table.setCellWidget(index, 3, remove_button)
            remove_button.clicked.connect(
                partial(self.remove_obj, remove_button)
            )

            self.obj_list.append({
                "file_path": file_path,
                "mat_name": mat_name, 
                "amount": 1, 
                "length": 1,
            })

    def create_cell_input(self) -> QtWidgets.QSpinBox:
        """Create SpinBox to set as a cell widget"""
        cell_input = QtWidgets.QSpinBox()
        cell_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        cell_input.setMinimum(1)
        cell_input.setMaximum(99)
        cell_input.setValue(1)
        cell_input.setAlignment(QtCore.Qt.AlignCenter)

        return cell_input

    def create_cell_float_input(self) -> QtWidgets.QDoubleSpinBox:
        """Create SpinBox to set as a cell widget"""
        cell_input = QtWidgets.QDoubleSpinBox()
        cell_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        cell_input.setDecimals(2)
        cell_input.setMinimum(0.1)
        cell_input.setMaximum(99)
        cell_input.setValue(1)
        cell_input.setAlignment(QtCore.Qt.AlignCenter)

        return cell_input

    def change_amount(self, widget: QtWidgets.QSpinBox, amount: int) -> None:
        """Change amount value for an object"""
        obj_index = self.find_obj_index(widget, 1)
        self.obj_list[obj_index]["amount"] = amount

    def change_length(self, widget: QtWidgets.QSpinBox, length: int) -> None:
        """Change length value for an object"""
        obj_index = self.find_obj_index(widget, 2)
        self.obj_list[obj_index]["length"] = length

    def remove_obj(self, widget: QtWidgets.QPushButton) -> None:
        """Remove object from table and data set"""
        obj_index = self.find_obj_index(widget, 3)

        self.obj_list.pop(obj_index)
        self.obj_table.removeRow(obj_index)

    def find_mat_index(self, widget: QtWidgets.QWidget, column: int) -> int:
        """Find the row index of a widget in the material table"""
        for row in range(self.mat_table.rowCount()):
            cellWidget = self.mat_table.cellWidget(row, column)
            if cellWidget == widget:
                return row
        raise RuntimeError("Widget not found in material table")

    def find_obj_index(self, widget: QtWidgets.QWidget, column: int) -> int:
        """Find the row index of a widget in the object table"""
        for row in range(self.obj_table.rowCount()):
            cellWidget = self.obj_table.cellWidget(row, column)
            if cellWidget == widget:
                return row
        raise RuntimeError("Object not found in material table")

    def submit_clothesline_data(self):
        """Create the clothesline"""
        length = self.length_input.value()
        wire_rad = self.wire_rad_input.value()
        curvature = self.curvature_input.value()
        randomise = self.randomise_checkbox.isChecked()

        cmds.undoInfo(openChunk=True)
        try:
            clh.create_clothesline(self.mat_list, self.obj_list, length, wire_rad, 
                        curvature, randomise)
        finally:
            cmds.undoInfo(closeChunk=True)
