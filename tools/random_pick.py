import vtk
import os
import scipy.spatial as ss
import random
import math
from ctypes import *
import gc


def distance(sp, ep):
    return math.sqrt((sp[0] - ep[0])**2 + (sp[1] - ep[1])**2 + (sp[2] - ep[2])**2)


def generate(input_path, output_path):
    folders = os.listdir(input_path)
    folders.sort()

    folders = folders[folders.index('AN28'):]

    for folder in folders:
        files = os.listdir(os.path.join(input_path, folder))
        files.sort()

        print(files[0], 'start')
        generate_one(os.path.join(input_path, folder, files[0]), files[0]+'.obj', output_path)
        print(files[0], 'finish')


def generate_one(input_path, input_file, output_path):
    random_number = 20
    distance_limitation = 15

    # load data
    input_model = vtk.vtkOBJReader()
    input_model.SetFileName(os.path.join(input_path, input_file))
    input_model.Update()
    print('load over')

    input_points = []

    p = [0.0, 0.0, 0.0]
    for i in range(input_model.GetOutput().GetNumberOfPoints()):
        input_model.GetOutput().GetPoint(i, p)
        input_points.append(tuple(p))

    picked_points = [random.randint(0, len(input_points)) for i in range(random_number)]

    calculation = CDLL('./calculation.so')
    calculation.path_distance.argtypes = (POINTER(c_float), c_int)
    calculation.path_distance.restype = c_float

    dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
    dijkstra.SetInputData(input_model.GetOutput())

    for i, pp in enumerate(picked_points):
        # bug, if two points are not connected
        # knn_points = kd_tree.query_ball_point(input_points[pp], distance_limitation)
        # print(len(knn_points))

        # use propagation
        knn_points = [pp]
        for sp in knn_points:
            nn_index = []

            cellidlist = vtk.vtkIdList()
            input_model.GetOutput().GetPointCells(sp, cellidlist)
            for k in range(cellidlist.GetNumberOfIds()):
                cell = input_model.GetOutput().GetCell(cellidlist.GetId(k))
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
            dijkstra.SetStartVertex(pp)
            dijkstra.SetEndVertex(nnp)
            dijkstra.Update()

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

        print('Save finished!')
        file.close()


if __name__ == '__main__':
    input_path = 'folder'
    output_path = 'folder'

    generate(input_path, output_path)


