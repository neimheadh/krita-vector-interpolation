from krita import *
import sys
import os
import importlib

# Ajouter le chemin absolu vers le fichier Svg.py
sys.path.append("/home/neim/projects/krita-vector-interpolation/lib")  # Remplacer par le chemin absolu correct
import Svg  # Importer le fichier Svg.py
import Ui
importlib.reload(Svg)
importlib.reload(Ui)


# Récupérer l'instance de Krita et le document actif
app = Krita.instance()
doc = app.activeDocument()

# Vérifier si le document contient un calque vectoriel
if doc:
    layer = doc.activeNode()

    if layer.type() == "vectorlayer":
        # Récupérer l'objet Svg du layer
        svg = Svg.Svg(layer.toSvg())

        # Get selected shapes
        # We add one to the result index as layer.toSvg() return a <deps /> node not present in layer.shapes() 
        selected_shapes = [[s + 1, shape] for s, shape in enumerate(layer.shapes()) if shape.isSelected()]

        # Vérifier qu'on a exactement deux formes sélectionnées
        if len(selected_shapes) == 2:
            dialog = Ui.InterpolationDialog()
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

                print(f"{len(shapes)} chemins interpolés créés.")
        else:
            Ui.ErrorDialog("Sélectionnez exactement deux formes vectorielles.").exec_()
    else:
        Ui.ErrorDialog("Le calque actif n'est pas un calque vectoriel.").exec_()
else:
    Ui.ErrorDialog("Aucun document actif trouvé.").exec_()