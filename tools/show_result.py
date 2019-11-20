import numpy as np
import open3d as o3d
import vtk


def load_file(path):
    points = []
    labels = []
    normals = []

    with open(path, 'r') as f:
        for line in f.readlines():
            s_line = line.split()
            points.append([float(s_line[0]), float(s_line[1]), float(s_line[2])])
            normals.append([float(s_line[3]), float(s_line[4]), float(s_line[5])])
            labels.append(int(s_line[6]))

    return points, labels, normals


def load_obj_file(filename):
    points = []
    faces = []

    with open(filename, 'r') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            s_line = line.split()
            if len(s_line) > 0:
                if s_line[0] == 'v':
                    points.append((float(s_line[1]), float(s_line[2]), float(s_line[3])))
                if s_line[0] == 'f':
                    f = (int(s_line[1].split('//')[0]) - 1,
                         int(s_line[2].split('//')[0]) - 1,
                         int(s_line[3].split('//')[0]) - 1)
                    faces.append(f)

    return points, faces


def points_normalize(points):
    centroid = np.mean(points, axis=0)
    points = points - centroid
    m = np.max(np.sqrt(np.sum(points ** 2, axis=1)))
    points = points / m

    return points


def show_one_model(points, normals, labels):
    colors = []
    for l in labels:
        if l == 0:
            colors.append([0.8, 0.06, 0.04])
        else:
            colors.append([0.06, 0.04, 0.8])

    pc = o3d.geometry.PointCloud()
    pc.points = o3d.utility.Vector3dVector(points)
    # pc.normals = o3d.utility.Vector3dVector(normals)
    pc.colors = o3d.utility.Vector3dVector(colors)

    # o3d.visualization.point_size = 1000
    o3d.visualization.draw_geometries([pc])


def create_glyph(point, sphere):
    glyph = vtk.vtkGlyph3D()
    glyph.SetSourceConnection(sphere.GetOutputPort())
    glyph.SetInputData(point)
    glyph.SetVectorModeToUseNormal()
    glyph.SetScaleFactor(1)
    glyph.SetColorModeToColorByVector()
    glyph.SetScaleModeToScaleByVector()
    glyph.OrientOn()
    glyph.Update()

    glyphMapper = vtk.vtkPolyDataMapper()
    glyphMapper.SetInputConnection(glyph.GetOutputPort())
    glyphMapper.SetScalarModeToUsePointFieldData()
    glyphMapper.SetColorModeToMapScalars()
    glyphMapper.ScalarVisibilityOn()
    glyphMapper.SelectColorArray('Elevation')

    scalarRange = point.GetScalarRange()

    glyphActor = vtk.vtkActor()
    glyphActor.SetMapper(glyphMapper)

    return glyphActor


def show_one_vtk(ps, normals, ls):
    v_points = vtk.vtkPoints()
    v_vertices = vtk.vtkCellArray()

    a_points = vtk.vtkPoints()
    a_vertices = vtk.vtkCellArray()

    for i in range(len(ps)):
        if ls[i] == 0:
            p = [ps[i][0], ps[i][1], ps[i][2]]
            id = v_points.InsertNextPoint(p)
            v_vertices.InsertNextCell(1)
            v_vertices.InsertCellPoint(id)
        elif ls[i] == 1:
            p = [ps[i][0], ps[i][1], ps[i][2]]
            id = a_points.InsertNextPoint(p)
            a_vertices.InsertNextCell(1)
            a_vertices.InsertCellPoint(id)
        else:
            print('?????')

    v_point = vtk.vtkPolyData()
    v_point.SetPoints(v_points)
    v_point.SetVerts(v_vertices)

    a_point = vtk.vtkPolyData()
    a_point.SetPoints(a_points)
    a_point.SetVerts(a_vertices)

    sphere = vtk.vtkSphereSource()
    sphere.Update()

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    renderer.SetBackground(1, 1, 1)

    v_glyphActor = create_glyph(v_point, sphere)
    a_glyphActor = create_glyph(a_point, sphere)

    v_glyphActor.GetProperty().SetColor(0.8, 0.06, 0.04)
    a_glyphActor.GetProperty().SetColor(0, 1, 1)

    renderer.AddActor(v_glyphActor)
    renderer.AddActor(a_glyphActor)
    render_window.Render()
    render_window_interactor.Start()


if __name__ == '__main__':
    points, labels, normals = load_file('input_file.ad')
    show_one_vtk(points, normals, labels)
