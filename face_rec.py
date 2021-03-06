import bisect
import collections
import ntpath
import os
import queue
import re
import sqlite3 as lite
import sys
import time
import traceback

import AdobeElementsSQLiteTools as AEL
import PIL
import dlib
import face_recognition
import numpy
from PIL import ImageDraw, Image, ExifTags, ImageQt
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool, Qt, QMutexLocker, QMutex, QDate
from PyQt5.QtGui import QImage, QKeyEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication, qApp, QLabel, QComboBox, QTreeWidgetItem, \
    QMessageBox, QInputDialog

from face_rec_processing import Ui_MainWindow


# class delkeyFilter(QObject):
#     def __init(self):
#         super(Worker, self).__init__()
#         self.delkeyPressed = pyqtSignal()
#
#     def eventFilter(self,  obj,  event):
#         if event.type() == QEvent.KeyPress:
#             if event.key() == Qt.Key_Delete:
#                 self.delkeyPressed.emit()
#                 print ('delkey pressed')
#                 return True
#         return False


# class TableWidget(QtWidgets.QTableWidget):
#
#     def setImage(self, row, col, image:QImage):
#         # imageHeight = 100
#         mediaCell = QtWidgets.QTableWidgetItem()
#         # image = QtGui.QPixmap(imagePath).scaled(100, imageHeight, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
#         pix_image = QtGui.QPixmap(image)
#         mediaCell.setData(QtCore.Qt.DecorationRole, pix_image)
#         imageHeight = pix_image.height()
#         # self.setRowHeight(row, imageHeight)
#         self.setItem(row, col, mediaCell)
#         ## image = ImageWidget(imagePath, self)
#         ## self.setCellWidget(row, col, image)
#
#     def setListWidget(self, row, col, list_data):
#         listWidget = QtWidgets.QListWidget(self)
#         listWidget.addItems(list_data)
#         # listWidget.setWindowTitle('PyQT QListwidget Demo')
#         self.setCellWidget(row, col, listWidget)

class EditImageTableCellWidget(QWidget):
    # TODO Implement a system to keep track of whether any cell has changed since last save and if it has then
    #  reenable the save button. Probably an event in the instance rather than here!!!!!

    # def __init__(self, parent=None):
    #     super(EditImageTableCellWidget, self).__init__(parent)
    #
    #     # Arrange in layout
    #     layout = QVBoxLayout()
    #
    #     # adjust spacings to your needs
    #     layout.setContentsMargins(0, 0, 0, 0)
    #     layout.setSpacing(0)
    #     self.thumb_qlabel = QLabel()  # Label in which to display thumbnail image
    #     # self.thumb_qcombo = QComboBox()
    #     self.thumb_qcombo = QLabel()  # Label in which to display tag (planned to be a combo eventually)
    #     layout.addWidget(self.thumb_qlabel)
    #     # self.thumb_qlabel.setAutoFillBackground(True)
    #     self.thumb_qcombo.setAutoFillBackground(True)
    #     layout.addWidget(self.thumb_qcombo)
    #     self._is_reference_face = None
    #
    #     self.setLayout(layout)
    #
    #     self.face_id = None
    #     self.media_id = None
    #     self.tag_id = None

    # def __init__(self,
    #              parent=None,
    #              face_id:int=None,
    #              tag_distance_list:list=None,
    #              media_id:int=None,
    #              is_reference_face:bool=None,
    #              is_confirmed_face:bool=None,
    #              filename:str=''):
    #     """
    #
    #     :param parent:              Parent window
    #     :param face_id:             face_id of this face in face_table of PK extended Adobe elements cataolg
    #     :param tag_distance_list:   list of (tag_id, (tag_name, distance)) tuples, sorted by ascending face_recognition
    #                                 distance where distance is the similarity between this face_id and a reference face
    #                                 with the specified tag indicated a number from 0 to 1 where 0 is closest match.
    #     :param media_id:            media_id (from PK extended Adobe elements cataolg) from which this face was extracted.
    #     :param is_reference_face:   True if this face has been selected as a face to use as a reference
    #                                 to use for identification of other faces for the same person
    #     :param is_confirmed_face:   True if this face's tag has been confirmed to match the best matching face in the
    #                                 tag_distance_list
    #     :param filename:            The fully qualified filename of the image with media_id from whcih this face was extracted
    #     """
    #     layout = self._init_base_params(parent=parent,
    #                           face_id=face_id,
    #                           media_id=media_id,
    #                           filename=filename)
    #     # Now add tag elements
    #     self.thumb_qcombo = QComboBox()
    #     self.thumb_qcombo.setAutoFillBackground(True)
    #
    #     # Has to be done here since these rely on thumb_qcombo existence
    #     self.is_reference_face = is_reference_face
    #     self.is_confirmed_face = is_confirmed_face
    #
    #     # add tags to the combo
    #     if tag_distance_list:
    #         (tag_ids, (tag_names, distances)) = zip(*tag_distance_list)
    #         self.thumb_qcombo.addItems(tag_names[0:4])
    #     layout.addWidget(self.thumb_qcombo, alignment=Qt.AlignBottom)

    def keyPressEvent(self, e: QKeyEvent):
        key_pressed = e.key()
        if (e.modifiers() & Qt.ControlModifier) and (key_pressed == Qt.Key_C or key_pressed) == Qt.Key_V or key_pressed == Qt.Key_Insert:
            # Ignore Ctrl+C and Ctrl+V and Ctrl+Ins event and send event to parent
            e.ignore()


    def __init__(self,
                 parent=None,
                 face_id: int = None,
                 tag_distance_list: list = None,
                 tag_id: int = None,
                 tag_name: str = None,
                 media_id: int = None,
                 is_reference_face: bool = None,
                 is_confirmed_face: bool = None,
                 exclude_from_face_search: bool = None,
                 filename: str = ''):
        """
        Initialise this cell widget with values
        :param parent:              Parent window
        :param face_id:             int face_id of this face in face_table of PK extended Adobe elements cataolg
        :param tag_distance_list:   list of (tag_id, (tag_name, distance)) tuples, sorted by ascending face_recognition
                                    distance where distance is the similarity between this face_id and a reference face
                                    with the specified tag indicated a number from 0 to 1 where 0 is closest match.
        :param tag_id:              int tag_id of the face that identifies this person (None if not tagged)
        :param tag_name:            str tag_name containing name of person with this face (None if not tagged)
        :param media_id:            int media_id (from PK extended Adobe elements cataolg) from which this face was extracted.
        :param is_reference_face:   True if this face has been selected as a face to use as a reference
                                    to use for identification of other faces for the same person
        :param is_confirmed_face:   True if this face's tag has been confirmed to match the best matching face in the
                                    tag_distance_list
        :param filename:            The fully qualified filename of the image with media_id from whcih this face was extracted
        """
        layout = self._init_base_params(parent=parent,
                                        face_id=face_id,
                                        media_id=media_id,
                                        is_reference_face=is_reference_face,
                                        is_confirmed_face=is_confirmed_face,
                                        exclude_from_face_search=exclude_from_face_search,
                                        filename=filename)
        # Now add tag elements
        # self.thumb_qcombo = QComboBox()
        if face_id == 7490:
            pass

        if tag_distance_list:
            #todo restrict names for a single photo to only include the best matching name for each face once

            # set the cutoff distance below which a name will be included in the name list
            distance_cutoff_1 = 0.46
            distance_cutoff_2 = 0.65
            # Now add tag elements
            self.thumb_qcombo = QComboBox()
            self.thumb_qcombo.setAutoFillBackground(True)

            # add tags to the combo
            (tag_ids, tag_names_and_distances) = zip(*tag_distance_list)
            (tag_names, distances) = zip(*tag_names_and_distances)
            # add trailing distance to tag names
            annotated_tag_names = list()
            for tag_name, distance in tag_names_and_distances:
                annotated_tag_names.append("{} {:.2f}".format(tag_name, distance))
            # Find element in sorted list smaller or equal to distance_cutoff
            index2 = bisect.bisect_left(distances, distance_cutoff_2)
            self.thumb_qcombo.addItem("")
            self.thumb_qcombo.addItems(annotated_tag_names[0:index2])
            tag_ids_list = list(tag_ids[0:index2])
            tag_ids_list.insert(0, None)
            self.thumb_qcombo_tag_ids = tag_ids_list
            if distances[0] <= distance_cutoff_1:
                # Face found is a good match so select it
                # set default to tag_id of best match
                self.tag_id = tag_ids[0]
                # Set index to 1 to point at the best match
                self.thumb_qcombo.setCurrentIndex(1)
            else:
                # not a good enough match so include a blank item
                # set default to tag_id of best match
                self.tag_id = None

            layout.addWidget(self.thumb_qcombo, alignment=Qt.AlignBottom)
            self.thumb_qcombo.currentTextChanged.connect(self.on_thumb_qcombo_currentTextChanged)
        else:
            self.thumb_qcombo = QLabel()  # Label in which to display tag (combo for multiple tags)
            self.thumb_qcombo.setAutoFillBackground(True)
            layout.addWidget(self.thumb_qcombo, alignment=Qt.AlignBottom)
            if tag_name:
                # self.thumb_qcombo.addItem(tag_name)
                self.thumb_qcombo.setText(tag_name)

            if tag_id:
                self.tag_id = int(tag_id)
            else:
                self.tag_id = None
            # There's a single tag_id so clear the tag_id list
            self.thumb_qcombo_tag_ids = None


        self.set_thumb_qcombo_color()

        status_tip = "Face id: {}   Media id: {} tag_id: {} Media Filename: {}".format(self.face_id, self.media_id, self.tag_id,  filename)
        self.setStatusTip(status_tip)

        # Make sure all members are initialised
        try:
            self.face_id
            self.media_id
            self.tag_id
            self.thumb_qcombo
            self.thumb_qcombo_tag_ids
            self.thumb_qlabel
        except:
            raise

        # super(EditImageTableCellWidget, self).__init__(parent)
        #
        # # Arrange in layout
        # layout = QVBoxLayout()
        #
        # # adjust spacings to your needs
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        # self.thumb_qlabel = QLabel()  # Label in which to display thumbnail image
        # # self.thumb_qcombo = QComboBox()
        # self.thumb_qcombo = QLabel()  # Label in which to display tag (planned to be a combo eventually)
        # layout.addWidget(self.thumb_qlabel)
        # # self.thumb_qlabel.setAutoFillBackground(True)
        # self.thumb_qcombo.setAutoFillBackground(True)
        # layout.addWidget(self.thumb_qcombo)
        # self._is_reference_face = is_reference_face
        #
        # self.setLayout(layout)
        #
        # qimage = myapp.get_qimage_face_thumbnail(face_id=face_id)
        # pix_image = QtGui.QPixmap(qimage)
        # self.thumb_qlabel.setPixmap(pix_image)
        # # tag_name = 'Dummy'
        # if tag_name:
        #     # self.thumb_qcombo.addItem(tag_name)
        #     self.thumb_qcombo.setText(tag_name)
        #
        # if face_id:
        #     self.face_id = int(face_id)
        # else:
        #     self.face_id = None
        #
        # if media_id:
        #     self.media_id = int(media_id)
        # else:
        #     self.media_id = None
        #
        # self.is_reference_face = is_reference_face
        # self.is_confirmed_face = is_confirmed_face
        #
        # if tag_id:
        #     self.tag_id = int(tag_id)
        # else:
        #     self.tag_id = None
        #
        # status_tip = "Face id: {}   Media id: {}  Media Filename: {}".format(face_id, media_id, filename)
        # self.setStatusTip(status_tip)

    def _init_base_params(self,
                          parent=None,
                          face_id: int = None,
                          media_id: int = None,
                          is_reference_face: bool = False,
                          is_confirmed_face: bool = False,
                          exclude_from_face_search: bool = False,
                          filename: str = ''):
        """
        Initialise this cell widget base parameters excluding tag which will be initialised separately with multiple or
        single tag values
        :param parent:              Parent window
        :param face_id:             int face_id of this face in face_table of PK extended Adobe elements cataolg
        :param media_id:            int media_id (from PK extended Adobe elements cataolg) from which this face was extracted.
        :param is_reference_face:   True if this face has been selected as a face to use as a reference
                                    to use for identification of other faces for the same person
        :param is_confirmed_face:   True if this face's tag has been confirmed to match the person with tag_id and tag_name
        :param filename:            The fully qualified filename of the image with media_id from whcih this face was extracted
        :return                     Returns the QVBoxLayout created to continue adding to
        """
        super(EditImageTableCellWidget, self).__init__(parent)

        # Arrange in layout
        layout = QVBoxLayout()

        # adjust spacings to your needs
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.thumb_qlabel = QLabel()  # Label in which to display thumbnail image
        # self.thumb_qcombo = QComboBox()
        ##### self.thumb_qcombo = QLabel()  # Label in which to display tag (planned to be a combo eventually)
        layout.addWidget(self.thumb_qlabel, alignment=Qt.AlignTop)
        # self.thumb_qlabel.setAutoFillBackground(True)
        ##### self.thumb_qcombo.setAutoFillBackground(True)
        ##### layout.addWidget(self.thumb_qcombo)

        self.setLayout(layout)

        qimage = myapp.get_qimage_face_thumbnail(face_id=face_id)
        pix_image = QtGui.QPixmap(qimage)

        self.thumb_qlabel.setPixmap(pix_image)
        # tag_name = 'Dummy'
        ##### if tag_name:
        #####     # self.thumb_qcombo.addItem(tag_name)
        #####     self.thumb_qcombo.setText(tag_name)

        self._is_reference_face = bool(is_reference_face)
        self._is_confirmed_face = bool(is_confirmed_face)
        self._exclude_from_face_search = bool(exclude_from_face_search)

        if face_id:
            self.face_id = int(face_id)
        else:
            self.face_id = None

        if media_id:
            self.media_id = int(media_id)
        else:
            self.media_id = None

        ##### if tag_id:
        #####     self.tag_id = int(tag_id)
        ##### else:
        #####     self.tag_id = None

        return layout

    def on_thumb_qcombo_currentTextChanged(self, e:str):
        myapp.set_tableWidget_save_pending(True)

    def replace_thumb_qcombo_as_qlabel(self):
        """
        Changes this EditImageTableCellWidget's thumb_combo widget from a QComboBox to a QLabel
        :return:
        """
        if type(self.thumb_qcombo) is QComboBox:
            self.thumb_qcombo.setVisible(False)
            layout = self.thumb_qcombo.parent().layout()
            layout.removeWidget(self.thumb_qcombo)
            self.thumb_qcombo.destroy()
            self.thumb_qcombo = None
            self.thumb_qcombo = QLabel()
            layout.addWidget(self.thumb_qcombo, Qt.AlignBottom)
            self.thumb_qcombo_tag_ids = None
            self.thumb_qcombo.update()

    def set_thumb_qcombo_color(self):
        if type(self.thumb_qcombo) is QComboBox:
            t = 'QComboBox'
        else:
            t = 'QLabel'

        if self._exclude_from_face_search:
            self.thumb_qcombo.setStyleSheet(t + ' {background-color:grey;color:black}')
        elif self._is_reference_face:
            self.thumb_qcombo.setStyleSheet(t + ' {background-color:red;color:white}')
        elif self._is_confirmed_face:
            self.thumb_qcombo.setStyleSheet(t + ' {background-color:yellow;color:black}')
        else:
            self.thumb_qcombo.setStyleSheet(t + ' {background-color:white;color:black}')

    @property
    def is_confirmed_face(self):
        return self._is_confirmed_face

    @is_confirmed_face.setter
    def is_confirmed_face(self, value: bool):
        self._is_confirmed_face = value
        self.set_thumb_qcombo_color()

    @property
    def exclude_from_face_search(self):
        return self._exclude_from_face_search

    @exclude_from_face_search.setter
    def exclude_from_face_search(self, value: bool):
        self._exclude_from_face_search = value
        # self._is_reference_face = False
        # self._is_confirmed_face = False
        self.set_thumb_qcombo_color()


    @property
    def is_reference_face(self):
        return self._is_reference_face

    @is_reference_face.setter
    def is_reference_face(self, value: bool):
        self._is_reference_face = value
        self.set_thumb_qcombo_color()

    def mouseDoubleClickEvent(self, mouseEvent: QtGui.QMouseEvent):
        display_source_image_with_face_rectangles(face_id=self.face_id, db_con=myapp.db_con)
        mouseEvent.accept()

    # def focusInEvent(self, event:QtGui.QFocusEvent):
    #     QWidget.focusInEvent(event)


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = collections.OrderedDict()
        self.mutex = QMutex()

    def get(self, key):
        mutexLocker = QMutexLocker(self.mutex)
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return -1

    def set(self, key, value):
        mutexLocker = QMutexLocker(self.mutex)
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value


