import numpy as np
import open3d as o3d


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


def translate_pointcloud(pointcloud):
    xyz1 = np.random.uniform(low=2. / 3., high=3. / 2., size=[3])
    xyz2 = np.random.uniform(low=-0.2, high=0.2, size=[3])

    translated_pointcloud = np.add(np.multiply(pointcloud, xyz1), xyz2).astype('float32')
    return translated_pointcloud


def points_normalize(points):
    centroid = np.mean(points, axis=0)
    points = points - centroid
    m = np.max(np.sqrt(np.sum(points ** 2, axis=1)))
    points = points / m

    return points


if __name__ == '__main__':
    # points, labels, normals = load_file('/home/yang/backup/cvpr2020/IntrA/annotated/ad/AN1-_norm.ad')
    # # points, labels, normals = np.array(points), np.array(labels), np.array(normals)
    #
    # colors = []
    # for l in labels:
    #     if l == 0:
    #         colors.append([0.8, 0.06, 0.04])
    #     else:
    #         colors.append([0.06, 0.04, 0.8])
    #
    # points, _ = points_normalize(points)
    # # prints = translate_pointcloud(points)
    #
    # pc = o3d.geometry.PointCloud()
    # pc.points = o3d.utility.Vector3dVector(points)
    # pc.normals = o3d.utility.Vector3dVector(normals)
    # pc.colors = o3d.utility.Vector3dVector(colors)
    #
    # mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pc, o3d.utility.DoubleVector([0.06, 0.1]))

    # vis = o3d.visualization.Visualizer()
    # # print(vis.get_render_option().point_size)
    # vis.create_window()
    # vis.add_geometry(pc)
    # vis.run()
    # vis.destroy_window()

    # o3d.visualization.point_size = 1000
    # o3d.visualization.draw_geometries([pc, mesh])

    mesh = o3d.io.read_triangle_mesh("input_file.obj")

    v = np.asarray(mesh.vertices)
    v = points_normalize(v)
    mesh.vertices = o3d.utility.Vector3dVector(np.asarray(v))

    colors = []
    for l in range(len(mesh.vertices)):
        if l < 100:
            colors.append([0.8, 0.06, 0.04])
        else:
            colors.append([0.06, 0.04, 0.8])

    mesh.vertex_colors = o3d.utility.Vector3dVector(colors)

    mesh.compute_vertex_normals()
    # mesh.paint_uniform_color([0.8, 0.06, 0.04])
    o3d.visualization.draw_geometries([mesh])

