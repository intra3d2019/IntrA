import sys
import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import scipy.spatial as ss
import numpy as np
import time
import copy
import _thread
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import *


INPUT_MODEL = None
PICKED_POINT_INDEX = []
PICKED_POINT_ACTOR = []
APART_POINT_INDEX = []
UPDATE = False

KDTREE = None
POINTS = []

DISTANCE_LIMITATION = 10

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

COLORS = vtk.vtkUnsignedCharArray()
COLORS.SetNumberOfComponents(3)
COLORS.SetName('colors')

PROPAGATION = None


class VTKWidget:

    def __init__(self, filename, propagation):
        global INPUT_MODEL, PICKED_POINT_INDEX, POINTS, KDTREE, PROPAGATION

        PROPAGATION = propagation

        self.vtkWidget = QVTKRenderWindowInteractor()

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)

        iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        if filename is not None:
            INPUT_MODEL = vtk.vtkOBJReader()
            INPUT_MODEL.SetFileName(filename)
            INPUT_MODEL.Update()

            # coloring
            for i in range(INPUT_MODEL.GetOutput().GetNumberOfPoints()):
                COLORS.InsertNextTypedTuple(RED)

            INPUT_MODEL.GetOutput().GetPointData().SetScalars(COLORS)
            INPUT_MODEL.GetOutput().Modified()

            # get points
            p = [0.0, 0.0, 0.0]
            for i in range(INPUT_MODEL.GetOutput().GetNumberOfPoints()):
                INPUT_MODEL.GetOutput().GetPoint(i, p)
                POINTS.append(tuple(p))

            KDTREE = ss.KDTree(POINTS)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(INPUT_MODEL.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            self.ren.AddActor(actor)

            def rendering_apart(obj, event):
                global UPDATE

                # flatten points
                apart_region = []
                for i in APART_POINT_INDEX:
                    for j in i:
                        apart_region.append(j)

                if UPDATE is True:
                    for i in apart_region:
                        COLORS.SetTypedTuple(i, GREEN)

                    INPUT_MODEL.GetOutput().GetPointData().SetScalars(COLORS)
                    INPUT_MODEL.GetOutput().Modified()

                    UPDATE = False

            self.ren.AddObserver('StartEvent', rendering_apart)

            style = MouseInteractorPickingActor()
            style.SetDefaultRenderer(self.ren)
            iren.SetInteractorStyle(style)

        iren.Initialize()
        iren.Start()

    def undo(self):
        print('d')


class MouseInteractorPickingActor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)

    def picking(self):
        self.GetInteractor().GetPicker().Pick(self.GetInteractor().GetEventPosition()[0],
                                              self.GetInteractor().GetEventPosition()[1],
                                              0,
                                              self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer())

        distance, index = KDTREE.query(self.GetInteractor().GetPicker().GetPickPosition())

        if distance > 0.5:
            return None
        else:
            return index

    def leftButtonPressEvent(self, obj, event):
        global POINTS, PICKED_POINT_INDEX, PICKED_POINT_ACTOR

        index = self.picking()

        if index is not None:
            PICKED_POINT_INDEX.append(index)
            actor = addSphere(POINTS[index], 0.2, BLUE)
            PICKED_POINT_ACTOR.append(actor)

            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(actor)

            APART_POINT_INDEX.append([index])
            PROPAGATION.start()

        self.OnLeftButtonDown()
        return


