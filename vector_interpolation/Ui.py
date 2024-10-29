from PyQt5 import QtWidgets, uic
import os
import sys

class InterpolationDialog(QtWidgets.QDialog):
    def __init__(self):
        super(InterpolationDialog, self).__init__()
        
        # Load ui file
        uic.loadUi(os.path.dirname(os.path.realpath(__file__)) + '/../ui/InterpolationDialog.ui', self)
        
        # Set forcus on stepsSpinBox
        self.stepsSpinBox.setFocus()

        self.show()
    
    def get_steps(self):
        """Return the value of stepsSpinBox"""
        return self.stepsSpinBox.value()

class ErrorDialog(QtWidgets.QDialog):
    def __init__(self, msg):
        super(ErrorDialog, self).__init__()

        # Load ui file
        uic.loadUi(os.path.dirname(os.path.realpath(__file__)) + '/../ui/Error.ui', self)

        # Set error message
        self.message.setText(msg)

        self.show()