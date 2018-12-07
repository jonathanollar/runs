
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

tabs_base, tabs_form = uic.loadUiType("views/tabs.ui")
prop_base, prop_form = uic.loadUiType("views/props_editor.ui")
node_base, node_form = uic.loadUiType("views/node_editor.ui")
project_base, project_form = uic.loadUiType("views/project_editor.ui")
version_base, version_form = uic.loadUiType("views/version_editor.ui")
runs_base, runs_form = uic.loadUiType("views/runs_editor.ui")
nvh_runs_base, nvh_runs_form = uic.loadUiType("views/nvh_runs_editor.ui")
crash_runs_base, crash_runs_form = uic.loadUiType("views/crash_runs_editor.ui")

# MAIN WINDOW
class Application(tabs_base, tabs_form):
	def __init__(self, parent=None):
		super().__init__(parent)
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
		#runNode1 = NVHRunNode("R000",versionNode2)
		#runNode2 = NVHRunNode("R001",versionNode2)
		#runNode3 = CrashRunNode("R006a",versionNode2)
		#runNode4 = CrashRunNode("R006b",versionNode2)
		#runNode5 = CrashRunNode("R006c",versionNode2)

		# TREE VIEW + MODELS
		self._run_tree_model = RunTreeModel(self.rootNode)
		self._run_proxy_model = RunTreeProxyModel(self._run_tree_model)
		self._run_tree_view = RunTreeView(self._run_proxy_model)
		self._runs_tab_layout.addWidget(self._run_tree_view)

		# PROPERTY EDITOR + MODELS
		self._run_propeditor = PropertiesEditor(self)
		self._run_propeditor.setModel(self._run_proxy_model)
		self._runs_tab_layout.addWidget(self._run_propeditor)

		# ADD PROPERTY EDITOR

		# CONNECT TREE SELECTION MODEL TO PROPERTIES EDITOR
		self._run_tree_view.selectionModel().currentChanged.connect(self._run_propeditor.setSelection)

		# FILTERING OF RUNS
		#self.uiFilter.textChanged.connect(self._proxyModel.setFilterRegExp)

		# PRINT NODE STRUCTURE TO CONSOLE
		# print(rootNode)

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

		# BIND BUTTON TO BROWSE DIR
		self.proj_dir_browse.clicked.connect(self.browse_dir)

	def setModel(self, proxyModel):
		self._proxyModel = proxyModel
		self._dataMapper.setModel(proxyModel.sourceModel())

		self._dataMapper.addMapping(self.proj_dir, 2)
		self.proj_dir.textChanged.connect(self._dataMapper.submit)

	def setSelection(self, current):
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)

	def browse_dir(self):
		dir = QFileDialog.getExistingDirectory(None, 'Select a folder:', "", QFileDialog.ShowDirsOnly)
		if dir:
			self.proj_dir.setText(dir)



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

		self._dataMapper.addMapping(self.version_dir, 2)
		self.version_dir.textChanged.connect(self._dataMapper.submit)

	def setSelection(self, current):
		parent = current.parent()
		self._dataMapper.setRootIndex(parent)
		self._dataMapper.setCurrentModelIndex(current)


	def browse_dir(self):
		dir = QFileDialog.getExistingDirectory(None, 'Select a folder:', "", QFileDialog.ShowDirsOnly)
		if dir:
			self.version_dir.setText(dir)

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
		wnd = Application()
		wnd.show()
		sys.exit(app.exec_())
