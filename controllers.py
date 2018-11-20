
# GENERAL
import sys
#import ntpath as nt
#import os
#import math
#import csv
#import numpy as np
#import pandas as pd
#import random
#import pickle 
#import subprocess
#import datetime

# PYQT5
from PyQt5 import QtGui, QtCore, uic
from PyQt5.QtWidgets import *

# RESOURCE IMPORTS
#from resources import icons_rc

# PROJECT IMPORTS
from data import *
from models import *

main_base, main_form = uic.loadUiType("views/main.ui")
prop_base, prop_form = uic.loadUiType("views/props_editor.ui")
node_base, node_form = uic.loadUiType("views/node_editor.ui")
project_base, project_form = uic.loadUiType("views/project_editor.ui")
version_base, version_form = uic.loadUiType("views/version_editor.ui")
runs_base, runs_form = uic.loadUiType("views/runs_editor.ui")
nvh_runs_base, nvh_runs_form = uic.loadUiType("views/nvh_runs_editor.ui")
crash_runs_base, crash_runs_form = uic.loadUiType("views/crash_runs_editor.ui")

# MAIN WINDOW
class WnDTest(main_base, main_form):
	def __init__(self, parent=None):
		super(main_base, self).__init__(parent)
		self.setupUi(self)
		
		### HARD CODED NODE DATA ###
		self.rootNode   = Node("ROOT")
		projectNode1 = ProjectNode("F164",self.rootNode)
		projectNode2 = ProjectNode("F173",self.rootNode)
		projectNode3 = ProjectNode("F175",self.rootNode)
		projectNode4 = ProjectNode("F169",self.rootNode)
		projectNode5 = ProjectNode("F777",self.rootNode)
		projectNode6 = ProjectNode("F175BEV",self.rootNode)
		versionNode1 = VersionNode("V0",projectNode2)
		versionNode2 = VersionNode("V1",projectNode2)
		versionNode3 = VersionNode("V2",projectNode2)
		runNode1 = NVHRunNode("R000",versionNode2)
		runNode2 = NVHRunNode("R001",versionNode2)
		runNode3 = CrashRunNode("R006a",versionNode2)
		runNode4 = CrashRunNode("R006a",runNode2)
		runNode5 = CrashRunNode("R006a",runNode4)
		
		# SET TREE MODEL AND SPECS
		self._treemodel = treeModel(self.rootNode)
		
		# SET PROXYMODEL AND SPECS
		self._proxyModel = QtCore.QSortFilterProxyModel()
		self._proxyModel.setSourceModel(self._treemodel)
		self._proxyModel.setDynamicSortFilter(True)
		self._proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self._proxyModel.setSortRole(treeModel.sortRole)
		self._proxyModel.setFilterRole(treeModel.filterRole)
		self._proxyModel.setFilterKeyColumn(0)
		
		# TREE VIEW
		self.uiTree.setAlternatingRowColors(True)
		self.uiTree.setModel(self._proxyModel)
		self.uiTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.uiTree.customContextMenuRequested.connect(self.on_tree_rightclick)
		self.uiTree.setAlternatingRowColors(True)
		#self.uiTree.setSortingEnabled(True)
		#self.uiTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.uiTree.setDragEnabled(True)
		self.uiTree.setAcceptDrops(True)
		self.uiTree.setDropIndicatorShown(True)
		self.uiTree.setDragDropMode(QAbstractItemView.InternalMove)

		# FILTERING OF RUNS
		self.uiFilter.textChanged.connect(self._proxyModel.setFilterRegExp)
		
		# ADD PROPERTY EDITOR
		self._propEditor = PropertiesEditor(self)
		self._propEditor.setModel(self._proxyModel)

		# ADD PROPERTY EDITOR TO MAIN LAYOUT
		self.layout_main.addWidget(self._propEditor)
		
		# CONNECT TREE SELECTION MODEL TO PROPERTIES EDITOR
		self.uiTree.selectionModel().currentChanged.connect(self._propEditor.setSelection)

		# PRINT NODE STRUCTURE TO CONSOLE
		# print(rootNode)
				
		#child = Node("test")
		#self.rootNode.insertChild(1, child)
		#self.rootNode.insertChild(2, child)
		#self.rootNode.insertChild(3, child)

	def on_tree_rightclick(self,point):
		print(self.rootNode)
	
		indexes = self.uiTree.selectedIndexes()
		nodes = []
		#for index in indexes:
		if indexes:
			index = indexes[0] # only single selection allowed
			proxy = index.model()
			source_index = proxy.mapToSource(index)
			node = self._treemodel.getNode(source_index)
			node_type = node.typeInfo()
			parent_type = node.parent().typeInfo()
		
		# CREATE MENU
		self.menu = QMenu(self)

		# ITEMS ALWAYS PRESENT
		add_project_action = QAction('Add project', self)
		add_project_action.triggered.connect(lambda: self._treemodel.add_node(self._treemodel.rowCount(), 'project'))
		self.menu.addAction(add_project_action)

		# ITEMS ONLY PRESENT IF SELECTION
		if indexes:
			if node_type is 'project' or node_type is 'version':
				add_stage_action = QAction('Add version', self)
				add_stage_action.triggered.connect(lambda: self._treemodel.add_node(self._treemodel.rowCount(source_index), 'version',source_index))
				self.menu.addAction(add_stage_action)

			if node_type is 'version':
				add_nvh_run_action = QAction('Add NVH run', self)
				add_nvh_run_action.triggered.connect(lambda: self._treemodel.add_node(self._treemodel.rowCount(source_index), 'nvh_run',source_index))
				self.menu.addAction(add_nvh_run_action)
				add_crash_run_action = QAction('Add crash run', self)
				add_crash_run_action.triggered.connect(lambda: self._treemodel.add_node(self._treemodel.rowCount(source_index), 'crash_run',source_index))
				self.menu.addAction(add_crash_run_action)

			delstring = 'Delete '+str(node_type)
			del_node_action = QAction(delstring, self)
			del_node_action.triggered.connect(lambda: self._treemodel.removeRows(source_index.row(), 1, source_index.parent()))
			self.menu.addAction(del_node_action)			
		self.menu.popup(QtGui.QCursor.pos())

