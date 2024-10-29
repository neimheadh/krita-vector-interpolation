from krita import *
from PyQt5.QtWidgets import QWidget, QAction, QMessageBox

from .Svg import Svg
from .Ui import ErrorDialog, InterpolationDialog

class VectorInterpolation(Extension):
    messages = {
        'fr_FR': {
            'Generate shape interpolation': 'Générer les formes vectorielles interpolées',
            'created interpolation': 'interpolation créé',
            'created interpolations': 'interpolations créés',
            'Please select two vector shapes.': 'Veuillez sélectionner exactement 2 formes vectrorielles.',
            'Current layer is not a vector layer.': 'Le calque selectionné n\'est pas un calque vectoriel.',
            'Cannot find krita current document.': 'Impossible de charger le document courant.',
            'Cannot interpolate a different transform operation': 'Impossible d\'interpoler 2 opération "transform" différentes.',
            'Interpolation can only manage a maximum of one transform' : 'L\'interpolation ne gère qu\'un maximum d\'une opération "transform".',
            'Node not compatible with node for interpolation': 'Formes incompatibles pour l\'interpolation.',
        }
    }


    """Vector interpolation extension"""
    def __init__(self, parent):
        """Initialize extension"""
        super().__init__(parent)

    # called after setup(self)
    def createActions(self, window):
        """Create extension actions"""
        action = window.createAction("vector_interpolation.interpolate", self.trans('Generate shape interpolation'))
        action.triggered.connect(self.vector_interpolation)
        pass

    # Krita.instance() exists, so do any setup work
    def setup(self):
        """Setup extension"""
        pass

    def trans(self, msg):
        locale = QLocale().name()

        try:
            messages = self.messages[locale]
            return messages[msg]
        except KeyError:
            return msg

    def vector_interpolation(self):
        # Get Krita instance and document
        app = Krita.instance()
        doc = app.activeDocument()

        # Check the document contains a vector layer
        try :
            if doc:
                layer = doc.activeNode()

                if layer.type() == "vectorlayer":
                    # Get the Svg object for the layer
                    svg = Svg(layer.toSvg())

                    # Get selected shapes
                    # We add one to the result index as layer.toSvg() return a <deps /> node not present in layer.shapes() 
                    selected_shapes = [[s + 1, shape] for s, shape in enumerate(layer.shapes()) if shape.isSelected()]

                    # Check 2 shapes are selected
                    if len(selected_shapes) == 2:
                        dialog = InterpolationDialog()
                        if dialog.exec_():
                            steps = dialog.get_steps()
                            print(f"Interpolation steps: {steps}")
                            # Interpolate paths
                            interpolated = svg.interpolate(selected_shapes[0][0], selected_shapes[1][0], steps)

                            # Add & select generated svg into layer
                            shapes = layer.addShapesFromSvg(interpolated.toString())
                            selected_shapes[0][1].deselect()
                            selected_shapes[1][1].deselect()
                            for shape in shapes:
                                shape.select()

                            print(f"{len(shapes)} {self.trans('interpolation created' if len(shapes) < 2 else 'interpolations created')}")
                    else:
                        ErrorDialog("Please select two vector shapes.").exec_()
                else:
                    ErrorDialog("Current layer is not a vector layer.").exec_()
            else:
                ErrorDialog("Cannot find krita current document.").exec_()
        except RuntimeError:
            ErrorDialog("An error occured").exec_()