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
ENCLOSED = True
UPDATE = False
PICKED_POINT_INDEX = []
PICKED_POINT_ACTOR = []
APART_POINT_INDEX = []
PATH_POINT_INDEX = []
PICKED_PATH_ACTOR = []

KDTREE = None
POINTS = []

RED = (204, 10, 10)
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
        self.ren.SetBackground(1, 1, 1)
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

                if UPDATE is True:
                    for i in APART_POINT_INDEX:
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
        global PICKED_POINT_INDEX, PICKED_POINT_ACTOR, PICKED_PATH_ACTOR, PATH_POINT_INDEX

        if ENCLOSED is False:
            if len(PICKED_POINT_INDEX[-1]) > 0:
                PICKED_POINT_INDEX[-1].pop(-1)
                self.vtkWidget.GetRenderWindow().GetRenderers().GetFirstRenderer().RemoveActor(PICKED_POINT_ACTOR[-1])
                PICKED_POINT_ACTOR.pop(-1)

            if len(PATH_POINT_INDEX) > 0:
                PATH_POINT_INDEX.pop(-1)
                self.vtkWidget.GetRenderWindow().GetRenderers().GetFirstRenderer().RemoveActor(PICKED_PATH_ACTOR[-1])
                PICKED_PATH_ACTOR.pop(-1)

    def add(self):
        global ENCLOSED, PICKED_POINT_INDEX

        ENCLOSED = False
        PICKED_POINT_INDEX.append([])

    def init_data(self):
        global INPUT_MODEL, ENCLOSED, UPDATE, PICKED_POINT_INDEX, PICKED_POINT_ACTOR, APART_POINT_INDEX, PATH_POINT_INDEX
        global PICKED_PATH_ACTOR, KDTREE, POINTS, COLORS, PROPAGATION

        INPUT_MODEL = None
        ENCLOSED = True
        UPDATE = False
        PICKED_POINT_INDEX.clear()
        PICKED_POINT_ACTOR.clear()
        APART_POINT_INDEX.clear()
        PATH_POINT_INDEX.clear()
        PICKED_PATH_ACTOR.clear()

        KDTREE = None
        POINTS.clear()

        COLORS = vtk.vtkUnsignedCharArray()
        COLORS.SetNumberOfComponents(3)
        COLORS.SetName('colors')

        PROPAGATION = None


class MouseInteractorPickingActor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.AddObserver("MiddleButtonPressEvent", self.middleButtonPressEvent)
        self.AddObserver('MouseMoveEvent', self.mouseMoveEvent)

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
        global PICKED_POINT_INDEX, POINTS, ENCLOSED

        index = self.picking()

        if index is not None and ENCLOSED is False:
            if len(PICKED_POINT_INDEX[-1]) > 0 and index == PICKED_POINT_INDEX[-1][0]:
                ENCLOSED = True

            PICKED_POINT_INDEX[-1].append(index)
            actor = addSphere(POINTS[index], 0.5, BLUE)
            PICKED_POINT_ACTOR.append(actor)

            PICKED_PATH_ACTOR.append('')
            PATH_POINT_INDEX.append('')

            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(actor)

        self.OnLeftButtonDown()
        return

    def middleButtonPressEvent(self, obj, event):
        global PICKED_POINT_INDEX, ENCLOSED, APART_POINT_INDEX

        self.GetInteractor().GetPicker().Pick(self.GetInteractor().GetEventPosition()[0],
                                              self.GetInteractor().GetEventPosition()[1],
                                              0,
                                              self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer())

        # ----------------------------show path points---------------------------
        # for i in PATH_POINT_INDEX:
        #     for j in i:
        #         self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(
        #             addSphere(POINTS[j], 0.2, GREEN))
        #
        # self.GetInteractor().GetRenderWindow().Render()
        # ----------------------------show path points---------------------------

        startPointIndex = self.picking()

        if startPointIndex is not None and ENCLOSED is True:
            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(
                addSphere(POINTS[startPointIndex], 0.5, GREEN))
            self.GetInteractor().GetRenderWindow().Render()

            APART_POINT_INDEX.append(startPointIndex)

            # propagation
            PROPAGATION.start()

        self.OnMiddleButtonDown()
        return

    def mouseMoveEvent(self, obj, event):
        global PICKED_POINT_INDEX, PICKED_PATH_ACTOR

        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        temporary_end_point_index = self.picking()

        if temporary_end_point_index is not None and ENCLOSED is False:

            # print(PICKED_POINT_INDEX)
            if len(PICKED_POINT_INDEX[-1]) > 0:
                path_ids, path_actor = get_geodesic_path(PICKED_POINT_INDEX[-1][-1], temporary_end_point_index)

                if PATH_POINT_INDEX[-1] != '':
                    renderer.RemoveActor(PICKED_PATH_ACTOR[-1])

                renderer.AddActor(path_actor)
                PICKED_PATH_ACTOR[-1] = path_actor
                PATH_POINT_INDEX[-1] = path_ids

                self.GetInteractor().GetRenderWindow().Render()

        self.OnMouseMove()
        return