# PROPERTIES EDITOR
class PropertiesEditor(prop_base, prop_form):
	def __init__(self, parent=None):
		super(prop_base, self).__init__(parent)
		self.setupUi(self)
		
		self._proxyModel = None
		
		self._nodeEditor = NodeEditor(self)
		self._projectEditor = ProjectEditor(self)
		self._versionEditor = VersionEditor(self)
		self._runsEditor = RunsEditor(self)
		self._nvhRunsEditor = NVHRunsEditor(self)
		self._crashRunsEditor = CrashRunsEditor(self)
		
		self.layout_nodes.addWidget(self._nodeEditor)
		self.layout_specs.addWidget(self._projectEditor)
		self.layout_specs.addWidget(self._versionEditor)
		self.layout_specs.addWidget(self._runsEditor)
		self.layout_specs.addWidget(self._nvhRunsEditor)
		self.layout_specs.addWidget(self._crashRunsEditor)
		
		self._nodeEditor.setVisible(True)
		self._projectEditor.setVisible(False)
		self._versionEditor.setVisible(False)
		self._runsEditor.setVisible(False)
		self._nvhRunsEditor.setVisible(False)
		self._crashRunsEditor.setVisible(False)
		
	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._nodeEditor.setModel(proxyModel)
		self._projectEditor.setModel(proxyModel)
		self._versionEditor.setModel(proxyModel)
		self._runsEditor.setModel(proxyModel)
		self._nvhRunsEditor.setModel(proxyModel)
		self._crashRunsEditor.setModel(proxyModel)
		
	def setSelection(self, current):
		current = self._proxyModel.mapToSource(current)
		
		node = current.internalPointer()
		
		if node is not None:
			typeInfo = node.typeInfo()

			# DEFAULT
			self._nodeEditor.setVisible(True)
			self._projectEditor.setVisible(False)
			self._versionEditor.setVisible(False)
			self._runsEditor.setVisible(False)
			self._nvhRunsEditor.setVisible(False)
			self._crashRunsEditor.setVisible(False)
			
			# VARIABLE
			if typeInfo == "project":
				self._projectEditor.setVisible(True)
			elif typeInfo == "version":
				self._versionEditor.setVisible(True)
			elif typeInfo == "nvh_run":
				self._runsEditor.setVisible(True)
				self._nvhRunsEditor.setVisible(True)
			elif typeInfo == "crash_run":
				self._runsEditor.setVisible(True)
				self._crashRunsEditor.setVisible(True)
			
			self._nodeEditor.setSelection(current)
			self._projectEditor.setSelection(current)
			self._versionEditor.setSelection(current)
			self._runsEditor.setSelection(current)
			self._nvhRunsEditor.setSelection(current)
			self._crashRunsEditor.setSelection(current)

