import vtk


def load(filename):
    points = []
    a_points = []
    o_points = []
    a_faces = []
    o_faces = []
    group = None

    with open(filename, 'r') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            s_line = line.split()
            if len(s_line) > 0:
                if s_line[0] == 'v':
                    points.append((float(s_line[1]), float(s_line[2]), float(s_line[3])))
                if s_line[0] == 'g' and s_line[1][0] == 'a':
                    group = 'a'
                if s_line[0] == 'g' and s_line[1][0] == 'o':
                    group = 'o'
                if s_line[0] == 'f' and group == 'a':
                    f = (int(s_line[1]) - 1, int(s_line[2]) - 1, int(s_line[3]) - 1)
                    a_faces.append(f)
                    a_points.append(f[0])
                    a_points.append(f[1])
                    a_points.append(f[2])
                if s_line[0] == 'f' and group == 'o':
                    f = (int(s_line[1]) - 1, int(s_line[2]) - 1, int(s_line[3]) - 1)
                    o_faces.append(f)
                    o_points.append(f[0])
                    o_points.append(f[1])
                    o_points.append(f[2])

        # points = list({}.fromkeys(points).keys())
        print(len(points))

        a_points = list({}.fromkeys(a_points).keys())
        a_points.sort()
        o_points = list({}.fromkeys(o_points).keys())
        o_points.sort()

        print(len(a_points))
        print(len(o_points))

    return points, a_points, o_points, a_faces, o_faces


def make_poly_data(points, faces, color):
    vtk_points = vtk.vtkPoints()
    vtk_faces = vtk.vtkCellArray()
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName('colors')

    for i, p in enumerate(points):
        vtk_points.InsertNextPoint(p)
        colors.InsertNextTypedTuple(color)

    for i, f in enumerate(faces):
        triangle = vtk.vtkTriangle()
        triangle.GetPointIds().SetId(0, f[0])
        triangle.GetPointIds().SetId(1, f[1])
        triangle.GetPointIds().SetId(2, f[2])

        vtk_faces.InsertNextCell(triangle)

    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(vtk_points)
    poly_data.SetPolys(vtk_faces)

    poly_data.GetPointData().SetScalars(colors)
    poly_data.Modified()

    return poly_data


def make_actor(model):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(model)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetPointSize(5)

    return mapper, actor


def separate(points, part_points_index, part_faces):
    new_points = []
    new_faces = []

    for p in part_points_index:
        new_points.append(points[p])

    for f in part_faces:
        face = [0, 0, 0]
        for i in range(3):
            for j, pi in enumerate(part_points_index):
                if f[i] == pi:
                    face[i] = j
                    break
        new_faces.append(face)

    return new_points, new_faces


def show(filename):
    points, a_points_index, o_points_index, a_faces, o_faces = load(filename)

    a_points, a_faces = separate(points, a_points_index, a_faces)
    o_points, o_faces = separate(points, o_points_index, o_faces)

    red = (255, 0, 0)
    blue = (0, 0, 255)
    a_model = make_poly_data(a_points, a_faces, red)
    o_model = make_poly_data(o_points, o_faces, blue)

    _, a_actor = make_actor(a_model)
    _, o_actor = make_actor(o_model)

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    renderer.AddActor(a_actor)
    renderer.AddActor(o_actor)

    render_window.Render()
    render_window_interactor.Start()


if __name__ == '__main__':
    filename = 'input_file.obj'

    # data = load(filename)
    # for i in data:
    #     print(len(i))

    show(filename)

