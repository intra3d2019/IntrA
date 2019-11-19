import os
import math
import vtk
import scipy.spatial as ss
from ctypes import *


INPUT_MODEL = None
KDTREE = None
POINTS = []
BLUE = (0, 0, 255)

S_P = []

random_number = 20
distance_limitation = 15

input_filename = 'input_file.obj'


def main():
    global INPUT_MODEL, POINTS, KDTREE

    INPUT_MODEL = vtk.vtkOBJReader()
    INPUT_MODEL.SetFileName(input_filename)
    INPUT_MODEL.Update()

    v_mapper = vtk.vtkPolyDataMapper()
    v_mapper.SetInputConnection(INPUT_MODEL.GetOutputPort())

    v_actor = vtk.vtkActor()
    v_actor.SetMapper(v_mapper)

    # get points
    p = [0.0, 0.0, 0.0]
    for i in range(INPUT_MODEL.GetOutput().GetNumberOfPoints()):
        INPUT_MODEL.GetOutput().GetPoint(i, p)
        POINTS.append(tuple(p))

    KDTREE = ss.KDTree(POINTS)

    ren = vtk.vtkRenderer()
    ren.AddActor(v_actor)

    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)

    style = MouseInteractorPickingActor()
    style.SetDefaultRenderer(ren)

    iren = vtk.vtkRenderWindowInteractor()
    iren.SetInteractorStyle(style)
    iren.SetRenderWindow(renWin)
    iren.Initialize()
    iren.Start()


class MouseInteractorPickingActor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.AddObserver("MiddleButtonPressEvent", self.middleButtonPressEvent)

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
        index = self.picking()

        if index is not None:
            S_P.append(index)
            print('sp:', S_P)
            actor = addSphere(POINTS[index], 1, BLUE)

            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(actor)

        self.OnLeftButtonDown()
        return

    def middleButtonPressEvent(self, obj, event):
        split_input_filename = input_filename.split('/')

        generate_one(S_P, split_input_filename[-1], '/'+os.path.join(*split_input_filename[:-1]))

        self.OnMiddleButtonDown()
        return


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


def generate_one(index, input_file, output_path):
    print('Start!')

    input_points = POINTS
    input_model = INPUT_MODEL

    calculation = CDLL('./calculation.so')
    calculation.path_distance.argtypes = (POINTER(c_float), c_int)
    calculation.path_distance.restype = c_float

    dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
    dijkstra.SetInputData(INPUT_MODEL.GetOutput())

    for i, pp in enumerate(index):

        # use propagation
        knn_points = [pp]
        for sp in knn_points:
            nn_index = []

            cellidlist = vtk.vtkIdList()
            INPUT_MODEL.GetOutput().GetPointCells(sp, cellidlist)
            for k in range(cellidlist.GetNumberOfIds()):
                cell = INPUT_MODEL.GetOutput().GetCell(cellidlist.GetId(k))
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

                for ep in knn_points:
                    if p == ep:
                        if_pushback = False
                        break

                start_point = input_points[pp]
                end_point = input_points[p]

                if distance(start_point, end_point) > distance_limitation:
                    if_pushback = False

                if if_pushback is True:
                    knn_points.append(p)
        # end propagation

        apart_points = []

        for nnp in knn_points:
            # print('pp', pp)
            # print('nnp', nnp)
            dijkstra.SetStartVertex(pp)
            dijkstra.SetEndVertex(nnp)
            dijkstra.Update()
            # print('over')

            id_list = dijkstra.GetIdList()

            path_data_list = c_float * (id_list.GetNumberOfIds() * 3)
            path_data = path_data_list()

            for k in range(id_list.GetNumberOfIds()):
                path_data[k * 3] = input_points[id_list.GetId(k)][0]
                path_data[k * 3 + 1] = input_points[id_list.GetId(k)][1]
                path_data[k * 3 + 2] = input_points[id_list.GetId(k)][2]

            path_dis = calculation.path_distance(path_data, id_list.GetNumberOfIds() * 3)

            if path_dis < distance_limitation:
                apart_points.append(nnp)

        cells = []

        # get cells
        for ap in apart_points:
            cell_id_list = vtk.vtkIdList()
            input_model.GetOutput().GetPointCells(ap, cell_id_list)

            for j in range(cell_id_list.GetNumberOfIds()):
                cells.append(cell_id_list.GetId(j))

        cells = list(dict.fromkeys(cells))

        faces = []

        # get faces
        for c in cells:
            f = (input_model.GetOutput().GetCell(c).GetPointIds().GetId(0),
                 input_model.GetOutput().GetCell(c).GetPointIds().GetId(1),
                 input_model.GetOutput().GetCell(c).GetPointIds().GetId(2))

            if f[0] in apart_points and f[1] in apart_points and f[2] in apart_points:
                faces.append((apart_points.index(f[0]) + 1,
                              apart_points.index(f[1]) + 1,
                              apart_points.index(f[2]) + 1))

        # save file
        print(i)
        file = open(os.path.join(output_path, input_file[:-4] + '-' + str(i) + '.obj'), 'w')

        for p in apart_points:
            file.writelines('v {} {} {}\n'.format(input_points[p][0], input_points[p][1], input_points[p][2]))

        file.writelines('\n')

        for f in faces:
            file.writelines('f {} {} {}\n'.format(f[0], f[1], f[2]))

        file.writelines('\n')

        file.close()
        print('Save finished!')

    print('All finished!')


def distance(sp, ep):
    return math.sqrt((sp[0] - ep[0])**2 + (sp[1] - ep[1])**2 + (sp[2] - ep[2])**2)


if __name__ == '__main__':
    main()