# NODE EDITOR
class NodeEditor(node_base, node_form):
	def __init__(self, parent=None):
		super(node_base, self).__init__(parent)
		self.setupUi(self)
		
		self._proxyModel = None
		self._dataMapper = QDataWidgetMapper()
		
	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._dataMapper.setModel(proxyModel.sourceModel())
		
		self._dataMapper.addMapping(self.ui_name, 0)
		self._dataMapper.addMapping(self.ui_type, 1)
	
	def setSelection(self, current): 
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)
		
# PROJECT EDITOR
class ProjectEditor(project_base, project_form):
	def __init__(self, parent=None):
		super(project_base, self).__init__(parent)
		self.setupUi(self)
		
		self._proxyModel = None
		self._dataMapper = QDataWidgetMapper()
		
	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._dataMapper.setModel(proxyModel.sourceModel())
		
		#self._dataMapper.addMapping(self.ui_light, 2)
		#self._dataMapper.addMapping(self.ui_near, 3)
		#self._dataMapper.addMapping(self.ui_far, 4)
		#self._dataMapper.addMapping(self.ui_shadows, 5)

		#self.ui_shadows.stateChanged.connect(self._dataMapper.submit)
	
	def setSelection(self, current): 
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)
		
# VERSION EDITOR
class VersionEditor(version_base, version_form):
	def __init__(self, parent=None):
		super(version_base, self).__init__(parent)
		self.setupUi(self)
		
		self._proxyModel = None
		self._dataMapper = QDataWidgetMapper()
		
	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._dataMapper.setModel(proxyModel.sourceModel())
		
		#self._dataMapper.addMapping(self.ui_blur, 2)
		#self._dataMapper.addMapping(self.ui_shake, 3)
	
	def setSelection(self, current): 
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)

# RUNS EDITOR
class RunsEditor(runs_base, runs_form):
	def __init__(self, parent=None):
		super(runs_base, self).__init__(parent)
		self.setupUi(self)
		
		self._proxyModel = None
		self._dataMapper = QDataWidgetMapper()
		
	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._dataMapper.setModel(proxyModel.sourceModel())
		
		#self._dataMapper.addMapping(self.ui_blur, 2)
		#self._dataMapper.addMapping(self.ui_shake, 3)
	
	def setSelection(self, current): 
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)

# NVH RUNS EDITOR
class NVHRunsEditor(nvh_runs_base, nvh_runs_form):
	def __init__(self, parent=None):
		super(nvh_runs_base, self).__init__(parent)
		self.setupUi(self)
		
		self._proxyModel = None
		self._dataMapper = QDataWidgetMapper()
		
	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._dataMapper.setModel(proxyModel.sourceModel())
		
		#self._dataMapper.addMapping(self.ui_blur, 2)
		#self._dataMapper.addMapping(self.ui_shake, 3)
	
	def setSelection(self, current): 
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)

# CRASH RUNS EDITOR
class CrashRunsEditor(crash_runs_base,crash_runs_form):
	def __init__(self, parent=None):
		super(crash_runs_base, self).__init__(parent)
		self.setupUi(self)
		
		self._proxyModel = None
		self._dataMapper = QDataWidgetMapper()
		
	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._dataMapper.setModel(proxyModel.sourceModel())
		
		#self._dataMapper.addMapping(self.ui_blur, 2)
		#self._dataMapper.addMapping(self.ui_shake, 3)
		#self._dataMapper.addMapping(self.ui_shake, 3, 'currentIndex')
	
	def setSelection(self, current): 
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)

if __name__ == '__main__':
		app = QApplication(sys.argv)
		app.setStyle("cleanlooks")
		wnd = WnDTest()
		wnd.show()
		
		sys.exit(app.exec_())

		#app = QApplication(sys.argv)
		#form = MainWindow()
		#form.show()
		#app.exec_()