# This is an example of running face recognition on a single image
# and drawing a box around each person that was identified.

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No parameters

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress and threadID

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int, int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            try:
                self.signals.result.emit(result)  # Return the result of the processing
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))

        finally:
            self.signals.finished.emit()  # Done


class myMainWindow(QMainWindow):
    timer_interval = 0.5
    face_distance_tolerance = 0.6  # 0.45
    scaled_height_for_resized_images = 1200
    thumbnail_height = 100
    tag_id_of_face_scan_completed_tag = 0
    image_cache = LRUCache(300)
    thumbnail_cache = LRUCache(1000)
    thumbnail_directory = os.getenv('LOCALAPPDATA') + r'\face_rec\thumbnails' + '\\'

    def __del__(self):
        if self.db_con:
            self.db_con.close()

    def keyPressEvent(self, e: QKeyEvent):
        key_pressed = e.key()
        if e.modifiers() & Qt.ControlModifier:
            if key_pressed == Qt.Key_C:
                # Get current tableWidget cell and copy its tag name and tag_id
                table_widget_item = self.ui.tableWidget.cellWidget(self.ui.tableWidget.currentRow(),
                                                                 self.ui.tableWidget.currentColumn())
                if table_widget_item:
                    # There is a current widget so get it's tag name and id
                    if type(table_widget_item.thumb_qcombo) is QComboBox:
                        # widget's tag is in a combo box so get its text
                        if table_widget_item.thumb_qcombo_tag_ids:
                            tag_name = table_widget_item.thumb_qcombo.currentText()
                            tag_id = table_widget_item.thumb_qcombo_tag_ids[
                                table_widget_item.thumb_qcombo.currentIndex()]
                        else:
                            # combo but has no tag data so no tag
                            tag_name = ""
                            tag_id = None
                    else:
                        # tag is a qlabel so get its data
                        tag_name = table_widget_item.thumb_qcombo.text()
                        tag_id = table_widget_item.tag_id
                else:
                    # empty cell so clear
                    tag_name = ""
                    tag_id = None

                # set the text of the label and id
                self.ui.label_clipboard_tag.setText(tag_name)
                self.copy_tag_id = tag_id

                # consume event
                e.accept()

            elif key_pressed == Qt.Key_V or key_pressed == Qt.Key_Insert:
                # change tag
                # get tag data from label
                tag_id = self.copy_tag_id
                tag_name = self.ui.label_clipboard_tag.text()

                # remove trailing distance portion of tag if present.
                m = self.re_trailing_distance_search.search(tag_name)
                if m:
                    tag_name = tag_name[0:m.start()]

                # update selected face widgets to this tag
                self.set_face_tag_of_selected_widget_items_to_tag_id(tag_id, tag_name)

                # Write changes in to selected face widgets to the db catalog
                self.update_catalog_from_selected_faces()

                # consume event
                e.accept()

    def closeEvent(self, *args, **kwargs):
        event = args[0]

        if not self.ExitApp():
            # Action was cancelled by user
            event.ignore()
        else:
            # Action not cancelled so accept this event.
            event.accept()

    def ExitApp(self):
        """
        Called when exit has been requested to first check if we need to save if appropriate.

        :return:  True if we should exit. False if exit cancelled by user.
        """
        print("Exit requested")
        if self.tableWidget_save_pending:
            # Call the save function tat was specified
            b_exit_confirmed = self.save_function_tableWidget()
            if not b_exit_confirmed:
                return False
            self.tableWidget_save_pending = False
        self.face_processing_termination_requested = True
        self.threadpool.waitForDone()
        qApp.exit()

        # Return flagging that action was not cancelled.
        return True

    # def testkeypress(self):
    #     print("testkeypress")

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # clipboard tag_id
        self.clipboard_tag_id = None
        self.ui.label_clipboard_tag.clear()

        # Regular expression search to find position of trailing distance portion of a tag
        self.re_trailing_distance_search = re.compile(' 0\.\d{2}$')

        # # Create an action group with every menu item so you can quickly enable and disable all menu items during processing.
        # self.menu_action_group = QActionGroup(self)
        # action_list = self.enumerate_menu_actions(self.ui.menubar)
        # for action in action_list:
        #     self.menu_action_group.addAction(action)

        self.ui.actionE_xit.triggered.connect(self.ExitApp)
        self.ui.action_About.triggered.connect(self.action_About)
        self.ui.action_Display_Image.triggered.connect(self.action_display_image)

        self.ui.action_Remove_Face_Tag.triggered.connect(self.remove_face_tag_from_selected_items)
        self.ui.action_Change_Face_Tag.triggered.connect(self.change_face_tag_from_tree_widget)
        self.ui.action_Search_for_Reference_Images.triggered.connect(self.search_for_reference_faces)

        self.ui.action_Delete_Selected_Faces.triggered.connect(self.delete_selected_faces)
        self.ui.action_Find_Faces_in_Images.triggered.connect(self.find_faces_in_images)
        self.ui.action_Filter_All_Faces.triggered.connect(self.filter_all_faces)
        self.ui.action_Filter_Named_Faces.triggered.connect(self.filter_named_faces)
        self.ui.action_Filter_Reference_Faces.triggered.connect(self.filter_reference_faces)
        self.ui.action_Set_Reference_Faces.triggered.connect(self.set_reference_faces)
        self.ui.action_Filter_Unnamed_Faces.triggered.connect(self.filter_unnamed_faces)
        self.ui.action_Set_Confirmed_Faces.triggered.connect(self.set_confirmed_faces)
        self.ui.action_Search_for_Clusters_in_Unnamed_Faces.triggered.connect(self.scan_unknown_faces_for_clusters_dlib)
        self.ui.action_People_with_No_Reference_Faces.triggered.connect(self.filter_people_with_no_reference_faces)
        self.ui.action_Fix_Ref_Images_not_properly_tagged.triggered.connect(self.fix_reference_images_that_were_not_properly_tagged)
        self.ui.action_Exclude_From_Face_Search.triggered.connect(
            self.exclude_from_face_search)
        self.ui.action_Add_Face_Tag.triggered.connect(self.add_face_tag_to_tree_widget)

        self.ui.action_Update_Metadata_of_Files_in_Catalog.triggered.connect(self.update_metadata_of_files_in_catalog)
        self.ui.PushButton_Save.clicked.connect(self.save_added_tags)
        self.ui.lineEditSearch.textChanged.connect(self.tree_search_text_changed)

        self.ui.StartStopPushButton.setEnabled(False)
        self.ui.StartStopPushButton.setVisible(False)

        self.ui.PushButton_Save.setEnabled(False)
        self.ui.PushButton_Save.setVisible(False)

        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setVisible(False)
        self.ui.tableWidget.cellDoubleClicked.connect(self.cellDoubleClicked)
        # self.ui.tableWidget.setMouseTracking(True) #Set this if you want mouse movement to be tracked over table cells so it automatically updates status bar if using QTableWidgetItems

        # self.connect(self.ui.tableWidget, QtCore.pyqtSignal(self.cellDoubleClicked(int, int)), self,
        #               QtCore.pyqtSlot(self.tableItemDoubleClicked(int, int)))
        # status_bar = QtWidgets.QStatusBar(self)
        # self.setStatusBar(status_bar)

        self.face_proecessing_in_progress = False
        self.face_processing_termination_requested = False

        self.grid_cols = 10
        self.grid_num_images = 10000
        self.grid_start_image = 1
        self.tableWidget_save_pending = False  # Set to true if the tableWidget has been changed and needs to be saved
        # and set save_function_tableWidget to function you need to call
        self.save_function_tableWidget = None
        self.tree_widget_item_list:list = None

        self.ui.tableWidget.setColumnCount(self.grid_cols)

        # self.shortcut = QShortcut(QKeySequence("PgDown"), self, self.onPgDnShortcutTriggered(), self.onPgDnShortcutTriggered(), Qt.WindowShortcut)
        # self.filter = delkeyFilter(self)
        # self.installEventFilter(self.filter)
        # self.filter.delkeyPressed.connect(self.testkeypress)

        # Queue to store the results passed back by Worker threads processing faces so that they can be progressively saved
        # to the database and added to the display list
        self.result_queue = queue.Queue()

        self.work_to_be_done_queue = queue.Queue()
        self.threadpool = QThreadPool()
        self.max_thread_count = 1

        # Open sqlite adobe photoshop element 6 catalog database
        self.db_con = lite.connect(r'C:\ProgramData\Adobe\Photoshop Elements\Catalogs\My Catalog\catalog.psedb')

        # Set up for use of default, special row_factory so that columns can be accessed by name
        self.db_con.row_factory = lite.Row

        # Open sqlite media thumbnail cache and setup row factory in case we want to access columns by name
        self.media_thumb_db_con = lite.connect(r'C:\ProgramData\Adobe\Photoshop Elements\Catalogs\My Catalog\thumb.5.cache')

        self.people_tag_id = AEL.get_tag_id_of_specified_tag_name(self.db_con, 'People')

        # Get tag number of
        myMainWindow.tag_id_of_face_scan_completed_tag = AEL.get_tag_id_of_specified_tag_name(self.db_con,
                                                                                              'Face Scan Completed')
        if not myMainWindow.tag_id_of_face_scan_completed_tag:
            raise (Exception("Couldn't find 'Face Scan Completed' in Adobe catalog."))

    def add_face_tag_to_tree_widget(self):
        """
        Adds a face tag as a child of the currently selected treeWidget element and allows user to edit.  Then
        saves the new tag in the catalog and updates the treeWidget element list.
        :return:
        """
        tree_widget_items = self.ui.treeWidget.selectedItems()
        if not tree_widget_items or tree_widget_items.__len__() != 1:
            msgBox = QMessageBox()
            msgBox.setText("Please select a single tag under which you would like the new face tag inserted.")
            msgBox.exec()
            return

        tree_widget_item = tree_widget_items[0]
        tree_widget_item.setExpanded(True)
        new_tree_widget_item = QTreeWidgetItem()
        flags = new_tree_widget_item.flags()
        new_flags = flags | Qt.ItemIsEditable
        new_tree_widget_item.setFlags(new_flags)
        tree_widget_item.insertChild(0, new_tree_widget_item)
        self.ui.treeWidget.scrollToItem(tree_widget_item)

        # Activate trapping of this signal so we can save disable editability when we've finished.
        self.ui.treeWidget.itemChanged.connect(self.tree_widget_item_changed)

        self.ui.treeWidget.editItem(new_tree_widget_item)

    def tree_widget_item_changed(self, tree_widget_item:QTreeWidgetItem, column:int):
        """
        Signal activated when a treeWidgetItem is changed.  Updates item in catalog and dactiveates editability of the
        treeWidgetItem
        :return:
        """
        # Disconnect signal so this doesn't get called again until reactivated.
        self.ui.treeWidget.itemChanged.disconnect(self.tree_widget_item_changed)

        # Disable editing of this item.
        flags = tree_widget_item.flags() & (~Qt.ItemIsEditable)
        tree_widget_item.setFlags(flags)

        # save new tag to catalog - which also sets "can_have_children" attribute of parent if not set in tag_table
        tag_name = tree_widget_item.text(0)
        parent_tag_id = tree_widget_item.parent().data(0, Qt.UserRole)
        tag_id = AEL.CreateTag(self.db_con, tag_name, parent_tag_id, can_have_children=0)
        tree_widget_item.setData(0, Qt.UserRole, tag_id)
        self.ui.treeWidget.scrollToItem(tree_widget_item)

    def update_metadata_of_files_in_catalog(self):
        """
        Updates the metadata of images added to the catalog with their earliest date metadata after the date
        entered by the user
        :return:
        """
        # get a date
        date_mask = "dd/MM/yyyy"

        qdate_default = QDate.currentDate().addMonths(-3)

        (user_date_text, ok) = QInputDialog.getText(self,
            'Catalog Metadata Update',
            'Enter date after which images in the Adobe Photoshop Elements catalog should have their metadata updated.',
            text=qdate_default.toString(date_mask))

        if ok:
            user_date = QDate.fromString(user_date_text, date_mask)
            if user_date:
                py_user_date = user_date.toPyDate()
                AEL.CheckUpdateMetadataOfFilesInCatalog(self.db_con, date_taken_start_date=py_user_date, update=False)

    def tree_search_text_changed(self, text:str):
        """
        Displays items in the treeview that match the entered text
        :param text:
        :return:
        """
        # disp items in treeview that match the entered text when >= 3 chars
        if len(text) >= 3:
            index = 0
            for tree_widget_item in self.tree_widget_item_list:
                if text.lower() in tree_widget_item.text(0).lower():
                    self.ui.treeWidget.setCurrentItem(tree_widget_item,0)
                    # model_index = self.ui.treeWidget.indexFromItem(tree_widget_item,0)
                    # self.ui.treeWidget.scrollTo(model_index)
                    break
                index += 1
        else:
            pass

    def enumerate_menu_actions(self, menu: QtWidgets.QMenu, action_list: list = None):
        """
        Returns list of all the QActions in a menu and it's submenus
        :param menu:            QMenu to enumerate
        :param action_list:     list to add actions to (None on first call as called recursively)
        :return:                list_of_actions: QAction
        """
        if not action_list:
            action_list = list()
        for action in menu.actions():
            if not action.isSeparator():
                if action.menu():
                    action_list = self.enumerate_menu_actions(action.menu(), action_list)
                else:
                    action_list.append(action)
        return action_list

    def save_added_tags(self):
        # todo WORK OUT WHY SAVE IS NOT WORKING!!!!! It's adding tags that should have been cleared.  Could be that clearing tags is not working properly (check tag_id is cleared???)
        # save newly added tags in tableWidget data to database up to the row that currently has focus
        # Check all faces in tableWidget and if they have tags, save them to the face_table
        row = 0
        col = 0
        update_list = list()
        max_row = self.ui.tableWidget.currentRow() + 1
        if max_row:
            for row in range(max_row):
                for col in range(self.ui.tableWidget.columnCount()):
                    table_widget_item = self.ui.tableWidget.cellWidget(row, col)
                    if table_widget_item:
                        # Found a non-empty table_widget_item in this cell so check if it has a tag value to save
                        if type(table_widget_item.thumb_qcombo) is QComboBox:
                            # widget's tag is in a combo box so get its text
                            if table_widget_item.thumb_qcombo_tag_ids:
                                # tag_name = table_widget_item.thumb_qcombo.currentText()
                                tag_id = table_widget_item.thumb_qcombo_tag_ids[table_widget_item.thumb_qcombo.currentIndex()]
                            else:
                                tag_id = None
                        else:
                            # widget's tag is in a QLabel so get its text
                            # tag_name = table_widget_item.thumb_qcombo.text()
                            tag_id = table_widget_item.tag_id
                        if tag_id:
                            update_list.append((tag_id, table_widget_item.face_id))
            # Update tags to face_table
            if update_list:
                try:
                    with self.db_con:

                        query = """
                            UPDATE face_table
                            SET 
                                tag_id = ?
                            WHERE
                                face_id = ?;            
                        """
                        cur = self.db_con.cursor()
                        cur.executemany(query, update_list)
                        self.db_con.commit()

                except:
                    ex = Exception("Unexpected error saving tags")
                    raise ex

                print("placeholder: tags saved")

        self.set_tableWidget_save_pending(False)

    def set_tableWidget_save_pending(self, save_state:bool) -> None:
        """
        Sets the save_state of the main face table to the specified state if not matching the state specified
        :param save_state: True if a save is pending (i.e. needs to be saved)
        :return:
        """
        if self.tableWidget_save_pending != save_state:
            self.tableWidget_save_pending = save_state
            self.ui.PushButton_Save.setEnabled(save_state)
            self.ui.PushButton_Save.setVisible(save_state)

    def search_for_reference_faces_save(self):
        """
        Check if we should save faces that have been identified as part of a search for reference faces.  If confirmed
        then save, if discarded then proceed without save, if cancelled return False to indicate this
        :return:    False if user cancelled, Ture if otherwise
        """
        msgBox = QMessageBox()
        msgBox.setText(
            "Would you like to save the tagged faces that were tagged automatically and have not been changed (hence are still unsaved)?")
        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        ret = msgBox.exec()
        if ret == QMessageBox.Save:
            # Save requested
            self.save_added_tags()
        elif ret == QMessageBox.Cancel:
            # User cancelled
            return False
        self.tableWidget_save_pending = False
        self.save_function_tableWidget = None

        # Flag that user did not cancel.
        return True

    def get_people_tags_from_treewidget(self):
        """
        Loads a dictionary of peopletags from the treewidget
        :return:    Dictionary { <tag_id> : <tag_name> }
        """
        tree_widget_items = get_all_items(self.ui.treeWidget)
        d = dict()
        for tree_widget_item in tree_widget_items:
            tag_id = tree_widget_item.data(0, Qt.UserRole)
            tag_name = tree_widget_item.text(0)
            d[tag_id] = tag_name
        return d

    def fix_reference_images_that_were_not_properly_tagged(self):
        # Search for reference faces in untagged images and add to tableWidget
        query = """
                /* Find reference faces with no tag id and load the list of people tags for them */
                select 
                    face_id,
                    face_table.media_id,
                    media_table.full_filepath,
                    volume_table.drive_path_if_builtin,
                    tag_to_media_table.tag_id, 
                    is_reference_face,
                    is_confirmed_face,
                    exclude_from_face_search,
                    tag_table.name 
                from 
                    face_table,
                    tag_to_media_table,
                    tag_table,
                    media_table, 
                    volume_table
                where
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id AND
                    face_table.media_id = tag_to_media_table.media_id and
                    face_table.is_reference_face = 1 and
                    tag_to_media_table.tag_id = tag_table.id and
                    face_table.tag_id is null and
                    tag_table.id in
                        (
                            WITH RECURSIVE
                                under_person(id_under_person,level) AS (
                                    values(59, 0)
                                    UNION ALL
                                    SELECT tag_table.id, under_person.level+1
                                        FROM tag_table JOIN under_person ON tag_table.parent_id=under_person.id_under_person
                                        ORDER BY 2
                                )
                            SELECT id FROM under_person, tag_table where id_under_person = tag_table.id
                        )
                order by face_id;"""
        try:
            with self.db_con:
                # First get row count
                count_query = "SELECT count(*) from ({});".format(query[0:-1])
                cur = self.db_con.cursor()
                cur.execute(count_query)
                db_row = cur.fetchone()
                num_unknown_faces = db_row[0]
                tableWidget_row_count = num_unknown_faces // self.grid_cols

                self.ui.tableWidget.setRowCount(tableWidget_row_count)
                self.clear_tableWidget()

                if tableWidget_row_count:
                    # Setup progress indicator
                    progress = QtWidgets.QProgressDialog("Comparing faces, please wait ...", "Abort", 0,
                                                         num_unknown_faces)
                    progress.setWindowModality(Qt.WindowModal)
                    progress.setWindowTitle("Face Recognition")

                    # Now run the actual query and fetch the first row
                    cur.execute(query)
                    db_row = cur.fetchone()

                    face_index = 0
                    row = 0
                    col = 0

                    while db_row:
                        (
                            face_id,
                            media_id,
                            full_filepath,
                            drive_path_if_builtin,
                            tag_id,
                            is_reference_face,
                            is_confirmed_face,
                            exclude_from_face_search,
                            tag_name
                        ) = db_row

                        filename = ntpath.normpath(drive_path_if_builtin + full_filepath)
                        # Setup face widget and loop for same face id adding to combo box
                        tag_distance_list = list()
                        while db_row is not None and face_id == db_row['face_id']:
                            # tag_distance_list is a list of tuples in format (tag_id, (tag_name, distance))
                            tag_id = db_row['tag_id']
                            tag_name = db_row['name']
                            tag_distance_list.append((tag_id, (tag_name, 0)))

                            # Get next row
                            db_row = cur.fetchone()

                        cellwidget = EditImageTableCellWidget(parent=None,
                                                              face_id=face_id,
                                                              tag_distance_list=tag_distance_list,
                                                              media_id=media_id,
                                                              is_reference_face=is_reference_face,
                                                              is_confirmed_face=is_confirmed_face,
                                                              exclude_from_face_search=exclude_from_face_search,
                                                              filename=filename)

                        progress.setValue(face_index)
                        if progress.wasCanceled():
                            break
                        face_index += 1
                        # Add cell widget to table
                        if col >= self.grid_cols:
                            row += 1
                            col = 0
                        if row + 1 > self.ui.tableWidget.rowCount():
                            # Extend table if needed
                            self.ui.tableWidget.setRowCount(row + 1)

                        self.ui.tableWidget.setCellWidget(row, col, cellwidget)

                        col += 1

                    self.ui.tableWidget.resizeRowsToContents()
                    self.ui.tableWidget.resizeColumnsToContents()

        except:
            print("Unexpected fixing images that were not properly tagged")
            raise


    def search_for_reference_faces(self):

        # Load reference faces
        reference_faces = self.load_reference_faces()
        (ref_face_ids,
         ref_media_ids,
         ref_fullpaths,
         ref_drive_path_if_builtins,
         ref_tag_ids,
         is_reference_face,
         is_confirmed_face,
         exclude_from_face_search,
         ref_tag_names,
         ref_face_encodings) = zip(*reference_faces)

        # Search for reference faces in untagged images and add to tableWidget
        # Select untagged faces that are not flagged for exclusion
        query = """
                SELECT 
                    face_id, 
                    media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin,
                    tag_id,
                    is_reference_face,
                    is_confirmed_face,
                    exclude_from_face_search,
                    '' as tag_name,
                    face_encoding_blob
                FROM 
                    face_table, 
                    media_table, 
                    volume_table
                WHERE 
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id AND
                    face_table.tag_id IS NULL AND
                    (exclude_from_face_search IS NULL OR
					exclude_from_face_search  = 0)
                ORDER BY face_id;"""
        try:
            with self.db_con:
                # First get row count
                count_query = "SELECT count(*) from ({});".format(query[0:-1])
                cur = self.db_con.cursor()
                cur.execute(count_query)
                db_row = cur.fetchone()
                num_unknown_faces = db_row[0]
                tableWidget_row_count = num_unknown_faces // self.grid_cols

                self.ui.tableWidget.setRowCount(tableWidget_row_count)
                self.clear_tableWidget()
                # self.ui.tableWidget.clear()

                # Set save function and flag that we need to save.
                self.set_tableWidget_save_pending(True)
                # print (self.ui.PushButton_Save.isEnabled())
                app.processEvents()
                self.save_function_tableWidget = self.search_for_reference_faces_save
                self.tableWidget_save_pending = True

                table_widget_item_list = list()

                if tableWidget_row_count:
                    # Setup progress indicator
                    progress = QtWidgets.QProgressDialog("Comparing faces, please wait ...", "Abort", 0,
                                                         num_unknown_faces)
                    progress.setWindowModality(Qt.WindowModal)
                    progress.setWindowTitle("Face Recognition")

                    # Now run the actual query and fetch the first row
                    cur.execute(query)
                    db_row = cur.fetchone()

                    face_index = 0
                    while db_row:
                        # get list of face data for this media id
                        db_rows = list()
                        media_id = db_row['media_id']
                        while db_row and media_id == db_row['media_id']:
                            db_rows.append(db_row)
                            db_row = cur.fetchone()

                        # process rows for the next media_id
                        for this_db_row in db_rows:
                            (
                                face_id,
                                media_id,
                                full_filepath,
                                drive_path_if_builtin,
                                tag_id,
                                is_reference_face,
                                is_confirmed_face,
                                exclude_from_face_search,
                                tag_name,
                                face_encoding_blob
                            ) = this_db_row

                            unknown_face_encoding = numpy.frombuffer(bytes(face_encoding_blob))
                            filename = ntpath.normpath(drive_path_if_builtin + full_filepath)

                            # Check if this image has a set of people tags and if it does restrict face comparison to these
                            # if there are enough tags for the faces in the image
                            tag_info  = get_people_tags_for_face_id(db_con=self.db_con, face_id=face_id)
                            if tag_info and len(tag_info) >= len(db_rows):
                                # there is tag info and there's enough for the number of faces found in the media item
                                # so restrict checking to these tags
                                (source_image_tag_ids, source_image_tag_names) = tag_info
                            else:
                                source_image_tag_ids = None
                                source_image_tag_names = None
                            # Compare this face to all known faces
                            face_distances = numpy.linalg.norm(ref_face_encodings - unknown_face_encoding, axis=1)
                            d = dict()
                            for ref_tag_id, ref_tag_name, distance in zip(ref_tag_ids, ref_tag_names, face_distances):
                                if source_image_tag_ids == None or ref_tag_id in source_image_tag_ids:
                                    if ref_tag_id in d:
                                        # tag already there so only update if its distance is smaller
                                        if d[ref_tag_id][1] > distance:
                                            d[ref_tag_id] = (ref_tag_name, distance)
                                    else:
                                        # tag not there so add it
                                        d[ref_tag_id] = (ref_tag_name, distance)

                            # sort dictionary by value
                            tag_distance_list = sorted(d.items(), key=lambda kv: kv[1][1])

                            cellwidget = EditImageTableCellWidget(parent=None,
                                                                  face_id=face_id,
                                                                  tag_distance_list=tag_distance_list,
                                                                  media_id=media_id,
                                                                  is_reference_face=is_reference_face,
                                                                  is_confirmed_face=is_confirmed_face,
                                                                  exclude_from_face_search=exclude_from_face_search,
                                                                  filename=filename)
                            table_widget_item_list.append(cellwidget)
                            progress.setValue(face_index)
                            if progress.wasCanceled():
                                break

                            face_index += 1
                        if progress.wasCanceled():
                            break
        except:
            ex = Exception("Unexpected error processing images")
            raise ex

        # Now sort and add to tableWidget
        # Setup progress indicator
        tableWidget_row_count = len(table_widget_item_list) // self.grid_cols
        progress = QtWidgets.QProgressDialog("Sorting and adding faces to table, please wait ...", "Abort", 0,
                                             tableWidget_row_count)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Face Recognition")

        progress.setValue(0)
        app.processEvents()
        if table_widget_item_list:
            table_widget_item_list.sort(key=lambda x: x.tag_id if x.tag_id else 0)

            row = 0
            col = 0
            table_widget_index = 0

            for cellwidget in table_widget_item_list:
                # Add cell widget to table
                if col >= self.grid_cols:
                    progress.setValue(row)
                    if (progress.wasCanceled()):
                        break
                    row += 1
                    col = 0
                if row + 1 > self.ui.tableWidget.rowCount():
                    # Extend table if needed
                    self.ui.tableWidget.setRowCount(row + 1)

                self.ui.tableWidget.setCellWidget(row, col, cellwidget)

                col += 1

            self.ui.tableWidget.resizeRowsToContents()
            self.ui.tableWidget.resizeColumnsToContents()

    def load_reference_faces(self):
        """
        Load faces tagged as reference faces in catalog and return an list of them
        :return:  List of tupples containing reference face info:
                        face_id,
                        media_id,
                        full_filepath,
                        drive_path_if_builtin,
                        tag_id,
                        is_reference_face,
                        is_confirmed_face,
                        exclude_from_face_search,
                        tag_name,
                        face_encoding
        """
        # load reference faces
        query = """
                SELECT 
                    face_id, 
                    media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin,
                    tag_id,
                    is_reference_face,
                    is_confirmed_face,
                    exclude_from_face_search,                    
                    (select tag_table.name from tag_table where tag_table.id = face_table.tag_id) as tag_name,
                    face_encoding_blob
                FROM 
                    face_table, 
                    media_table, 
                    volume_table
                WHERE 
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id AND
                    face_table.is_reference_face != 0
                ORDER BY tag_id;        
        """
        try:
            with self.db_con:
                cur = self.db_con.cursor()
                cur.execute(query)
                rows = cur.fetchall()
                known_face_list = list()
                if rows:
                    for db_row in rows:
                        (
                            face_id,
                            media_id,
                            full_filepath,
                            drive_path_if_builtin,
                            tag_id,
                            is_reference_face,
                            is_confirmed_face,
                            exclude_from_face_search,
                            tag_name,
                            face_encoding_blob
                        ) = db_row
                        filename = ntpath.normpath(drive_path_if_builtin + full_filepath)
                        # Add the reference images we've loaded to a list
                        face_encoding = numpy.frombuffer(bytes(face_encoding_blob))
                        known_face_list.append((
                            face_id,
                            media_id,
                            full_filepath,
                            drive_path_if_builtin,
                            tag_id,
                            is_reference_face,
                            is_confirmed_face,
                            exclude_from_face_search,
                            tag_name,
                            face_encoding
                        ))

        except:
            print("Unexpected error loading reference images", sys.exc_info()[0])
            raise

        return known_face_list

    def filter_all_faces(self):
        self.load_thumbnails_to_grid(sql_query="", break_row_on_tag_change=False)

    def clear_tableWidget(self):
        """
        Clear's the table widget, asking user whether to save if appropriate.
        :return:    Returns True if user confirms action or False if user presses Cancel.
        """
        # call save if pending
        if self.tableWidget_save_pending:
            # Call the save function tat was specified
            b_exit_confirmed = self.save_function_tableWidget()
            if not b_exit_confirmed:
                return False

        self.ui.tableWidget.clearContents()

        # Return indicating operation not cancelled.
        return True

    def filter_unnamed_faces(self):
        query = """
                SELECT 
                    face_id, 
                    media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin,
                    tag_id,
                    is_reference_face,
                    is_confirmed_face,
                    exclude_from_face_search,
                    '' as tag_name
                FROM 
                    face_table, 
                    media_table, 
                    volume_table
                WHERE 
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id AND
                    face_table.tag_id IS NULL;
                """
        self.load_thumbnails_to_grid(sql_query=query, break_row_on_tag_change=False)

    def filter_named_faces(self):
        query = """
                SELECT 
                    face_id, 
                    face_table.media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin,
                    tag_id,
                    is_reference_face,
                    is_confirmed_face,
                    exclude_from_face_search,
                    (select tag_table.name from tag_table where tag_table.id = face_table.tag_id) as tag_name
                FROM 
                    face_table, 
                    media_table, 
                    volume_table,
                    metadata_date_time_table, 
                    media_to_metadata_table 
                WHERE 
                    media_table.id = face_table.media_id
                    AND media_to_metadata_table.media_id = media_table.id
                    AND media_to_metadata_table.metadata_id = metadata_date_time_table.id
                    /* AND metadata_date_time_table.description_id = 8 */
                    AND media_table.volume_id = volume_table.id
                    AND face_table.tag_id IS NOT NULL
                GROUP BY face_id
                ORDER BY tag_name, is_reference_face DESC, min(metadata_date_time_table.value);         
        """
        self.load_thumbnails_to_grid(sql_query=query, break_row_on_tag_change=True)

    def filter_reference_faces(self):
        query = """
                SELECT 
                    face_id, 
                    media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin,
                    tag_id,
                    is_reference_face,
                    is_confirmed_face,
                    exclude_from_face_search,
                    (select tag_table.name from tag_table where tag_table.id = face_table.tag_id) as tag_name
                FROM 
                    face_table, 
                    media_table, 
                    volume_table
                WHERE 
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id AND
                    face_table.is_reference_face != 0
                ORDER BY tag_id;        
        """
        self.load_thumbnails_to_grid(sql_query=query, break_row_on_tag_change=True)


    def filter_people_with_no_reference_faces(self):
        """
        Find all faces with people tags that have no reference face but have media items with that tag so that the
        user can select a relevant face tag as a reference face
        :return:
        """
        query = """
                /* Find all faces from media items with tags that do not have reference faces in face_table */
                select 
                    face_table.face_id, 
                    face_table.media_id,
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin,
                    tag_to_media_table.tag_id, 
                    is_reference_face,
                    is_confirmed_face,
                    exclude_from_face_search,
                    tag_table.name
                from 
                    face_table, 
                    tag_to_media_table, 
                    tag_table, 
                    media_table,
                    volume_table
                where
                    face_table.media_id = tag_to_media_table.media_id and
                    face_table.media_id = media_table.id and
                    tag_to_media_table.tag_id = tag_table.id and
                    media_table.volume_id = volume_table.id and
                    tag_to_media_table.tag_id in
                        /* People tags that do not have reference faces in face_table */
                        (select tag_table.id
                            from tag_to_media_table, tag_table, face_table
                            where 
                                tag_table.id = tag_to_media_table.tag_id
                                and tag_to_media_table.media_id = face_table.media_id
                                and tag_to_media_table.tag_id in
                                    (
                                        /* Find people only tags */
                                        with recursive
                                            works_for(id_wf) as 
                                            (
                                                values({})
                                                union all
                                                select tag_table.id from tag_table, works_for
                                                where tag_table.parent_id = works_for.id_wf
                                            )
                                        select id from tag_table
                                            where id in works_for 
                                    )
                            group by tag_table.id
                            having sum(face_table.is_reference_face) = 0
                        )
                order by name, is_confirmed_face desc;        
        """.format(self.people_tag_id)
        self.load_thumbnails_to_grid(sql_query=query, break_row_on_tag_change=True)

    def set_reference_faces(self):
        selection = self.ui.tableWidget.selectedIndexes()
        for model_index in selection:
            table_widget_item = self.ui.tableWidget.cellWidget(model_index.row(), model_index.column())
            if table_widget_item:
                table_widget_item.is_reference_face = True
        self.update_catalog_from_selected_faces()

    def set_confirmed_faces(self):
        selection = self.ui.tableWidget.selectedIndexes()
        progress = QtWidgets.QProgressDialog("Updating faces, please wait ...", "Abort", 0,
                                             len(selection) * 2)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Face Recognition")

        face_count = 1
        for model_index in selection:
            table_widget_item = self.ui.tableWidget.cellWidget(model_index.row(), model_index.column())
            if table_widget_item and table_widget_item.tag_id != None :
                # item has a face and the face has a tag so allow it to be flagged as confirmed
                table_widget_item.is_confirmed_face = True
            progress.setValue(face_count)
            if (progress.wasCanceled()):
                break
            face_count += 1
        self.update_catalog_from_selected_faces(progress=progress, progress_start=face_count)

    def exclude_from_face_search(self):
        selection = self.ui.tableWidget.selectedIndexes()
        for model_index in selection:
            table_widget_item = self.ui.tableWidget.cellWidget(model_index.row(), model_index.column())
            table_widget_item.exclude_from_face_search = True
        # Call remove face tags first to remove any tag_ids before saving to ensure we don't save
        # face tags that were returned a recent search that are wrong (which is why we're excluding from future
        # searches
        self.remove_face_tag_from_selected_items()
        self.update_catalog_from_selected_faces()

    def action_About(self):
        print("About")

    def queue_result_callback(self, result):
        """
        Receives a result from a worker thread which it adds to the queue for processing in the main loop
        """
        if result:
            # with QMutexLocker(self.mutex):
            #     if self.faces_added_to_queue:
            #         # Start timer
            #         self.timer.start()

            self.result_queue.put(result)

    def error_callback(self, error_info_tuple):
        """
        Receives error tuple from worker thread with contents (exctype, value, traceback.format_exc()) and
        raises an exception
        """
        error_type, error_instance, traceback = error_info_tuple
        print(error_type, error_instance, traceback)
        raise Exception("Error in worker thread")

    def thread_complete_callback(self):
        # prior thread was finished so create a new thread with next item from work queue
        if not self.face_processing_termination_requested:
            # self.dispatch_next_task_to_thread()
            self.process_results()
        myapp.ui.progressBar.setValue(
            myapp.ui.progressBar.maximum() - self.work_to_be_done_queue.qsize() - self.threadpool.activeThreadCount())

    def process_faces_worker_callback(self, filename, media_id):
        # Load an image with an unknown face
        unknown_image = load_orient_and_resize_face_rec_image(filename, myMainWindow.scaled_height_for_resized_images)

        # Find all the faces and face encodings in the unknown image
        if isinstance(unknown_image, numpy.ndarray):
            unknown_image_face_locations = face_recognition.face_locations(unknown_image, model='hog')
            unknown_image_face_encodings = face_recognition.face_encodings(unknown_image, unknown_image_face_locations)
            return (unknown_image_face_locations, unknown_image_face_encodings, filename, media_id)
        else:
            return (None, None, filename, media_id)

    def process_results(self):
        """
        Process results from the result_queue if there are any by writing them to database and updating results display list
        """
        if not self.result_queue.empty() and not self.face_processing_termination_requested:
            (unknown_image_face_locations, unknown_image_face_encodings, filename, media_id) = self.result_queue.get()
            if unknown_image_face_locations is None:
                # Value has been set to None to flag that it was not possible to scan this file
                face_location_count = 0
            else:
                face_location_count = unknown_image_face_locations.__len__()

            print("Found {} face locations in media_id {} file '{}' to be written to database.".format(
                face_location_count, media_id, filename))

            # Add these to database for each face and then flag the media_item as processed by adding a 'Face Scan Completed' tag.
            try:
                if face_location_count:
                    for (face_encoding, face_location) in zip(unknown_image_face_encodings,
                                                              unknown_image_face_locations):
                        # Write this face's data to the database
                        # Found face encoding so add to database
                        query = """
                                    INSERT INTO face_table(
                                        media_id, 
                                        scaled_image_max_height, 
                                        face_loc_top, 
                                        face_loc_right, 
                                        face_loc_bottom, 
                                        face_loc_left, 
                                        face_encoding_blob, 
                                        is_reference_face, 
                                        is_confirmed_face,
                                        exclude_from_face_search)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """
                        cur = self.db_con.cursor()
                        blob_bytes = face_encoding.tobytes()
                        cur.execute(query, (media_id,
                                            myMainWindow.scaled_height_for_resized_images,
                                            face_location[0],
                                            face_location[1],
                                            face_location[2],
                                            face_location[3],
                                            lite.Binary(blob_bytes),
                                            False,
                                            False,
                                            False
                                            )
                                    )

                        face_id = cur.lastrowid
                        print("    face_id {} in media_id {} at ({}, {}, {}, {}) added to database.".format(face_id,
                                                                                                            media_id,
                                                                                                            face_location[
                                                                                                                0],
                                                                                                            face_location[
                                                                                                                1],
                                                                                                            face_location[
                                                                                                                2],
                                                                                                            face_location[
                                                                                                                3]))

                        # Attempt to load face thumbnail to cause creation of thumbnail image in thumbnail_directory
                        im = myapp.get_qimage_face_thumbnail(face_id=face_id)

                # Flag the media_item as processed by adding a 'Face Scan Completed' tag.
                query = """
                            INSERT INTO tag_to_media_table(
                                media_id,
                                tag_id,
                                media_index)
                            VALUES (?, ?, ?)
                                """
                cur = self.db_con.cursor()
                cur.execute(query, (media_id,
                                    myMainWindow.tag_id_of_face_scan_completed_tag,
                                    0)
                            )

                self.db_con.commit()

            except:
                # unable to add face locations for this image
                ex = "Unable to add face encodings for media_id () file '()'".format(media_id, filename)
                print(ex)
                self.db_con.rollback()
                traceback.print_exc()
                raise ex

    def get_qimage_face_thumbnail(self, face_id: int):
        """
        Loads a QImage face thumbnail from cache (if found) or .png file in thumbnail_directory (if found).  If not found in these
        it creates the thumbnail from the source image in which the face was originally found and adds it to the
        cache and thumbnail_directory.  If no image is found in the face_table returns None.
        :param face_id: Adobe Elements catalog sqlite database face_table Face id to create thumbnail for
        :return:        QImage of thumbnail or None if not found
        """
        # check if face thumbnail is in thumbnail_cache
        thumbnail = myMainWindow.thumbnail_cache.get(face_id)
        if thumbnail != -1:
            # found in cache so return it.
            return thumbnail

        thumbnail = None

        # Now try to get from .png file.
        # Directory of all thumbnails between 1 and 999 inclusive is stored in a directory named <thumbnail_directory>+'0001000'
        # and 1001 to 1999 is stored in '00002000' and so on
        filespec = get_thumbnail_filename_from_face_id(face_id)
        thumbnail = QImage(filespec)
        if not thumbnail.isNull():
            # Succeeded in getting from .png so add to cache
            myMainWindow.thumbnail_cache.set(face_id, thumbnail)
        else:
            # unable to load thumbnail from .png file so assume it's not there and load from original image
            thumbnail = self.create_qimage_face_thumbnail_from_original_image(face_id, myMainWindow.thumbnail_height)
            if thumbnail:
                # add to cache
                myMainWindow.thumbnail_cache.set(face_id, thumbnail)

                # save thumbnail to .png file
                try:
                    try:
                        this_thumbnail_directory = os.path.dirname(filespec)
                        if not os.path.exists(this_thumbnail_directory):
                            os.makedirs(this_thumbnail_directory)
                    except:
                        print("Couldn't create thumbnail directory")
                        raise

                    thumbnail.save(filespec)
                except:
                    raise (Exception("Unable to save thumbnail file '()'".format(filespec)))
        return thumbnail

    def create_qimage_face_thumbnail_from_original_image(self, face_id: int, thumb_height: int = 100):
        """
        Creates a thumbnail for a specified face by finding the face in its source image
        and cropping the image.
        :param face_id: Adobe Elements catalog sqlite database face_table Face id to create thumbnail for
        :return:        QImage of thumbnail
        """
        thumbnail = None

        with self.db_con:
            query = """
                    SELECT 
                        face_id, 
                        media_id, 
                        media_table.full_filepath, 
                        volume_table.drive_path_if_builtin, 
                        scaled_image_max_height, 
                        face_loc_top, 
                        face_loc_right, 
                        face_loc_bottom, 
                        face_loc_left
                    FROM 
                        face_table, 
                        media_table, 
                        volume_table
                    WHERE 
                        face_table.face_id = {} AND
                        media_table.id = face_table.media_id AND
                        media_table.volume_id = volume_table.id;            
            """.format(face_id)
            cur = self.db_con.cursor()
            cur.execute(query)
            row = cur.fetchone()
            if row:
                (face_id,
                 media_id,
                 full_filepath,
                 drive_path_if_builtin,
                 scaled_image_max_height,
                 face_loc_top,
                 face_loc_right,
                 face_loc_bottom,
                 face_loc_left) = row

                filename = ntpath.normpath(drive_path_if_builtin + full_filepath)
                image = load_image_from_file_or_cache(filespec=filename, image_mode='RGB')
                if image:
                    # TODO  replace resize by changing height scale (no longer urgent cos of caching)

                    old_height, old_width = image.size
                    # new_height = scaled_image_max_height

                    image = resize_image(image, scaled_image_max_height)
                    # scale_factor = float(old_height) / float(new_height)
                    qtr_height = int((face_loc_bottom - face_loc_top) / 4.0)

                    face_loc_bottom = min(scaled_image_max_height, face_loc_bottom + qtr_height)
                    face_loc_top = max(0, face_loc_top - qtr_height)

                    # # Scale face location coordinates
                    # face_loc_left = int(face_loc_left * scale_factor)
                    # face_loc_top = int(face_loc_top * scale_factor)
                    # face_loc_right = int(face_loc_right * scale_factor)
                    # face_loc_bottom = int(face_loc_bottom * scale_factor)
                    box = tuple((face_loc_left, face_loc_top, face_loc_right, face_loc_bottom))
                    cropped_image = image.crop(box)
                    qimage = PIL_image_to_QImage(cropped_image)
                    # Resize image
                    thumbnail = qimage.scaledToHeight(myMainWindow.thumbnail_height)
                    # thumbnail = resize_image(image=thumbnail, new_height=myMainWindow.thumbnail_height)

                    # ba = QtCore.QByteArray()
                    # buffer = QtCore.QBuffer(ba)
                    # buffer.open(QtCore.QIODevice.WriteOnly)
                    # thumbnail.save(buffer, "PNG")
                    # print("Thumbnail '{}' serialised to len {}".format(filename, len(buffer.data())))
                    print('    Thumbnail created for face_id {} file "{}"'.format(face_id, filename))
                    return thumbnail
            return None

    def recurring_timer(self):
        expiry_time = time.time() + myMainWindow.timer_interval - 0.2
        while time.time() < expiry_time:
            self.process_results()
            app.processEvents()
            if self.face_processing_termination_requested or \
                    (
                            self.faces_added_to_queue and self.work_to_be_done_queue.empty() and self.threadpool.activeThreadCount() == 0 and self.result_queue.empty()):
                # It's time to finish
                self.face_processing_cleanup()
                return

    def face_processing_cleanup(self):
        if self.face_processing_termination_requested:
            print("Processing terminated")
            self.threadpool.waitForDone()
            self.clear_queue(self.work_to_be_done_queue)
        else:
            self.threadpool.waitForDone()
            print("Finished processing")
        # Clean up and exit
        # self.timer.stop()
        self.face_proecessing_in_progress = False
        self.face_processing_termination_requested = False
        # Enable all menus.
        self.ui.menubar.setEnabled(True)

        # self.menu_action_group.setEnabled(True)

        # myapp.ui.StartStopPushButton.setText("Start")
        # print("Start button renamed")
        # myapp.ui.StartStopPushButton.setEnabled(True)
        self.ui.progressBar.setVisible(False)
        myapp.ui.StartStopPushButton.setVisible(False)
        myapp.ui.StartStopPushButton.setEnabled(False)

    def terminate_face_processing(self):
        """
        Terminate any face processing threads that are in progress
        :return:
        """

        print("terminating")
        self.face_processing_termination_requested = True
        # myapp.ui.StartStopPushButton.setEnabled(False)
        # print ("StartStop button disabled")
        # app.processEvents()
        self.face_processing_cleanup()

    def find_faces_in_images(self):
        """
        Search all media items in adobe elements catalog that do not have the tag 'Face Scan Completed' and find
        faces in them.

        :return:
        """
        # Set the function to call if face processing is terminated
        self.ui.StartStopPushButton.clicked.connect(self.terminate_face_processing)
        # Disable all menus.
        self.ui.menubar.setEnabled(False)
        self.faces_added_to_queue = False

        # self.menu_action_group.setEnabled(False)
        self.process_faces()

    def process_faces(self):
        if self.face_proecessing_in_progress or self.face_processing_termination_requested:
            # Button has been clicked again indicating user wants to stop processing
            # Begin termination process and allow the timer to complete the work
            print("terminating")
            self.face_processing_termination_requested = True
            # myapp.ui.StartStopPushButton.setEnabled(False)
            # print ("StartStop button disabled")
            # app.processEvents()
            self.face_processing_cleanup()
            return
        print('face processing commenced')

        # Clear Queues
        self.clear_queue(self.result_queue)
        self.clear_queue(self.work_to_be_done_queue)

        self.face_proecessing_in_progress = True
        self.face_processing_termination_requested = False
        myapp.ui.StartStopPushButton.setVisible(True)
        myapp.ui.StartStopPushButton.setEnabled(True)
        app.processEvents()
        # myapp.ui.StartStopPushButton.setEnabled(False)
        with self.db_con:
            cur = self.db_con.cursor()

            # Delete all faces in the face table for media items we're about to scan for faces so that we don't get
            # duplicates if we re-scan the same media items

            # Remove thumbnails first if they exist.
            # Get details of all media items that have not been tagged with 'Face Scan Completed'.
            query = """
                    SELECT face_id FROM face_table
                        WHERE
                            face_table.media_id IN
                                (Select media_id from tag_table, tag_to_media_table, media_table
                                    where
                                        tag_to_media_table.media_id = media_table.id and
                                        tag_to_media_table.tag_id = tag_table.id and
                                        tag_table.name = 'Images for Face Tagging' and 
                                        tag_to_media_table.media_id NOT IN
                                            (select media_id from tag_to_media_table, tag_table
                                                where
                                                    tag_to_media_table.tag_id = tag_table.id and
                                                    tag_table.name = 'Face Scan Completed'));
                            """

            cur.execute(query)
            rows = cur.fetchall()
            # Remove thumbnails
            for row in rows:
                face_id = row[0]
                delete_face_thumbnail_if_it_exists(face_id)

            query = """
                    DELETE FROM face_table
                        WHERE
                            face_table.media_id IN
                                (Select media_id from tag_table, tag_to_media_table, media_table
                                    where
                                        tag_to_media_table.media_id = media_table.id and
                                        tag_to_media_table.tag_id = tag_table.id and
                                        tag_table.name = 'Images for Face Tagging' and 
                                        tag_to_media_table.media_id NOT IN
                                            (select media_id from tag_to_media_table, tag_table
                                                where
                                                    tag_to_media_table.tag_id = tag_table.id and
                                                    tag_table.name = 'Face Scan Completed'));
                            """
            cur.execute(query)

            # Get details of all media items that have not been tagged with 'Face Scan Completed'.
            query = """
                Select media_id, full_filepath, drive_path_if_builtin, tag_id from tag_table, tag_to_media_table, media_table, volume_table
                    where
                        media_table.volume_id = volume_table.id and
                        tag_to_media_table.media_id = media_table.id and
						tag_to_media_table.tag_id = tag_table.id and
						tag_table.name = 'Images for Face Tagging' and 
						tag_to_media_table.media_id not in
							(select media_id from tag_to_media_table, tag_table
								where
									tag_to_media_table.tag_id = tag_table.id and
									tag_table.name = 'Face Scan Completed');
                """

            cur.execute(query)
            rows = cur.fetchall()

            if not rows:
                # no rows to process so exit ... before we even start!
                app.processEvents()
                self.face_proecessing_in_progress = False
                self.face_processing_termination_requested = False
                myapp.ui.StartStopPushButton.setVisible(False)
                myapp.ui.StartStopPushButton.setEnabled(False)
                myapp.ui.menubar.setEnabled(True)
                return

            # Move all of the rows to a work_to_be_done_queue
            for row in rows:
                media_id = row[0]
                full_filepath = row[1]
                drive_path_if_builtin = row[2]
                filename = ntpath.normpath(drive_path_if_builtin + full_filepath)
                self.work_to_be_done_queue.put((filename, media_id))

            # No longer needed now transferred to queue.
            rows = None
            cur = None

            myapp.ui.progressBar.setMaximum(self.work_to_be_done_queue.qsize())
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setVisible(True)

            # call a dispatch_work fn while there are still threads left.
            while (not self.work_to_be_done_queue.empty() or self.threadpool.activeThreadCount() != 0):
                app.processEvents()
                if self.face_processing_termination_requested:
                    # Button has been clicked again indicating user wants to stop processing
                    # Begin termination process and allow the timer to complete the work
                    print("terminating")
                    self.face_processing_termination_requested = True
                    # myapp.ui.StartStopPushButton.setEnabled(False)
                    # print("StartStop button disabled")
                    self.face_processing_cleanup()
                    return
                else:
                    # Whilst spare threads, create threads
                    if self.threadpool.activeThreadCount() <= self.max_thread_count:
                        self.dispatch_next_task_to_thread()

            self.face_processing_cleanup()

            # Now that we've dipatched enough work to exhaust the threadpool further threadpool additions will
            # be maintained when each thread finishes so process results while there are some

            # get ready to start timer as soon as first item is added to the queue.
            # self.timer = QTimer()
            # self.timer.setInterval(myMainWindow.timer_interval)
            # self.timer.timeout.connect(self.recurring_timer)

            # while not self.work_to_be_done_queue.empty() or self.threadpool.activeThreadCount() != 0 or not self.result_queue.empty():
            #     # keep going while work to be dispatched or work to befinished or results to be processed
            #     if self.terminate_face_processing:
            #         self.threadpool.waitForDone()
            #         self.clear_queue(self.work_to_be_done_queue)
            #         break
            #     self.process_results()
            #     time.sleep(0.02)  # sleep 20 ms
            #     # Allow GUI events to continue to be processed
            #     app.processEvents()
            # print("Finished processing")
            # self.face_proecessing_in_progress = False
            # self.terminate_face_processing = False
            # myapp.ui.StartStopPushButton.setText("Start")
            # myapp.ui.StartStopPushButton.setEnabled(True)
            # # myapp.ui.StartStopPushButton.setEnabled(True)
            # self.ui.progressBar.setVisible(False)

    def clear_queue(self, the_queue: queue.Queue):
        if the_queue:
            while not the_queue.empty():
                the_queue.get()

    # # @pyqtSlot()
    # def onPgDnShortcutTriggered(self):
    #     print("event triggered")
    #
    # def keyPressEvent(self, event):
    #     key = event.key()
    #     if key == Qt.Key_PageDown or key == Qt.Key_D:
    #         self.grid_start_image += self.grid_num_images
    #         self.disp_thumbnail_grid()
    #     elif key == Qt.Key_PageUp or key == Qt.Key_U:
    #         self.grid_start_image -= self.grid_num_images
    #         if self.grid_start_image < 1:
    #             self.grid_start_image = 1
    #         self.disp_thumbnail_grid()

    def scan_unknown_faces_for_clusters(self):
        """
        Use Chinese whispers
        Algorithm adapted from Li Yuan https://blog.csdn.net/LIYUAN123ZHOUHUI/article/details/70312716
        """

        retval = self.clear_tableWidget()
        if retval == False:
            # user pressed cancel so exit
            return

        import chinese_whispers as cw
        # Load face data for all unknown faces from database
        (face_ids, media_ids, tag_ids, filenames, face_encodings) = load_data_from_face_table(db_con=self.db_con)

        # Setup progress indicator
        progress = QtWidgets.QProgressDialog("Grouping faces, please wait ...", "Abort", 0,
                                             len(face_ids))
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Face Recognition")

        face_dict = dict(list(zip(face_ids,list(zip(media_ids, tag_ids, filenames, face_encodings)))))

        # return sorted clusters from largest to smallest
        #todo Finish this
        # Create list of clusters.  Each cluster is a list of face_ids
        sorted_clusters = cw.chinese_whispers(face_ids, face_encodings)

        # Display clusters in tableWidget
        self.ui.tableWidget.setRowCount((len(face_ids) // self.grid_cols) + len(sorted_clusters))

        row = 0
        col = 0
        table_widget_index = 0
        face_count = 0

        for cluster in sorted_clusters:
            for face_id in cluster:
                (media_id, tag_id, filename, face_encoding) = face_dict[face_id]

                cellwidget = EditImageTableCellWidget(parent=None,
                                                      face_id=face_id,
                                                      tag_id=None,
                                                      media_id=media_id,
                                                      is_reference_face=False,
                                                      is_confirmed_face=False,
                                                      exclude_from_face_search=False,
                                                      filename=filename)

                # Add cell widget to table
                progress.setValue(face_count)
                if (progress.wasCanceled()):
                    break
                face_count += 1
                if col >= self.grid_cols:
                    row += 1
                    col = 0
                if row + 1 > self.ui.tableWidget.rowCount():
                    # Extend table if needed
                    self.ui.tableWidget.setRowCount(row + 1)

                self.ui.tableWidget.setCellWidget(row, col, cellwidget)
            # End of cluster so skip to next row
            row += 1
            col = 0

    def scan_unknown_faces_for_clusters_dlib(self):
        """
        Use Chinese whispers
        Algorithm adapted from Li Yuan https://blog.csdn.net/LIYUAN123ZHOUHUI/article/details/70312716
        """

        retval = self.clear_tableWidget()
        if retval == False:
            # user pressed cancel so exit
            return

        #  from dlib import chinese_whispers_clustering

        # Load face data for all unknown faces from database
        (face_ids, media_ids, tag_ids, filenames, face_encodings) = load_data_from_face_table(db_con=self.db_con)

        # Setup progress indicator
        progress = QtWidgets.QProgressDialog("Grouping faces, please wait ...", "Abort", 0,
                                             len(face_ids))
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Face Recognition")

        # face_dict = dict(list(zip(face_ids,list(zip(media_ids, tag_ids, filenames, face_encodings)))))

        # return sorted clusters from largest to smallest
        #todo Face clustering using scan_unknown_faces_for_clusters_dlib():not working
        # Create list of clusters.  Each cluster is a list of face_ids
        clusters = dlib.chinese_whispers_clustering(face_encodings, 0.5)

        # Display clusters in tableWidget
        self.ui.tableWidget.setRowCount((len(face_ids) // self.grid_cols) + len(clusters))

        # row = 0
        # col = 0
        # table_widget_index = 0
        # face_count = 0
        #
        # for cluster in clusters:
        #     for face_id in cluster:
        #         (media_id, tag_id, filename, face_encoding) = face_dict[face_id]
        #
        #         cellwidget = EditImageTableCellWidget(parent=None,
        #                                               face_id=face_id,
        #                                               tag_id=None,
        #                                               media_id=media_id,
        #                                               is_reference_face=False,
        #                                               is_confirmed_face=False,
        #                                               filename=filename)
        #
        #         # Add cell widget to table
        #         progress.setValue(face_count)
        #         if (progress.wasCanceled()):
        #             break
        #         face_count += 1
        #         if col >= self.grid_cols:
        #             row += 1
        #             col = 0
        #         if row + 1 > self.ui.tableWidget.rowCount():
        #             # Extend table if needed
        #             self.ui.tableWidget.setRowCount(row + 1)
        #
        #         self.ui.tableWidget.setCellWidget(row, col, cellwidget)
        #     # End of cluster so skip to next row
        #     row += 1
        #     col = 0


    def load_thumbnails_to_grid(self, break_row_on_tag_change:bool = True, sql_query:str =""):
        """
        Display a grid of face thumbnails starting from self.grid_start_image
        :param break_row_on_tag_change  True if you want the tableWidget to take a new row each time a tag name changes
        :param sql_query:
        :return:
        """
        # self.grid_layout = QtWidgets.QGridLayout(self.ui.graphicsView)

        with self.db_con:
            # query = "select face_table.face_id from face_table;"
            if sql_query:
                query = sql_query
            else:
                query = """
                        SELECT 
                            face_id, 
                            media_id, 
                            media_table.full_filepath, 
                            volume_table.drive_path_if_builtin,
                            tag_id, 
                            is_reference_face,
                            is_confirmed_face,
                            exclude_from_face_search,
                            (select tag_table.name from tag_table where tag_table.id = face_table.tag_id) as tag_name
                        FROM 
                            face_table, 
                            media_table, 
                            volume_table
                        WHERE 
                            media_table.id = face_table.media_id AND
                            media_table.volume_id = volume_table.id;
                """
            # query = """
            #         SELECT
            #             face_id,
            #             media_id,
            #             media_table.full_filepath,
            #             volume_table.drive_path_if_builtin,
            #             (select tag_table.name from tag_table where tag_table.id = face_table.tag_id) as tag_name
            #         FROM
            #             face_table,
            #             media_table,
            #             volume_table
            #         WHERE
            #             media_table.id = face_table.media_id AND
            #             media_table.volume_id = volume_table.id;
            # """

            cur = self.db_con.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            row = 0
            col = 0
            if rows:
                num_rows = rows.__len__() // self.grid_cols
                if break_row_on_tag_change:
                    # add rows if we want row breaks
                    num_rows += len(self.get_people_tags_from_treewidget())
                self.ui.tableWidget.setRowCount(num_rows)
                # Note that clear_tableWidget() also saves the current table data if necessary.
                if not self.clear_tableWidget():
                    # operation cancelled by user
                    return
                progress = QtWidgets.QProgressDialog("Reading thumbnails, please wait ...", "Abort", 0,
                                                     num_rows)
                progress.setWindowModality(Qt.WindowModal)
                progress.setWindowTitle("Face Recognition")
                tag_id = rows[0]['tag_id']
                for db_row in rows:
                    if break_row_on_tag_change and db_row['tag_id'] != tag_id:
                        # skip to next row
                        row += 1
                        col = 0
                    (
                        face_id,
                        media_id,
                        full_filepath,
                        drive_path_if_builtin,
                        tag_id,
                        is_reference_face,
                        is_confirmed_face,
                        exclude_from_face_search,
                        tag_name
                    ) = db_row
                    filename = ntpath.normpath(drive_path_if_builtin + full_filepath)

                    # Set values for this cell
                    cellwidget = EditImageTableCellWidget(parent=None,
                                                          face_id=face_id,
                                                          tag_id=tag_id,
                                                          tag_name=tag_name,
                                                          media_id=media_id,
                                                          is_reference_face=is_reference_face,
                                                          is_confirmed_face=is_confirmed_face,
                                                          exclude_from_face_search=exclude_from_face_search,
                                                          filename=filename)
                    # qimage = myapp.get_qimage_face_thumbnail(face_id=face_id)
                    # pix_image = QtGui.QPixmap(qimage)
                    # cellwidget.thumb_qlabel.setPixmap(pix_image)
                    # # tag_name = 'Dummy'
                    # if tag_name:
                    #     # cellwidget.thumb_qcombo.addItem(tag_name)
                    #     cellwidget.thumb_qcombo.setText(tag_name)
                    #
                    # cellwidget.face_id = int(face_id)
                    # cellwidget.media_id = int(media_id)
                    # cellwidget.is_reference_face = bool(is_reference_face)
                    # if tag_id:
                    #     cellwidget.tag_id = int(tag_id)
                    # else:
                    #     cellwidget.tag_id = None
                    # status_tip = "Face id: {}   Media id: {}  Media Filename: {}".format(face_id, media_id, filename)
                    # cellwidget.setStatusTip(status_tip)

                    progress.setValue(row)
                    if (progress.wasCanceled()):
                        break
                    # Add cell widget to table
                    if col >= self.grid_cols:
                        row += 1
                        col = 0
                    if row + 1 > self.ui.tableWidget.rowCount():
                        # Extend table if needed
                        self.ui.tableWidget.setRowCount(row + 1)

                    self.ui.tableWidget.setCellWidget(row, col, cellwidget)

                    # table_item = QTableWidgetItem()
                    # table_item.setData(Qt.StatusTipRole, "Face ID: {} Media ID: {} Filename: {}".format(face_id, media_id, filename))
                    # d = dict([('face_id', face_id), ('media_id', media_id), ('filename', filename)])
                    # table_item.setData(QtCore.Qt.DecorationRole, pix_image)
                    # self.ui.tableWidget.setItem(row, col, table_item)
                    col += 1

                self.ui.tableWidget.resizeRowsToContents()
                self.ui.tableWidget.resizeColumnsToContents()
                # self.show()
                # See whether this makes QTableWidget more efficient
                hdr = self.ui.tableWidget.horizontalHeader()
                hdr.setResizeContentsPrecision(100)

    def remove_face_tag_from_selected_items(self):
        """
        Remove the tag in the face_table of the selected faces.
        :return:
        """
        # Get selected faces.
        selection = self.ui.tableWidget.selectedIndexes()
        face_id_list = list()
        for model_index in selection:
            row = model_index.row()
            column = model_index.column()
            table_widget_item = self.ui.tableWidget.cellWidget(row, column)
            if table_widget_item:
                # thare is a table_widget_item for this tableWidget cell
                # If this is a combo box then change it to a qlabel since it now has only one value of ""
                if type(table_widget_item.thumb_qcombo) is QComboBox:
                    table_widget_item.replace_thumb_qcombo_as_qlabel()

                # Update this widget's tag to nothing
                table_widget_item.thumb_qcombo.setText("")
                table_widget_item.tag_id = None
                table_widget_item.thumb_qcombo_tag_ids = None

                # Valid widget found in this cell location so add face_id list for it's tag to be remvoed from face_table
                face_id_list.append((int(table_widget_item.face_id),))
                table_widget_item.is_reference_face = False
                table_widget_item.is_confirmed_face = False
                # table_widget_item.exclude_from_face_search = False
                table_widget_item.set_thumb_qcombo_color()

        # Remove faces from catalog
        try:
            query = """
                UPDATE face_table
                SET 
                    tag_id = NULL,
                    is_reference_face = 0,
                    is_confirmed_face = 0,
                    exclude_from_face_search = 0
                WHERE
                    face_id = ?;            
            """

            cur = self.db_con.cursor()
            cur.executemany(query, face_id_list)
            self.db_con.commit()

        except:
            print("Unexpected error attempting to remove face tags.")
            raise

    def update_catalog_from_selected_faces(self, progress:QtWidgets.QProgressDialog=None, progress_start:int=0):
        """
        Updates that face_table and tag_to_media_table with the tag_id, is_reference_face and is_confirmed_face fields
        of each selected widget in the tableWidget
        :return:
        """

        # Get selected faces.
        selected_faces = self.ui.tableWidget.selectedIndexes()
        # Setup progress dialog if not already done.
        if not progress:
            progress = QtWidgets.QProgressDialog("Updating catalog from faces, please wait ...", "Abort", 0,
                                                 len(selected_faces))
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Face Recognition")
            face_count = 1
        else:
            face_count = progress_start
        tag_to_media_table_update_set = set()
        face_table_update_list = list()

        # for each selected face (and its associated media_id and tag_id)
        for model_index in selected_faces:
            row = model_index.row()
            column = model_index.column()
            table_widget_item = self.ui.tableWidget.cellWidget(row, column)
            if table_widget_item:
                # table widget item present
                if type(table_widget_item.thumb_qcombo) == QComboBox:
                    # It's a combo so get its tag_id from the list
                    table_widget_item.tag_id = table_widget_item.thumb_qcombo_tag_ids[table_widget_item.thumb_qcombo.currentIndex()]

                # Add data to face_id list for updating face_table later
                face_table_update_list.append((table_widget_item.tag_id,
                                               table_widget_item.is_reference_face,
                                               table_widget_item.is_confirmed_face,
                                               table_widget_item.exclude_from_face_search,
                                               table_widget_item.face_id
                                               ))

                # Find  media_ids (which have a 1:1 relationship with this face_id) that need to have this tag added.
                # Use "SELECT" first to find any existing values and avoid replacting (or duplicating) them rather than
                # INSERT OR REPLACE sql command in order to preserve any existing media_index values
                try:
                    with self.db_con:

                        query = """
                            SELECT media_id FROM tag_to_media_table
                                WHERE
                                    media_id = ? AND tag_id = ?;       
                        """
                        cur = self.db_con.cursor()
                        media_and_tag_id = (table_widget_item.media_id, table_widget_item.tag_id)
                        cur.execute(query, media_and_tag_id)
                        row = cur.fetchone()

                        if not row and media_and_tag_id[1] and media_and_tag_id not in tag_to_media_table_update_set:
                            # Didn't find this media_id and tag_id combo and tag_id is not None and not already in update
                            # set so add to set so it will be inserted
                            tag_to_media_table_update_set.add(media_and_tag_id)

                        progress.setValue(face_count)
                        if (progress.wasCanceled()):
                            break
                        face_count += 1

                except:
                    print("Unexpected error checking whether media_id tags need updating.")
                    raise

        # Now update face_table and tag_to_mdeia_table
        try:
            with self.db_con:
                if face_table_update_list:
                    # Update face_ids to new tag.
                    query = """
                        UPDATE face_table
                        SET 
                            tag_id = ?,
                            is_reference_face = ?,
                            is_confirmed_face = ?,
                            exclude_from_face_search = ?
                        WHERE
                            face_id = ?;            
                    """
                    cur = self.db_con.cursor()
                    cur.executemany(query, face_table_update_list)

                    if tag_to_media_table_update_set:
                        # Update media_ids to new tag
                        query = """
                            INSERT INTO tag_to_media_table (media_id, tag_id, media_index)
                            VALUES(?, ?, 0);            
                        """
                        cur = self.db_con.cursor()
                        cur.executemany(query, tag_to_media_table_update_set)

        except:
            print("Unexpected error trying to update face_table or media_table with selected face data.")
            raise

    def set_face_tag_of_selected_widget_items_to_tag_id(self, tag_id:int, tag_name:str):
        """
        Update the tags of selected widgetTable items/cells to the specified tag_id and tag_name.
        NOTE: DOES NOT write these changes to the catalog DB - just updates the widgets. To write to
        disk use update_catalog_from_selected_faces()
        :param tag_id:      tag_id to set selected items to.  If None, also slears the confirmed and reference
                            face attributes of selected widgetTable items
        :param tag_name:    tag_name / face name to change to
        :return:
        """
        # Get selected faces and update the tag_id in each widget item to the one selected in the treeWidget.
        selected_faces = self.ui.tableWidget.selectedIndexes()

        for model_index in selected_faces:
            row = model_index.row()
            column = model_index.column()
            table_widget_item = self.ui.tableWidget.cellWidget(row, column)
            if table_widget_item:
                # Valid widget/face found in this cell location that needs its tag updated
                # Update this widget's tag to the new value
                # If this is a combo vs a label then change this combo to a label and set to a single value
                if type(table_widget_item.thumb_qcombo) == QComboBox:
                    table_widget_item.replace_thumb_qcombo_as_qlabel()

                table_widget_item.thumb_qcombo.setText(tag_name)

                # Change its tag_id
                table_widget_item.tag_id = tag_id

                if not tag_id:
                    # Clearing this face so clear reference and confirmed attributes
                    table_widget_item.is_confirmed_face = False
                    table_widget_item.is_reference_face = False
                    # table_widget_item.exclude_from_face_search = False

    def change_face_tag_from_tree_widget(self):
        """
        Change tags in the face_table of the selected faces to the tag selected in the TreeWidget
        :return:
        """
        # Get new face tag name from TreeWidget
        tree_widget_items = self.ui.treeWidget.selectedItems()
        if not tree_widget_items or tree_widget_items.__len__() != 1:
            msgBox = QMessageBox()
            msgBox.setText("Please select a single tag to add to the face.")
            msgBox.exec()
            return

        # Only one tag selected so get it
        tree_widget_item = tree_widget_items[0]
        tree_widget_tag_name = tree_widget_item.text(0)
        tree_widget_tag_id = tree_widget_item.data(0, Qt.UserRole)

        # tag_id should be non-zero
        assert tree_widget_tag_id

        # update selected face widgets to this tag
        self.set_face_tag_of_selected_widget_items_to_tag_id(tree_widget_tag_id, tree_widget_tag_name)

        # Write changes in to selected face widgets to the db catalog
        self.update_catalog_from_selected_faces()


    def action_display_image(self):
        tableCellWidget = self.ui.tableWidget.cellWidget(self.ui.tableWidget.currentRow(),
                                                         self.ui.tableWidget.currentColumn())
        if tableCellWidget:
            display_source_image_with_face_rectangles(face_id=tableCellWidget.face_id, db_con=myapp.db_con)

    def cellDoubleClicked(self, row: int, col: int):
        # table_item = self.ui.tableWidget.item(row, col)
        # item_data = table_item.data(Qt.UserRole)
        # print (item_data['filename'])
        # print(item_data)

        pass
        # tableCellWidget = self.ui.tableWidget.cellWidget(row, col)
        # display_source_image_with_face_rectangles(face_id=tableCellWidget.face_id, db_con=self.db_con)

    def dispatch_next_task_to_thread(self):
        """
        Checks the work_to_be_done_queue and if there is any dispatches next task to a worker thread if there is one spare
        """
        if not self.face_processing_termination_requested:
            if not self.work_to_be_done_queue.empty() and self.threadpool.activeThreadCount() <= self.max_thread_count:
                # Pass the function to execute
                filename, media_id = self.work_to_be_done_queue.get()
                worker = Worker(self.process_faces_worker_callback, filename,
                                media_id)  # Any other args, kwargs are passed to the run function
                worker.signals.result.connect(self.queue_result_callback)
                worker.signals.finished.connect(self.thread_complete_callback)
                # worker.signals.progress.connect(self.progress_fn)
                worker.signals.error.connect(self.error_callback)

                # Execute
                self.threadpool.start(worker)

    def delete_selected_faces(self):
        """
        Deletes selected faces in tableWidget from Elements catalog face_table
        :return:
        """
        # Get selected faces.
        selection = self.ui.tableWidget.selectedIndexes()
        face_id_list = list()
        table_widget_item_locations = list()
        for model_index in selection:
            row = model_index.row()
            column = model_index.column()
            table_widget_item = self.ui.tableWidget.cellWidget(row, column)
            if table_widget_item:
                # Valid widget found in this cell location so add to list
                face_id_list.append((int(table_widget_item.face_id),))
                table_widget_item_locations.append((row, column))

        # Remove faces from catalog
        try:
            query = """
                DELETE FROM face_table
                WHERE
                    face_id = ?;         
            """
            cur = self.db_con.cursor()
            cur.executemany(query, face_id_list)
            self.db_con.commit()

            # Remove faces from TableWidget
            for location in table_widget_item_locations:
                (row, column) = location
                self.ui.tableWidget.removeCellWidget(row, column)

            # remove thumbnails
            for face_id in face_id_list:
                delete_face_thumbnail_if_it_exists(face_id[0])

        except:
            print("Unexpected error attempting to delete selected faces.")
            raise

    def populate_tree_widget(self):
        """
        Adds person data to the tree widget on the main form
        :return:
        """
        with self.db_con:
            # Note that 59 is the id of the "Person" tag in tag_table
            query = """
                    WITH RECURSIVE
                        under_person(id_under_person,level) AS (
                            VALUES({},0)
                            UNION ALL
                            SELECT tag_table.id, under_person.level+1
                                FROM tag_table JOIN under_person ON tag_table.parent_id=under_person.id_under_person
                                ORDER BY 2
                        )
                    SELECT level, id, name, parent_id FROM under_person, tag_table where id_under_person = tag_table.id;    
             """.format(self.people_tag_id)
            cur = self.db_con.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            if rows:
                tw_dict = dict()
                tree_widget = self.ui.treeWidget
                tree_widget.setColumnCount(1)
                tree_widget.setHeaderLabels(["People Tag List"])

                for row in rows:
                    (
                        level,
                        id,
                        name,
                        parent_id
                    ) = row
                    # Find parent QTreeWidgetItem
                    try:
                        parent = tw_dict[parent_id]
                    except KeyError:
                        # Key not present so must be a parent
                        parent = tree_widget

                    tree_widget_item = QTreeWidgetItem(parent)
                    tree_widget_item.setText(0, name)
                    # Add tag id as data so that we can easily get the tag_id for each tree item
                    tree_widget_item.setData(0, Qt.UserRole, id)
                    tw_dict[id] = tree_widget_item
                tree_widget.sortByColumn(0,Qt.AscendingOrder)
                tree_widget.setSortingEnabled(True)

                # update list of items
                self.tree_widget_item_list = get_all_items(self.ui.treeWidget)


def delete_face_thumbnail_if_it_exists(face_id: int):
    """
    Look in relevant %localappdata%\face_rec\thumbnails subdirectory for thumbnail with specified face_id and
    if it exists, delete it.
    :param face_id: face_id of thumbnail to delete if it's there
    :return:        True if deleted, False if not.
    """
    thumb_filespec = get_thumbnail_filename_from_face_id(face_id)
    if os.path.exists(thumb_filespec):
        try:
            os.remove(thumb_filespec)
            return True

        except Exception as e:
            print ("Unable to delete thumbnail '{}'.".format(thumb_filespec))
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)

            return False
    else:
        return False


def display_source_image_with_face_rectangles(face_id: int, db_con: lite.Connection):
    """
    Loads an image and draws face rectangles around it based on faces identfied and recorded in the face_table
    :param db_oon:  Sqlite customised adobe elements catalog database connection
    :param face_id:
    :return:
    """
    with db_con:
        query = """
                SELECT 
                    face_id, 
                    media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin, 
                    scaled_image_max_height, 
                    face_loc_top, 
                    face_loc_right, 
                    face_loc_bottom, 
                    face_loc_left,
                    tag_id
                FROM 
                    face_table, 
                    media_table, 
                    volume_table
                WHERE 
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id AND
                    face_table.media_id =
                        (SELECT face_table.media_id FROM face_table WHERE face_table.face_id = ?);          
        """
        cur = db_con.cursor()
        cur.execute(query, (face_id,))
        rows = cur.fetchall()
        if rows:
            row = rows[0]
            # face_id = row[0]
            # media_id = row[1]
            full_filepath = row[2]
            drive_path_if_builtin = row[3]

            filename = ntpath.normpath(drive_path_if_builtin + full_filepath)
            image = load_image_from_file_or_cache(filespec=filename, image_mode='RGB',
                                                  new_height=myMainWindow.scaled_height_for_resized_images)

            draw = ImageDraw.Draw(image)
            for row in rows:
                (
                    this_face_id,
                    media_id,
                    full_filepath,
                    drive_path_if_builtin,
                    scaled_image_max_height,
                    face_loc_top,
                    face_loc_right,
                    face_loc_bottom,
                    face_loc_left,
                    tag_id
                ) = row
                if tag_id:
                    tag_name = AEL.FindTagName(db_con, tag_id)
                else:
                    tag_name = ''
                name = ("Face ID {}: {}").format(this_face_id, tag_name)

                # Draw a box around the face using the Pillow module
                qtr_height = int((face_loc_bottom - face_loc_top) / 4.0)

                face_loc_bottom = min(scaled_image_max_height, face_loc_bottom + qtr_height)

                face_loc_top = max(0, face_loc_top - qtr_height)
                if face_id == this_face_id:
                    # set this face_id frame to red
                    color = (255, 0, 0)
                    # create blow up of this face in top right corner
                    # get new cut out of this face
                    # todo image within image
                    full_image = load_image_from_file_or_cache(filename, image_mode='RGB', new_height=0)
                    # full_image = PIL.Image.open(filename)
                    cut_out_image = full_image.copy()
                    scale_x = full_image.width / image.width
                    scale_y = full_image.height / image.height
                    box = tuple((int(face_loc_left * scale_x),
                                 int(face_loc_top * scale_y),
                                 int(face_loc_right * scale_x),
                                 int(face_loc_bottom * scale_y))
                                )
                    cut_out_image = cut_out_image.crop(box)
                    cut_out_image = resize_image(cut_out_image, new_height=int(image.height / 3), scale_up=True)
                    position = ((image.width - cut_out_image.width), 0)
                    image.paste(cut_out_image, position)
                else:
                    # set others to blue
                    color = (0, 0, 255)
                draw.rectangle(
                    ((face_loc_left, face_loc_top), (face_loc_right, face_loc_bottom)),
                    outline=color)

                # Draw a label with a name below the face
                text_width, text_height = draw.textsize(name)
                draw.rectangle(((face_loc_left, face_loc_bottom - text_height - 10),
                                (face_loc_right, face_loc_bottom)), fill=color, outline=color)
                draw.text((face_loc_left + 6, face_loc_bottom - text_height - 5), name,
                          fill=(255, 255, 255, 255))

            d = QtWidgets.QDialog(myapp, Qt.Dialog)
            title = "Image file '{!r}'".format(os.path.normpath(filename))
            d.setWindowTitle(title)
            d.setWindowModality(Qt.ApplicationModal)
            # d.setWindowState(Qt.WindowFullScreen)
            label = QtWidgets.QLabel(d)
            # image = resize_image(image, d.height())
            qimage = ImageQt.ImageQt(image)

            qpix = QtGui.QPixmap.fromImage(qimage)
            d.resize(qpix.width(), qpix.height())

            label.setPixmap(qpix)

            # Remove the drawing library from memory as per the Pillow docs
            del draw

            d.exec_()


def load_data_from_face_table(db_con: lite.Connection, query: str = None, field_list: str = ['face_id', 'media_id', 'tag_id', 'filename', 'face_encoding_blob']):
    """
    Loads face_table data for the specified query.  Default query where query = None
    is to return data for all untagged faces.  Note that face_encoding_blob is converted to a numpy buffer and that
    filename is created based on concatenation of full_filepath and drive_path_if_builtin fields.
    Returns specified fields in field_list as list of lists with default
    field list returning:
        [face_ids, media_ids, tag_ids, filenames, face_encodings].
    :param face_id: Face id for whcih source image details are to be retrieved
    :param db_oon:  Sqlite customised adobe elements catalog database connection
    :return:        tuple of lists (face_ids, face_encodings).
    """
    with db_con:
        if query == None:
            #todo NOTE query limited to 200 ROWS
            query = """
               SELECT 
                    face_id, 
                    media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin, 
                    scaled_image_max_height, 
                    face_loc_top, 
                    face_loc_right, 
                    face_loc_bottom, 
                    face_loc_left,
                    face_encoding_blob,                    
                    tag_id
                FROM 
                    face_table, 
                    media_table, 
                    volume_table
                WHERE 
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id AND 
                    tag_id IS NULL
                LIMIT 200;
            """
        try:
            cur = db_con.cursor()
            cur.execute(query)
            row = cur.fetchone()
            list_of_val_lists = [[] for x in range(len(field_list))]
            field_zip = list(zip(field_list, list_of_val_lists))
            while row:
                # (face_id, face_encoding_blob) = row
                for (field_name, value_list) in field_zip:
                    if field_name == 'filename':
                        field_val = ntpath.normpath(row['drive_path_if_builtin'] + row['full_filepath'])
                    elif field_name == 'face_encoding_blob':
                        field_val = numpy.frombuffer(bytes(row['face_encoding_blob']))
                    else:
                        field_val = row[field_name]
                    value_list.append(field_val)
                # Get next row
                row = cur.fetchone()

        except Exception as e:
            raise e

        return list_of_val_lists


def get_media_item_details_for_face_id(face_id: int, db_con: lite.Connection):
    """
    Loads the row details of a media item image given a face_id.  Returns a dictionary or None if not found.
    :param face_id: Face id for whcih source image details are to be retrieved
    :param db_oon:  Sqlite customised adobe elements catalog database connection
    :return:        dictionary with following keys:
                        face_id,
                        media_id,
                        filename
    """
    with db_con:
        # query = "select face_table.face_id from face_table;"
        query = """
                SELECT 
                    face_table.media_id, 
                    media_table.full_filepath, 
                    volume_table.drive_path_if_builtin 
                FROM 
                    face_table,
                    media_table,
                    volume_table
                WHERE face_table.face_id = ? AND
                    media_table.id = face_table.media_id AND
                    media_table.volume_id = volume_table.id;       
        """
        try:
            cur = db_con.cursor()
            cur.execute(query, (face_id,))
            row = cur.fetchone()

        except Exception as e:
            raise e

        if not row:
            return None

        (media_id, full_filepath, drive_path_if_builtin) = row
        filename = ntpath.normpath(drive_path_if_builtin + full_filepath)
        d = {'face_id': face_id, 'media_id': media_id, 'filename': filename}

        return d


def get_people_tags_for_face_id(db_con: lite.Connection, face_id: int):
    """
    Returns a list of people tag_ids (i.e. only descendents of the People tag) for the specified face_id
    :param db_oon:                  Sqlite customised adobe elements catalog database connection
    :param face_id:                 int face_id to look for tag_ids for associated with the face_id's originating
                                    media item
    :return:                        Tuple contianing, for this face
                                        ( <tag_id_list>, <face_id_list>)
    """
    with db_con:
        query = """
                SELECT
                    tag_to_media_table.tag_id,
                    tag_table.name
                FROM 
                    face_table, 
                    tag_to_media_table,
                    tag_table
                WHERE
                    face_table.face_id = ? AND 
                    tag_to_media_table.tag_id = tag_table.id AND
                    tag_to_media_table.media_id = face_table.media_id
                    AND (SELECT tag_table.id FROM tag_table WHERE name = 'People') IN 
                        (WITH RECURSIVE
                                parent_of(id, parent_id) AS
                                    (SELECT id, parent_id FROM tag_table),
                                ancestor_of_person(id) AS
                                    (SELECT parent_id FROM parent_of WHERE id=tag_to_media_table.tag_id
                                UNION ALL
                                    SELECT parent_id FROM parent_of JOIN ancestor_of_person USING(id))
                            SELECT tag_table.parent_id FROM ancestor_of_person, tag_table
                                WHERE ancestor_of_person.id=tag_table.id and tag_table.parent_id!=0
                        );
        """
        try:
            cur = db_con.cursor()
            cur.execute(query, (face_id,))
            rows = cur.fetchall()

        except Exception as e:
            raise e

        tag_list = list(zip(*rows))

        return tag_list


def get_tag_ids_for_face_id(db_con: lite.Connection, face_id: int):
    """
    Gets a list of tag_ids associated with this face_id
    :param db_oon:  Sqlite customised adobe elements catalog database connection
    :param face_id: Face id for whcih source image details are to be retrieved
    :return:        list of tag_ids
    """
    with db_con:
        # query = "select face_table.face_id from face_table;"
        query = """
                SELECT 
                    tag_id 
                FROM 
                    face_table, 
                    media_table 
                WHERE
                    where face_table.face_id = ? 
                    media_table.id = face_table.media_id;
        """
        try:
            cur = db_con.cursor()
            cur.execute(query, (face_id,))
            rows = cur.fetchall()

        except Exception as e:
            raise e

        tag_ids = list(map(lambda kv: kv[0], rows))

        return tag_ids


def write_face_encoding_to_file(face_encoding: numpy.ndarray, person_name: str) -> bool:
    """
    Writes face_encoding data to a file in the current directory named <person_name>.fce
    If file exists it is overwritten
    :param face_encoding:   The face_encoding from face_recognition library (128 float numpy array)
    :param person_name:     String containing the person's name
    :return:                True if succeeded else False
    """
    try:
        f = open(person_name + '.fce', 'wb')
    except:
        # couldn't open file
        return False

    try:
        # f.write(marshal.dumps(face_encoding))
        f.write(face_encoding.tobytes())
        retval = True
    except:
        retval = False

    f.close()

    return retval


def read_face_encoding_from_file(person_name: str):
    """
    Reads face_encoding data from a file in the current directory named <person_name>.fce
    :param person_name: String containing the person's name
    :return:            The face_encoding from face_recognition library (128 float numpy array) or None if file does not exist
    """

    try:
        f = open(person_name + '.fce', 'rb')
    except:
        # couldn't open file
        return None

    try:
        data = f.read()
        # face_encoding = marshal.loads(data)
        face_encoding = numpy.frombuffer(data)
    except:
        face_encoding = None

    f.close()

    return face_encoding


def load_image_from_file_or_cache(filespec: str, image_mode: str = 'RGB', new_height: int = 1200):
    """
    Loads an image from file rotates it and converts it to RGB but DOES NOT resize it and returns as PIL image.  If in
    Cache, returns the cached image NOTE YOU MUST COPY THE CACHED IMAGE before changing it.
    :param filespec:    Fully qualified filespec string of file to open.
    :param image_mode:  Mode to convert image to (default is 'RGB')
    :param new_height:  Height in pixels to reduce image size to for faster face recognition (set to 0 or sys.maxsize for no scaling)
    :return:            PIL.image or None if not found
    """
    cached_image = myMainWindow.image_cache.get((filespec, new_height))
    if cached_image != -1:
        return (cached_image)
    else:
        try:
            image = PIL.Image.open(filespec)
        except:
            # Error opening file or file not found
            print("Error opening file or file not found: '{}'".format(filespec))
            image = None
            return image

        try:
            for orientation in ExifTags.TAGS.keys():
                if PIL.ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = dict(image._getexif().items())

            if exif[orientation] == 3:
                image = image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                image = image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                image = image.rotate(90, expand=True)

        except (AttributeError, KeyError, IndexError):
            # cases: image don't have getexif
            pass

        except:
            raise (Exception("Unexpected exception adjusting image orientation"))

        if image.mode != image_mode:
            # Image is not 3x8 bit trud coloru RGB so convert to that
            image = image.convert(mode=image_mode)

        if new_height:
            resized_image = resize_image(image, new_height)
            if not image:
                print(
                    "ERROR - Unexpected error attempting to resize image '{}'.  Returning unresized image from load_image_from_file_or_cache().".format(
                        filespec))
            else:
                image = resized_image

        # Add to cache
        myMainWindow.image_cache.set(key=(filespec, new_height), value=image)

        return image


def resize_image(image: PIL.Image, new_height: int = 1200, scale_up: bool = False):
    """
    Reduces size of an image to a sensible size for reasonably efficient face recognition and returns a copy as a PIL image
    or the original if no resizing is required
    :param image:       PIL image to resize
    :param new_height:  Height in pixels to reduce image size to for faster face recognition (set to 0 or sys.maxsize for no scaling)
    :param scale_up:    Set to true if you want to be able to scale the image up in size.
    :return:            resized PIL image copy or None if error.
    """
    if image == None or new_height == 0:
        # If no image or new_height is 0 whcich means don't resize, then return original.
        return image

    # resize image
    old_height, old_width = image.size
    if scale_up or new_height < old_height:
        # Image needs shrinking to be easier to scan for faces
        hpercent = float(new_height) / float(old_width)
        wsize = int((float(old_height) * hpercent))
        try:
            resized_image = image.resize((wsize, new_height), PIL.Image.ANTIALIAS)
        except:
            return None
            # raise(Exception("Error resizing image"))
        return resized_image
    else:
        return image


def load_orient_and_resize_face_rec_image(filespec: str, new_height: int = 1200):
    """
    Loads an image from file or cache, correcting its orientation from Exif data, resizes it to a sensible size for
    reasonably efficient face recognition and returns it as a numpy array
    :param filespec:    Fully qualified filespec string of file to open.
    :param new_height:  Height in pixels to reduce image size to for faster face recognition (set to 0 or sys.maxsize for no scaling)
    :return:            numpy.array() of reoriented and resized image data loaded.
    """
    image_nparray = None

    image = load_image_from_file_or_cache(filespec=filespec, new_height=new_height)
    if not image:
        return None

    # convert to numpy array
    image_nparray = numpy.array(image)
    if not isinstance(image_nparray, numpy.ndarray):
        return None

    return image_nparray


# def load_known_face_encodings():


def test_face_rec(unknown_image_filename, known_face_encodings, known_face_names, tolerance=0.6):
    # tom_face_encoding = read_face_encoding_from_file("Tom Krantz")
    # if tom_face_encoding is None:
    #     tom_image = face_recognition.load_image_file(r"C:\Users\Peter4\PycharmProjects\face rec\Tom Krantz.jpg")
    #     tom_face_encoding = face_recognition.face_encodings(tom_image)[0]
    #     write_face_encoding_to_file(tom_face_encoding, "Tom Krantz")
    #
    # # Load a sample picture and learn how to recognize it.
    # emma_face_encoding = read_face_encoding_from_file("Emma Krantz")
    # if emma_face_encoding is None:
    #     emma_image = face_recognition.load_image_file(r"C:\Users\Peter4\PycharmProjects\face rec\Emma Krantz.jpg")
    #     emma_face_encoding = face_recognition.face_encodings(emma_image)[0]
    #     write_face_encoding_to_file(emma_face_encoding, "Emma Krantz")
    #
    # # Create arrays of known face encodings and their names
    # known_face_encodings = [
    #     tom_face_encoding,
    #     emma_face_encoding
    # ]
    # known_face_names = {
    #     "Tom Krantz",
    #     "Emma Krantz"
    # }

    print("\nChecking face match for image '{}'".format(unknown_image_filename))

    # Load an image with an unknown face
    unknown_image = load_orient_and_resize_face_rec_image(unknown_image_filename,
                                                          myMainWindow.scaled_height_for_resized_images)

    # Find all the faces and face encodings in the unknown image
    unknown_image_face_locations = face_recognition.face_locations(unknown_image, model='hog')
    unknown_image_face_encodings = face_recognition.face_encodings(unknown_image, unknown_image_face_locations)

    # Convert the image to a PIL-format image so that we can draw on unknown_image_top of it with the Pillow library
    # See http://pillow.readthedocs.io/ for more about PIL/Pillow
    pil_image = Image.fromarray(unknown_image)

    # Create a Pillow ImageDraw Draw instance to draw with
    draw = ImageDraw.Draw(pil_image)
    # Loop through each face found in the unknown image
    count = 0
    if unknown_image_face_locations.__len__() == 0:
        print("    No faces found in image.")
    else:
        for (unknown_image_top, unknown_image_right, unknown_image_bottom,
             unknown_image_left), unknown_image_face_encoding in zip(unknown_image_face_locations,
                                                                     unknown_image_face_encodings):
            # See if the face is a match for the known face(s)
            # matches = face_recognition.compare_faces(known_face_encodings, unknown_image_face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, unknown_image_face_encoding)
            name = "Unknown"
            count += 1
            # If a match was found in known_face_encodings, just use the first one.
            lowest_distance_found = 1
            for (known_face_name, this_distance) in zip(known_face_names, face_distances):
                if this_distance <= tolerance:
                    if this_distance < lowest_distance_found:
                        lowest_distance_found = this_distance
                        name = known_face_name
                print("    face_distance between face {} and known image '{}' is {}".format(count, known_face_name,
                                                                                            this_distance))

            # Draw a box around the face using the Pillow module
            draw.rectangle(((unknown_image_left, unknown_image_top), (unknown_image_right, unknown_image_bottom)),
                           outline=(0, 0, 255))
            name = ("Face {}: {}").format(count, name)
            print("        {}".format(name))
            # Draw a label with a name below the face
            text_width, text_height = draw.textsize(name)
            draw.rectangle(((unknown_image_left, unknown_image_bottom - text_height - 10),
                            (unknown_image_right, unknown_image_bottom)), fill=(0, 0, 255), outline=(0, 0, 255))
            draw.text((unknown_image_left + 6, unknown_image_bottom - text_height - 5), name, fill=(255, 255, 255, 255))
    # Remove the drawing library from memory as per the Pillow docs
    del draw
    # Display the resulting image
    pil_image.show()
    # You can also save a copy of the new image to disk if you want by uncommenting this line
    # pil_image.save("image_with_boxes.jpg")


def load_known_face_encodings_from_elements_catalog(db_con):
    """
    Find all those media_table images with face_encodings in the media_face_encoding_table, load known_face_encodings
    and and known_face_names
    :param db_con:  Open database connection to Adobe Elements 6.0 SQLite Catalog database file
    :return:        Tuple of the following three lists:
                    (known_face_encodings, known_face_names, media_id)
                    where ...
                        known_face_encodings is a list of numpy.nparray of face encoding data
                        known_face_names is a list of str names
                        known_filenames is a list of filenames of the relevant files
    """
    known_face_encodings = []
    known_face_names = []
    known_filenames = []

    with db_con:
        cur = db_con.cursor()

        query = """
            Select media_id, full_filepath, drive_path_if_builtin, tag_id from tag_to_media_table, media_table, volume_table
                where 
                    media_table.volume_id = volume_table.id and
                    media_id = media_table.id and
                    tag_id in 
                        (select id from tag_table where name = 'Known Faces');     
            """

        cur.execute(query)
        rows = cur.fetchall()

        for row in rows:
            media_id = row[0]
            filename = ntpath.normpath(row[2] + row[1])
            tag_list = AEL.GetTagListsForFileFromCatalog(db_con, media_id)
            people_tags = [s for s in tag_list if s[0] == 'People']
            if people_tags.__len__() != 1:
                ex = "Unable to identify unique person from Catalog tags for file '{}' media_id {} - People tag count: ()".format(
                    filename, media_id, people_tags.__len__())
                if people_tags.__len__() == 0:
                    ex = "Please add a tag in Adobe Photoshop Elements to this photo.  " + ex
                raise Exception(ex)

            # Extract tag name of this person.
            person_name = people_tags[0][-1]

            # Try to read an encoding blob for this file / media_id from the media_face_encoding_table
            query = """
                select face_encoding_blob from media_face_encoding_table where media_id = {};
            """.format(media_id)

            cur.execute(query)
            blob_row = cur.fetchone()
            if blob_row:
                # Found a blob so convert it to a face encoding
                ## face_encoding: numpy.array = numpy.frombuffer(blob_row[0])
                face_encoding = numpy.frombuffer(bytes(blob_row[0]))
            else:
                # No face encoding in database so read file and create one.  Note no scaling as we want max
                # resolution on known images.
                image = load_orient_and_resize_face_rec_image(filename,
                                                              new_height=myMainWindow.scaled_height_for_resized_images)

                face_encodings = face_recognition.face_encodings(image)
                if face_encodings.__len__() != 1:
                    print("Error - unable to r"
                          "ead unique face encoding for file '{}'.  {} faces found.".format(filename,
                                                                                            face_encodings.__len__()))
                    continue

                # Found face encoding so add to database
                face_encoding = face_encodings[0]
                blob_bytes = face_encoding.tobytes()
                # blob_bytes_without_b = "{}".format(blob_bytes)[1:]
                query = """
                      INSERT INTO media_face_encoding_table 
                      VALUES({}, ?)""".format(media_id)
                cur.execute(query, (lite.Binary(blob_bytes),))
                db_con.commit()

            # We now have all elements for this file so add to relevant lists
            known_face_encodings.append(face_encoding)
            known_face_names.append(person_name)
            known_filenames.append((filename))

        # We now hoave all data so return
        return (known_face_encodings, known_face_names, known_filenames)


def get_thumbnail_filename_from_face_id(face_id: int):
    """
    Returns the filespec in the thumbnail cache for a given face_id thumbnail.
    :param face_id:
    :return: Fully qualified filespec of the thumbnail in the relevant %localappdata%\face_rec\thumbnails subdirectory
    """
    # Directory of all thumbnails between 1 and 999 inclusive is stored in a directory named <thumbnail_directory>+'0001000'
    # and 1001 to 1999 is stored in '00002000' and so on
    this_thumbnail_directory = myMainWindow.thumbnail_directory + '{:07}'.format(int(((face_id) / 1000) + 1) * 1000)
    filespec = this_thumbnail_directory + r'\{}.png'.format(face_id)
    return filespec


def PIL_image_to_QImage(image: PIL.Image):
    """
    Converts a PIL image to a Qt QImage
    :param image:   PIL image
    :return:        QImage
    """
    if image.mode != "RGBA":
        imrgba = image.convert("RGBA")
    else:
        imrgba = image
    data = imrgba.tobytes("raw", "RGBA")
    qimage = QtGui.QImage(data, imrgba.size[0], imrgba.size[1], QtGui.QImage.Format_RGBA8888)
    return qimage


def get_subtree_nodes(tree_widget_item):
    """Returns all QTreeWidgetItems in the subtree rooted at the given node."""
    nodes = []
    nodes.append(tree_widget_item)
    for i in range(tree_widget_item.childCount()):
        nodes.extend(get_subtree_nodes(tree_widget_item.child(i)))
    return nodes


def get_all_items(tree_widget):
    """Returns all QTreeWidgetItems in the given QTreeWidget."""
    all_items = []
    for i in range(tree_widget.topLevelItemCount()):
        top_item = tree_widget.topLevelItem(i)
        all_items.extend(get_subtree_nodes(top_item))
    return all_items


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myapp = myMainWindow()
    # scene = QtWidgets.QGraphicsScene()
    # for i in range(1,5):
    #     image = myapp.create_thumbnail_for_face(face_id=i)
    #     qimage = ImageQt.ImageQt(image)
    #     qpix = QtGui.QPixmap.fromImage(qimage)
    #     item = QtWidgets.QGraphicsPixmapItem(qpix)
    #     scene.addItem(item)
    # # view = QtWidgets.QGraphicsView(scene)
    # myapp.ui.graphicsView.setScene(scene)

    # view = QtWidgets.QGraphicsView(scene)

    ## d = load_data_from_face_table(db_con=myapp.db_con)
    # r = myapp.scan_unknown_faces_for_clusters()

    myapp.filter_named_faces()
    myapp.populate_tree_widget()

    ## Code to read a thumbnail from Adobe Photoshop Elements 6 thumbnail cache
    # media_thumbnail_qimage = AEL.GetMediaThumbnailFromMediaId(myapp.media_thumb_db_con, 443870, 160, 120)
    # pix_image = QtGui.QPixmap(media_thumbnail_qimage)

    myapp.show()
    sys.exit(app.exec_())

    # # test_face_rec()
    # db_con = lite.connect('C:\ProgramData\Adobe\Photoshop Elements\Catalogs\My Catalog\catalog.psedb')
    #
    # (known_face_encodings, known_face_names, known_filenames) = load_known_face_encodings_from_elements_catalog(db_con)
    #
    # with db_con:
    #     cur = db_con.cursor()
    #
    #     query = """
    #         Select media_id, full_filepath, drive_path_if_builtin, tag_id from tag_to_media_table, media_table, volume_table
    #             where
    #                 media_table.volume_id = volume_table.id and
    #                 media_id = media_table.id and
    #                 tag_id in
    #                     (select id from tag_table where name = 'Images for Face Tagging')
    #             LIMIT 10;
    #         """
    #
    #     cur.execute(query)
    #     rows = cur.fetchall()
    #
    #     for row in rows:
    #         filename = ntpath.normpath(row[2] + row[1])
    #         test_face_rec(filename, known_face_encodings, known_face_names)
