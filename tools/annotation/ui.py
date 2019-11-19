from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import viewer as viewer


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.set_window()

        self.propagation = viewer.Propagation()

        self.input_filename = None
        # self.input_filename = 'input_file.obj'
        self.tools = self.init_tools()
        self.viewer = viewer.VTKWidget(self.input_filename, self.propagation)

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
        save_button.clicked.connect(self.save_file)

        save_separate_button = QPushButton('Save Separately')
        save_separate_button.clicked.connect(self.save_separate_files)

        undo_button = QPushButton('Undo')
        undo_button.clicked.connect(self.undo_button_clicked)

        clear_button = QPushButton('Clear')
        clear_button.clicked.connect(self.clear_button_clicked)

        add_button = QPushButton('Add')
        add_button.clicked.connect(self.add_button_clicked)

        help_button = QPushButton('Help')
        help_button.clicked.connect(self.show_help)

        tools = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(open_button)
        layout.addWidget(save_button)
        layout.addWidget(save_separate_button)
        layout.addWidget(clear_button)
        layout.addWidget(undo_button)
        layout.addWidget(add_button)
        layout.addWidget(help_button)
        tools.setLayout(layout)

        return tools

    def open_file(self):
        self.viewer.init_data()

        input_filename = QFileDialog.getOpenFileName(self)[0]
        if input_filename != '':
            self.input_filename = input_filename

            self.main_layout.removeWidget(self.viewer.vtkWidget)
            self.viewer = viewer.VTKWidget(input_filename, self.propagation)
            self.main_layout.addWidget(self.viewer.vtkWidget)

    def save_file(self):
        save_filename = QFileDialog.getSaveFileName(self)[0]

        if save_filename != '':
            # obj file with groups
            file = open(save_filename, 'w')
            
            points, ann_faces, non_faces = viewer.output_data()

            for p in points:
                file.writelines('v {} {} {}\n'.format(p[0], p[1], p[2]))

            file.writelines('\n')
            file.writelines('g aneurysm\n')

            for f in ann_faces:
                file.writelines('f {} {} {}\n'.format(f[0], f[1], f[2]))

            file.writelines('\n')
            file.writelines('g others\n')

            for f in non_faces:
                file.writelines('f {} {} {}\n'.format(f[0], f[1], f[2]))

            print('Save finished!')
            file.close()


    def save_separate_files(self):
        save_filename = QFileDialog.getSaveFileName(self)[0]

        if save_filename != '':
            ann_filename = save_filename + 'ann.obj'
            non_filename = save_filename + 'non.obj'

            ann_file = open(ann_filename, 'w')
            non_file = open(non_filename, 'w')

            ann_points, non_points, ann_faces, non_faces = viewer.output_separated_data()

            for p in ann_points:
                ann_file.writelines('v {} {} {}\n'.format(p[0], p[1], p[2]))

            ann_file.writelines('\n')

            for f in ann_faces:
                ann_file.writelines('f {} {} {}\n'.format(f[0], f[1], f[2]))

            print('Ann file save finished!')
            ann_file.close()

            for p in non_points:
                non_file.writelines('v {} {} {}\n'.format(p[0], p[1], p[2]))

            non_file.writelines('\n')

            for f in non_faces:
                non_file.writelines('f {} {} {}\n'.format(f[0], f[1], f[2]))

            print('Non file save finished!')
            non_file.close()

    # def point_button_clicked(self):
    #     self.viewer.update_mode('POINT')

    # def line_button_clicked(self):
    #     self.viewer.update_mode('LINE')

    def clear_button_clicked(self):
        viewer.clear_data()
        self.main_layout.removeWidget(self.viewer.vtkWidget)
        self.viewer = viewer.VTKWidget(self.input_filename, self.propagation)
        self.main_layout.addWidget(self.viewer.vtkWidget)

    def undo_button_clicked(self):
        self.viewer.undo()

    def add_button_clicked(self):
        self.viewer.add()

    @staticmethod
    def show_help():
        with open('help.txt') as f:
            help_information = f.read()

        msg = QMessageBox()
        msg.setWindowTitle('Help')
        msg.setText(help_information)
        msg.exec_()