class Propagation(QThread):

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self) -> None:
        global PATH_POINT_INDEX, APART_POINT_INDEX, UPDATE

        # flatten picked points
        picked_points = []
        for i in PATH_POINT_INDEX:
            for j in i:
                picked_points.append(j)

        # propagation
        for sp in APART_POINT_INDEX:

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
                if_pushback = True

                for ep in APART_POINT_INDEX:
                    if p == ep:
                        if_pushback = False
                        break

                for pp in picked_points:
                    if p == pp:
                        if_pushback = False
                        break

                if if_pushback is True:
                    APART_POINT_INDEX.append(p)
                    print('append', len(APART_POINT_INDEX))

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


def addLine(point1, point2, lineWidth, color):
    lineSource = vtk.vtkLineSource()
    lineSource.SetPoint1(point1)
    lineSource.SetPoint2(point2)
    lineSource.Update()

    lineMapper = vtk.vtkPolyDataMapper()
    lineMapper.SetInputConnection(lineSource.GetOutputPort())

    lineActor = vtk.vtkActor()
    lineActor.SetMapper(lineMapper)
    lineActor.GetProperty().SetLineWidth(lineWidth)
    lineActor.GetProperty().SetColor(color)

    return lineActor


def get_geodesic_path(start_index, end_index):
    global INPUT_MODEL

    dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
    dijkstra.SetInputData(INPUT_MODEL.GetOutput())
    dijkstra.SetStartVertex(start_index)
    dijkstra.SetEndVertex(end_index)
    dijkstra.Update()

    path_mapper = vtk.vtkPolyDataMapper()
    path_mapper.SetInputConnection(dijkstra.GetOutputPort())

    path_actor = vtk.vtkActor()
    path_actor.SetMapper(path_mapper)
    path_actor.GetProperty().SetColor(BLUE)
    path_actor.GetProperty().SetLineWidth(10)

    ids = []
    id_list = dijkstra.GetIdList()
    for i in range(id_list.GetNumberOfIds()):
        ids.append(id_list.GetId(i))

    return ids, path_actor


def get_nnindex(index):
    nn_index = []

    for i in range(INPUT_MODEL.GetOutput().GetNumberOfCells()):
        id_list = vtk.vtkIdList()
        INPUT_MODEL.GetOutput().GetCellPoints(i, id_list)

        if id_list.GetId(0) == index:
            nn_index.append(id_list.GetId(1))
            nn_index.append(id_list.GetId(2))

        if id_list.GetId(1) == index:
            nn_index.append(id_list.GetId(0))
            nn_index.append(id_list.GetId(2))

        if id_list.GetId(2) == index:
            nn_index.append(id_list.GetId(0))
            nn_index.append(id_list.GetId(1))

    nn_index = list(dict.fromkeys(nn_index))

    return nn_index


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


# need to improve
def output_separated_data():
    global INPUT_MODEL, POINTS, PATH_POINT_INDEX, APART_POINT_INDEX

    ann_points = APART_POINT_INDEX
    non_points = []
    ann_faces = []
    non_faces = []

    # get points
    for i in PATH_POINT_INDEX:
        for j in i:
            ann_points.append(j)

    for i in POINTS:
        is_ann = False
        for j in APART_POINT_INDEX:
            if i == j:
                is_ann = True
                break
        if is_ann is False:
            non_points.append(i)

    # get faces
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
            ann_faces.append([id_list.GetId(0) + 1, id_list.GetId(1) + 1, id_list.GetId(2) + 1])
        else:
            non_faces.append([id_list.GetId(0) + 1, id_list.GetId(1) + 1, id_list.GetId(2) + 1])

    # revise point ids
    for f in ann_faces:
        for n in range(3):
            for i, id in enumerate(ann_points):
                if f[n] == id:
                    f[n] = i
                    break

    for f in non_faces:
        for i, id in enumerate(non_points):
            if f[0] == id:
                f[0] = i
            if f[1] == id:
                f[1] = i
            if f[2] == id:
                f[2] = i

    return ann_points, non_points, ann_faces, non_faces