class Propagation(QThread):

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self) -> None:
        global APART_POINT_INDEX, UPDATE

        center_point = POINTS[PICKED_POINT_INDEX[-1]]
        dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
        dijkstra.SetInputData(INPUT_MODEL.GetOutput())

        # propagation
        for sp in APART_POINT_INDEX[-1]:
            nn_index = []

            cellidlist = vtk.vtkIdList()
            INPUT_MODEL.GetOutput().GetPointCells(sp, cellidlist)
            for i in range(cellidlist.GetNumberOfIds()):
                cell = INPUT_MODEL.GetOutput().GetCell(cellidlist.GetId(i))
                for e in range(cell.GetNumberOfEdges()):
                    edge = cell.GetEdge(e)
                    pointidlist = edge.GetPointIds()
                    if pointidlist.GetId(0) != sp and pointidlist.GetId(1) != sp:
                        nn_index.append(pointidlist.GetId(0))
                        nn_index.append(pointidlist.GetId(1))
                        break

            nn_index = {}.fromkeys(nn_index).keys()

            for p in nn_index:
                dijkstra.SetStartVertex(PICKED_POINT_INDEX[-1])
                dijkstra.SetEndVertex(p)
                dijkstra.Update()

                path_distance = 0.0

                id_list = dijkstra.GetIdList()
                for i in range(id_list.GetNumberOfIds()-1):
                    p0 = POINTS[id_list.GetId(i)]
                    p1 = POINTS[id_list.GetId(i+1)]
                    path_distance += math.sqrt(((p0[0] - p1[0]) ** 2) + ((p0[1] - p1[1]) ** 2) + ((p0[2] - p1[2]) ** 2))

                if path_distance > DISTANCE_LIMITATION:
                    continue

                if_pushback = True

                for ep in APART_POINT_INDEX[-1]:
                    if p == ep:
                        if_pushback = False
                        break

                if if_pushback is True:
                    APART_POINT_INDEX[-1].append(p)
                    print('append', len(APART_POINT_INDEX[-1]))

        UPDATE = True
        print('segmentation finished!')


def addSphere(point, radius, color):
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetCenter(point)
    sphereSource.SetRadius(radius)

    sphereMapper = vtk.vtkPolyDataMapper()
    sphereMapper.SetInputConnection(sphereSource.GetOutputPort())

    sphereActor = vtk.vtkActor()
    sphereActor.SetMapper(sphereMapper)
    sphereActor.GetProperty().SetColor(color)

    return sphereActor


def clear_data():
    global ENCLOSED, PICKED_POINT_INDEX, PICKED_PATH_ACTOR, PICKED_POINT_ACTOR, APART_POINT_INDEX, PATH_POINT_INDEX

    ENCLOSED = True

    PICKED_POINT_INDEX.clear()
    APART_POINT_INDEX.clear()
    PATH_POINT_INDEX.clear()

    PICKED_PATH_ACTOR.clear()
    PICKED_POINT_ACTOR.clear()

    if INPUT_MODEL is not None:
        for i in range(INPUT_MODEL.GetOutput().GetNumberOfPoints()):
            COLORS.SetTypedTuple(i, RED)


def output_data():
    global INPUT_MODEL, POINTS, PATH_POINT_INDEX, APART_POINT_INDEX

    ann_faces = []
    non_faces = []

    for i in range(INPUT_MODEL.GetOutput().GetNumberOfCells()):
        id_list = vtk.vtkIdList()
        INPUT_MODEL.GetOutput().GetCellPoints(i, id_list)

        is_ann = False

        # todo
        for p in APART_POINT_INDEX:
            if id_list.GetId(0) == p or id_list.GetId(1) == p or id_list.GetId(2) == p:
                is_ann = True
                break

        if is_ann is True:
            ann_faces.append((id_list.GetId(0) + 1, id_list.GetId(1) + 1, id_list.GetId(2) + 1))
        else:
            non_faces.append((id_list.GetId(0) + 1, id_list.GetId(1) + 1, id_list.GetId(2) + 1))

    return POINTS, ann_faces, non_faces


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.set_window()

        self.propagation = Propagation()

        self.input_filename = None
        # self.input_filename = 'input_file.obj'

        self.tools = self.init_tools()
        self.viewer = VTKWidget(self.input_filename, self.propagation)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.tools)
        self.main_layout.addWidget(self.viewer.vtkWidget)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.main_layout)

        self.show()

    def set_window(self):
        self.setWindowTitle('Annotation')
        self.resize(1000, 800)
        self.move(int((QDesktopWidget().width() - self.width()) / 2),
                  int((QDesktopWidget().height() - self.height()) / 2))

    def init_tools(self):
        open_button = QPushButton('Open')
        open_button.clicked.connect(self.open_file)

        save_button = QPushButton('Save as One')
        # save_button.clicked.connect(self.save_file)

        tools = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(open_button)
        layout.addWidget(save_button)
        tools.setLayout(layout)

        return tools

    def open_file(self):
        # viewer.clear_data()

        input_filename = QFileDialog.getOpenFileName(self)[0]
        if input_filename != '':
            self.input_filename = input_filename

            self.main_layout.removeWidget(self.viewer.vtkWidget)
            self.viewer = viewer.VTKWidget(input_filename, self.propagation)
            self.main_layout.addWidget(self.viewer.vtkWidget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec())
