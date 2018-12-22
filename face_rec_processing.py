# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'face_rec_processing.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1687, 1169)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.horizontalLayout_6.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.PushButton_Save = QtWidgets.QPushButton(self.centralwidget)
        self.PushButton_Save.setEnabled(False)
        self.PushButton_Save.setCheckable(False)
        self.PushButton_Save.setChecked(False)
        self.PushButton_Save.setDefault(False)
        self.PushButton_Save.setObjectName("PushButton_Save")
        self.verticalLayout_2.addWidget(self.PushButton_Save, 0, QtCore.Qt.AlignTop)
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.verticalLayout_2.addWidget(self.treeWidget)
        self.StartStopPushButton = QtWidgets.QPushButton(self.centralwidget)
        self.StartStopPushButton.setObjectName("StartStopPushButton")
        self.verticalLayout_2.addWidget(self.StartStopPushButton)
        self.horizontalLayout_6.addLayout(self.verticalLayout_2)
        self.horizontalLayout.addLayout(self.horizontalLayout_6)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1687, 21))
        self.menubar.setObjectName("menubar")
        self.menu_File = QtWidgets.QMenu(self.menubar)
        self.menu_File.setObjectName("menu_File")
        self.menu_Help = QtWidgets.QMenu(self.menubar)
        self.menu_Help.setObjectName("menu_Help")
        self.menuTools = QtWidgets.QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menu_Filter = QtWidgets.QMenu(self.menubar)
        self.menu_Filter.setObjectName("menu_Filter")
        self.menu_Set = QtWidgets.QMenu(self.menubar)
        self.menu_Set.setObjectName("menu_Set")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionE_xit = QtWidgets.QAction(MainWindow)
        self.actionE_xit.setObjectName("actionE_xit")
        self.action_About = QtWidgets.QAction(MainWindow)
        self.action_About.setObjectName("action_About")
        self.action_Display_Image = QtWidgets.QAction(MainWindow)
        self.action_Display_Image.setObjectName("action_Display_Image")
        self.actionSet_Reference_Faces = QtWidgets.QAction(MainWindow)
        self.actionSet_Reference_Faces.setObjectName("actionSet_Reference_Faces")
        self.action_Filter_All_Faces = QtWidgets.QAction(MainWindow)
        self.action_Filter_All_Faces.setObjectName("action_Filter_All_Faces")
        self.action_Filter_Named_Faces = QtWidgets.QAction(MainWindow)
        self.action_Filter_Named_Faces.setObjectName("action_Filter_Named_Faces")
        self.action_Filter_Reference_Faces = QtWidgets.QAction(MainWindow)
        self.action_Filter_Reference_Faces.setObjectName("action_Filter_Reference_Faces")
        self.action_Set_Reference_Faces = QtWidgets.QAction(MainWindow)
        self.action_Set_Reference_Faces.setObjectName("action_Set_Reference_Faces")
        self.action_Filter_Unnamed_Faces = QtWidgets.QAction(MainWindow)
        self.action_Filter_Unnamed_Faces.setEnabled(True)
        self.action_Filter_Unnamed_Faces.setObjectName("action_Filter_Unnamed_Faces")
        self.action_Find_Faces_in_Images = QtWidgets.QAction(MainWindow)
        self.action_Find_Faces_in_Images.setObjectName("action_Find_Faces_in_Images")
        self.action_Delete_Selected_Faces = QtWidgets.QAction(MainWindow)
        self.action_Delete_Selected_Faces.setObjectName("action_Delete_Selected_Faces")
        self.action_Tag_Unnamed_Faces = QtWidgets.QAction(MainWindow)
        self.action_Tag_Unnamed_Faces.setObjectName("action_Tag_Unnamed_Faces")
        self.action_Remove_Face_Tag = QtWidgets.QAction(MainWindow)
        self.action_Remove_Face_Tag.setObjectName("action_Remove_Face_Tag")
        self.action_Change_Face_Tag = QtWidgets.QAction(MainWindow)
        self.action_Change_Face_Tag.setObjectName("action_Change_Face_Tag")
        self.action_Search_for_Reference_Images = QtWidgets.QAction(MainWindow)
        self.action_Search_for_Reference_Images.setObjectName("action_Search_for_Reference_Images")
        self.action_Set_Named_as_Confirmed = QtWidgets.QAction(MainWindow)
        self.action_Set_Named_as_Confirmed.setObjectName("action_Set_Named_as_Confirmed")
        self.menu_File.addAction(self.actionE_xit)
        self.menu_Help.addAction(self.action_About)
        self.menuTools.addAction(self.action_Display_Image)
        self.menuTools.addAction(self.action_Find_Faces_in_Images)
        self.menu_Filter.addAction(self.action_Filter_All_Faces)
        self.menu_Filter.addAction(self.action_Filter_Named_Faces)
        self.menu_Filter.addAction(self.action_Filter_Reference_Faces)
        self.menu_Filter.addAction(self.action_Filter_Unnamed_Faces)
        self.menu_Filter.addAction(self.action_Search_for_Reference_Images)
        self.menu_Set.addAction(self.action_Set_Reference_Faces)
        self.menu_Set.addAction(self.action_Delete_Selected_Faces)
        self.menu_Set.addAction(self.action_Remove_Face_Tag)
        self.menu_Set.addAction(self.action_Change_Face_Tag)
        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Filter.menuAction())
        self.menubar.addAction(self.menu_Set.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Face Recognition Processing"))
        self.PushButton_Save.setText(_translate("MainWindow", "Save"))
        self.StartStopPushButton.setText(_translate("MainWindow", "Stop"))
        self.menu_File.setTitle(_translate("MainWindow", "&File"))
        self.menu_Help.setTitle(_translate("MainWindow", "&Help"))
        self.menuTools.setTitle(_translate("MainWindow", "Tools"))
        self.menu_Filter.setTitle(_translate("MainWindow", "&Filter"))
        self.menu_Set.setTitle(_translate("MainWindow", "&Update"))
        self.actionE_xit.setText(_translate("MainWindow", "E&xit"))
        self.action_About.setText(_translate("MainWindow", "&About"))
        self.action_Display_Image.setText(_translate("MainWindow", "&Display Image"))
        self.actionSet_Reference_Faces.setText(_translate("MainWindow", "Set Reference Faces"))
        self.action_Filter_All_Faces.setText(_translate("MainWindow", "&All Faces"))
        self.action_Filter_Named_Faces.setText(_translate("MainWindow", "&Named Faces"))
        self.action_Filter_Reference_Faces.setText(_translate("MainWindow", "&Reference Faces"))
        self.action_Set_Reference_Faces.setText(_translate("MainWindow", "Set &Reference Faces"))
        self.action_Filter_Unnamed_Faces.setText(_translate("MainWindow", "&Unnamed Faces"))
        self.action_Find_Faces_in_Images.setText(_translate("MainWindow", "&Find Faces in Images"))
        self.action_Delete_Selected_Faces.setText(_translate("MainWindow", "&Delete Selected Faces"))
        self.action_Tag_Unnamed_Faces.setText(_translate("MainWindow", "Tag &Unnamed Faces"))
        self.action_Remove_Face_Tag.setText(_translate("MainWindow", "&Remove Face Tag"))
        self.action_Change_Face_Tag.setText(_translate("MainWindow", "&Change Face Tag"))
        self.action_Search_for_Reference_Images.setText(_translate("MainWindow", "Search for &Reference Images"))
        self.action_Set_Named_as_Confirmed.setText(_translate("MainWindow", "Set Selected Named as &Confirmed"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
