'''
RELEASE NOTES:
- Resizing now only optimises current plot, all other plots are optimised when shown.
- Resizing error when optimisation fails fixed.
- Runs can now be moved up/down in list.

WORKING ON:


BUGS TO FIX:
- Icons doesn't work properly
- Error checking for input (empty or non-existing points) in groups.
- Delete groups/runs should delete related plots (preferrably with warning message).

VERSION 1.0:
- Fix legend
- Import comment from .fem
- Fix table sizes etc.. layout stuff.
- Python-pptx
- Lower/upper bound graphs

VERSION 2.0:
1. VTF
2. NTF
3. PMOB

IDEAS MAYBE IMPLEMENT:
- Overlay click-button on single plot (to plot two points in one graph).
- Change color changes current plots? A lot of work.
'''
# GENERAL
import sys
import ntpath as nt
import os
import math
import csv
import numpy as np
import pandas as pd
import random
import pickle
import subprocess
import datetime

# GUI STUFF
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *
from resources import icons_rc

# PLOTTING
import matplotlib
import matplotlib.figure

import matplotlib.artist as artists
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter



from matplotlib.pyplot import savefig

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# QT
import Qt_designer.NVH_tool_design as des
QPlugin = QtCore.QPluginLoader("qico4.dll")

# Global vars
CONST_VALID_REQUESTS = ['DISPLACEMENTS']

# TREE VIEW STUFF
class Node(object):
	def __init__(self, name, parent=None):
		self._name = name
		self._children = []
		self._parent = parent
		
		if parent is not None:
			parent.addChild(self)
		
	def typeInfo(self):
		return "NODE"
	
	def addChild(self, child):
		self._children.append(child)
		
	def insertChild(self, position, child):
		if position < 0 or position > len(self._children):
			return False
			
		self._children.insert(position, child)
		child._parent = self
		return True
	
	def removeChild(self, position):
		if position < 0 or position > len(self._children):
			return False
			
		child = self._children.pop(position)
		child._parent = None
		return True
	
	def name(self):
		return self._name
		
	def setName(self, name):
		self._name = name
		
	def child(self, row):
		return self._children[row]
		
	def childCount(self):
		return len(self._children)
		
	def parent(self):
		return self._parent
		
	def row(self):
		if self._parent is not None:
			return self._parent._children.index(self)
			
	def log(self, tabLevel=-1):
		output = ""
		tabLevel += 1
		
		for i in range(tabLevel):
			output += "\t"
			
		output += "|-----" + self._name + "\n"
		
		for child in self._children:
			output += child.log(tabLevel)
		
		tabLevel -= 1
		output += "\n"
		
		return output
		
	def __repr__(self):
		return self.log()

class TransformNode(Node):
    
    def __init__(self, name, parent=None):
        super(TransformNode, self).__init__(name, parent)
        
    def typeInfo(self):
        return "TRANSFORM"

class CameraNode(Node):
    
    def __init__(self, name, parent=None):
        super(CameraNode, self).__init__(name, parent)
        
    def typeInfo(self):
        return "CAMERA"

class LightNode(Node):
    
    def __init__(self, name, parent=None):
        super(LightNode, self).__init__(name, parent)
        
    def typeInfo(self):
        return "LIGHT"

class treeModel(QtCore.QAbstractItemModel):
	def __init__(self, root, parent=None):
		super(treeModel, self).__init__(parent)
		self._rootNode = root
		
	def rowCount(self,parent):
		if not parent.isValid():
			parentNode = self._rootNode
		else:
			parentNode = parent.internalPointer()
			
		return parentNode.childCount()
		
	def columnCount(self,parent):
		return 2
		
	def flags(self,index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
	
	def data(self,index,role):
		if not index.isValid():
			return None
			
		node = index.internalPointer()
		
		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
			if index.column() == 0:
				return node.name()
			else:
				return node.typeInfo()
		elif role == QtCore.Qt.DecorationRole:
			if index.column() == 0:
				typeInfo = node.typeInfo()
				
				if typeInfo == "LIGHT"
					pass
				elif typeInfo == "TRANSFORM"
					pass
				elif typeInfo == "CAMERA"
					pass
		
			if index.column() == 1:
				Qcolor = QtGui.QColor("blue")
				pixmap = QtGui.QPixmap(26,26)
				pixmap.fill(Qcolor)
				icon = QtGui.QIcon(pixmap)
				return icon
				
		
	def setData(self, index, value, role=QtCore.Qt.EditRole):
		if index.isValid():
			if role == QtCore.Qt.EditRole:
				node = index.internalPointer()
				node.setName(value)
				
				return True
		return False
		
	def headerData(self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole:
			if section == 0:
				return "header 1"
			else:
				return "header 2"
		
	def parent(self, index):
		node = self.getNode(index)
		parentNode = node.parent()
		if parentNode == self._rootNode:
			return QtCore.QModelIndex()
			
		return self.createIndex(parentNode.row(), 0, parentNode)
		
	def index(self, row, column, parent):
		parentNode = self.getNode(parent)
		childItem = parentNode.child(row)
		
		if childItem:
			return self.createIndex(row, column, childItem)
		else: 
			return QtCore.QModelIndex()
			
	def getNode(self, index):
		if index.isValid():
			node = index.internalPointer()
			if node:
				return node
				
		return self._rootNode
		
	def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
		parentNode = self.getNode(parent)
		self.beginInsertRows(parent, position, position + rows - 1)
		
		for row in range(rows):
			childCount = parentNode.childCount()
			childNode = Node("untitled" + str(childCount))
			success = parentNode.insertChild(position, childNode)
		
		self.endInsertRows()
		
		return success
		
	def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
		parentNode = self.getNode(parent)
		self.beginRemoveRows(parent, position, position + rows - 1)
		
		for row in range(rows):
			childCount = parentNode.childCount()
			childNode = Node("untitled" + str(childCount))
			success = parentNode.removeChild(position)
		
		self.endRemoveRows()
		
		return success
		
# CLASSES FOR RUN TAB
class RunTableModel(QtCore.QAbstractTableModel):
	def __init__(self, runs, runs_headers, parent=None):
		super(RunTableModel, self).__init__(parent)
		self.runs = runs
		self.runs_headers = runs_headers
		self.currentSelection = None

	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(self.runs)

	def columnCount(self, parent=QtCore.QModelIndex()):
		return len(self.runs_headers)

	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
			row=index.row()
			col=index.column()
			if col == 0:
				return self.runs[row].label
			elif col == 1:
				return self.runs[row].pchfile_short
			elif col == 2:
				if self.runs[row].dynk_extracted == True:
					return self.runs[row].dynkfile_short
			elif col == 3:
				if self.runs[row].mass_extracted == True:
					if self.runs[row].mass >= 0.0:
						return "{0:.1f} kg".format(self.runs[row].mass)
					else:
						return "N/A"
			elif col == 4:
				return self.runs[row].comment
	
		if role == QtCore.Qt.EditRole:
			row = index.row()
			col = index.column()
			if col == 0:
				return self.runs[row].label
			elif col == 4:
				return self.runs[row].comment
			else:
				return 0
	
		#if role == QtCore.Qt.ToolTipRole:
		#	return "tooltip"
	
		if role == QtCore.Qt.DecorationRole:
			row = index.row()
			col = index.column()
			if col == 0:
				Qcolor = self.runs[row].Qcolor
				pixmap = QtGui.QPixmap(26,26)
				pixmap.fill(Qcolor)
				icon = QtGui.QIcon(pixmap)
				return icon
	
	def headerData(self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole:
			if orientation == QtCore.Qt.Horizontal:
				return self.runs_headers[section]
			else:
				return section+1
	
	def flags(self, index):
		column = index.column()
		if column == 0 or column == 4:
			return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		else:
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable	
	
	def setData(self, index, value, role = QtCore.Qt.EditRole):
		if role == QtCore.Qt.EditRole:
			row=index.row()
			col=index.column()
			if col == 0 and value != '':
				self.runs[row].label = value
				self.layoutChanged.emit()
				return True
			elif col == 4 and value != '':
				self.runs[row].comment = value
				self.layoutChanged.emit()
				return True
			else:
				return False

	def add_run_browse(self, parent = QtCore.QModelIndex()):
		options = QFileDialog.Options()
		#options |= QFileDialog.DontUseNativeDialog
		fileSelected, _ = QFileDialog.getOpenFileName(None,"Select .pch file", "","Pch Files (*.pch);;All Files (*)", options=options)
		if fileSelected:
			self.add_run(fileSelected,parent)
			
	def add_target_browse(self, parent = QtCore.QModelIndex()):
		options = QFileDialog.Options()
		#options |= QFileDialog.DontUseNativeDialog
		fileSelected, _ = QFileDialog.getOpenFileName(None,"Select .csv file", "","csv Files (*.csv);;All Files (*)", options=options)
		if fileSelected:
			# First convert to correct format
			dynkfile = dynkFromBandedFile(fileSelected)
			
			if dynkfile:
				# then add run if exists
				self.add_run(dynkfile,parent)
		
	def add_run(self, fileSelected, parent = QtCore.QModelIndex()):
		if fileSelected:
			# Check valid files
			extension = nt.basename(fileSelected).split('.')[1]
			valid = False
			if extension == "pch":
				valid = True
			if extension == "csv":
				self.filename_noext = fileSelected.split('_dynk.')[0]
				if self.filename_noext != fileSelected:
					valid = True
			
			if not valid:
				return False
	
		
			position = len(self.runs) + 1
			self.beginInsertRows(parent, position, position)
			
			# Choose first from list
			Qcolors = [QtGui.QColor("blue"),QtGui.QColor("red"), QtGui.QColor("green"), 
					  QtGui.QColor("magenta"),QtGui.QColor("cyan"), QtGui.QColor("darkCyan"), QtGui.QColor("darkMagenta"), 
					  QtGui.QColor("darkRed"), QtGui.QColor("darkGreen"), QtGui.QColor("yellow")]
			for Qcolor in Qcolors:
				unique = True
				for run in self.runs:
					if Qcolor == run.Qcolor:
						unique = False
						break
				if (unique):
					break
					
			if (not unique):
				# If list exhausted generate new color randomly
				too_close = True
				counter = 0
				while (too_close):
					counter += 1
					rgb = list(np.random.choice(range(256), size=3))			
					too_close = False
					for run in self.runs:
						run_rgb = run.Qcolor.getRgb()
						diff = math.sqrt(0.3333333*((run_rgb[0]-rgb[0])**2 + (run_rgb[1]-rgb[1])**2 + (run_rgb[2]-rgb[2])**2))
						#print(diff)				
						if diff <= 25:
							too_close = True
							break
						elif counter > 50:
							break
				Qcolor = QtGui.QColor(rgb[0],rgb[1],rgb[2])

			
			self.runs.append(NVHrun(fileSelected))
			
			self.runs[-1].changeColor(Qcolor)
			self.endInsertRows()
			self.layoutChanged.emit()
			return True
		else:
			return False
		
	def del_runs(self, selected_rows, parent = QtCore.QModelIndex()):
		for row in reversed(selected_rows):
			self.beginRemoveRows(QtCore.QModelIndex(),row,row)
			self.runs.pop(row)
			self.endRemoveRows()
		#for run in self.runs:
		#	print(run.label)
		self.layoutChanged.emit()
		return True
	
	def internal_swap(self,row_from,row_to):
		if row_to > len(self.runs)-1:
			row_to = 0
		if row_to < 0:
			row_to = len(self.runs)-1
		self.runs[row_from],self.runs[row_to] = self.runs[row_to],self.runs[row_from]
		self.layoutChanged.emit()
		return row_to
	
	def refresh(self, runs, parent = QtCore.QModelIndex()):
		self.beginResetModel()
		self.runs = runs
		self.endResetModel()
		self.layoutChanged.emit()
		return True

	def ext_dynk(self, selected_rows, parent = QtCore.QModelIndex()):
		for row in selected_rows:
			self.runs[row].extractDynK()
		self.layoutChanged.emit()
		return True
		
	def ext_banded_dynk(self, selected_rows, parent = QtCore.QModelIndex()):
		for row in selected_rows:
			self.runs[row].exportBandedDynk()
		return True

	def ext_mass(self, selected_rows, parent = QtCore.QModelIndex()):
		for row in selected_rows:
			self.runs[row].extractMass()
		
		self.layoutChanged.emit()
		return True
		
	def change_color(self, row, parent = QtCore.QModelIndex()):
		self.runs[row].changeColor(QColorDialog.getColor())

class dynkRunListModel(QtCore.QAbstractListModel):
	def __init__(self, runs, parent=None):
		super(dynkRunListModel, self).__init__()
		#QtCore.QAbstractListModel.__init__(self, parent)
		self.runs = runs
		self.currentSelection = None
		
	def rowCount(self, parent=QtCore.QModelIndex()):
		extracted_indexes = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
		return len(extracted_indexes)
	
	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
				row=index.row()
				extracted_indexes = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
				index = extracted_indexes[row]
				return self.runs[index].label
		
		if role == QtCore.Qt.DecorationRole:
				extracted_indexes = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
				row=index.row()
				index = extracted_indexes[row]
				Qcolor = self.runs[index].Qcolor
				pixmap = QtGui.QPixmap(26,26)
				pixmap.fill(Qcolor)
				icon = QtGui.QIcon(pixmap)
				return icon
				
	def refresh(self, runs, parent = QtCore.QModelIndex()):
		self.beginResetModel()
		self.runs = runs
		self.endResetModel()
		self.layoutChanged.emit()
		return True

# CLASSES FOR GROUPS TAB
class dynkSetGroupListModel(QtCore.QAbstractListModel):
	def __init__(self, dynkGroups, parent=None):
		super(dynkSetGroupListModel, self).__init__()
		self.currentSelection = None
		self.dynkGroups = dynkGroups
		
	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(self.dynkGroups)
	
	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
			row=index.row()
			return self.dynkGroups[row].label
		
		if role == QtCore.Qt.EditRole:
			row = index.row()
			return self.dynkGroups[row].label
						
	def flags(self, index):
		if index.row() != 0:
			return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		else:
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
	
	def setData(self, index, value, role = QtCore.Qt.EditRole):
		if role == QtCore.Qt.EditRole:
			row=index.row()
			if value and not (value.strip()  == ''):
				labels = [ self.dynkGroups[i].label for i in range(len(self.dynkGroups))]
				if value not in labels:
					self.dynkGroups[row].label = value
					self.layoutChanged.emit()
					return True
				else:
					return False
			else:
				if self.dynkGroups[row].label.strip() == '':
					self.removeRow(row)
				return False
						
	def insertRow(self, row, parent = QtCore.QModelIndex()):
		self.beginInsertRows(QtCore.QModelIndex(),row,row)
		self.dynkGroups.insert(row, dynkGroup(''))
		self.endInsertRows()
		self.layoutChanged.emit()
		return True

	def removeRow(self, row, parent = QtCore.QModelIndex()):
		self.beginRemoveRows(QtCore.QModelIndex(),row,row)
		self.dynkGroups.pop(row)
		self.endRemoveRows()
		self.layoutChanged.emit()
		return True
	
	def refresh(self, dynkGroups, parent = QtCore.QModelIndex()):
		self.beginResetModel()
		self.dynkGroups = dynkGroups
		self.endResetModel()
		self.layoutChanged.emit()
		return True
	
class dynkSetGroupTableModel(QtCore.QAbstractTableModel):
	def __init__(self, dynkGroups, parent=None):
		super(dynkSetGroupTableModel, self).__init__(parent)
		self.dynkGroups = dynkGroups
		self.currentSelection = None
		self.groupIndex = 0
		
	def rowCount(self, parent=QtCore.QModelIndex()):
		if self.dynkGroups:
			return self.dynkGroups[self.groupIndex].nrows
		else:
			return 0
		
	def columnCount(self, parent=QtCore.QModelIndex()):
		if self.dynkGroups:
			return self.dynkGroups[self.groupIndex].ncols
		else:
			return 0
		
	def changeGroup(self, current):
		index = current.row()
		if index <= len(self.dynkGroups)-1:
			self.beginResetModel()
			self.groupIndex = index
			self.endResetModel()
				
	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
			row=index.row()
			col=index.column()
			return self.dynkGroups[self.groupIndex].subcases[row][col]
	
		if role == QtCore.Qt.EditRole:
			row = index.row()
			col = index.column()
			return self.dynkGroups[self.groupIndex].subcases[row][col]
	
	def flags(self, index):
		return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
	
	def setData(self, index, value, role = QtCore.Qt.EditRole):
		if role == QtCore.Qt.EditRole:
			row=index.row()
			col=index.column()
			self.dynkGroups[self.groupIndex].subcases[row][col] = value
			self.layoutChanged.emit()
			return True
			
	def refresh(self, dynkGroups, parent = QtCore.QModelIndex()):
		self.beginResetModel()
		self.dynkGroups = dynkGroups
		self.endResetModel()
		self.layoutChanged.emit()
		return True

class dynkGroup:
	def __init__(self,label):
		self.type = 'group'
		self.nrows = 3
		self.ncols = 3
		self.label = label
		self.subcases = [[None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None],
		                 [None,None,None,None,None,None,None,None,None,None]]
	
	def rowChange(self,nrows):
		self.nrows = nrows
		
	def colChange(self,ncols):
		self.ncols = ncols
	
# CLASSES FOR DYNK TAB
class dynkGroupListModel(QtCore.QAbstractListModel):
	def __init__(self, dynkGroups, parent=None):
		super(dynkGroupListModel, self).__init__()
		self.currentSelection = None
		self.dynkGroups = dynkGroups
		
	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(self.dynkGroups)
	
	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
			return self.dynkGroups[row].label
						
	def flags(self, index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		
	def refresh(self, dynkGroups, parent = QtCore.QModelIndex()):
		self.beginResetModel()
		self.dynkGroups = dynkGroups
		self.endResetModel()
		self.layoutChanged.emit()
		return True

class dynkNodeListModel(QtCore.QAbstractListModel):
	def __init__(self, runs, parent=None):
		super(dynkNodeListModel, self).__init__()
		self.runs = runs
		self.currentSelection = None
		
	def rowCount(self, parent=QtCore.QModelIndex()):
		extracted_indices = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
		if extracted_indices:
			first = extracted_indices[0]
			return len(self.runs[first].nodes)
		else:
			return 1
		
	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
			row=index.row()
			extracted_indices = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
			if extracted_indices:
				first = extracted_indices[0]
				return self.runs[first].nodes[row]
			else:
				return ""

class dynkDirListModel(QtCore.QAbstractListModel):
	def __init__(self, runs, parent=None):
		super(dynkDirListModel, self).__init__()
		self.runs = runs
		self.currentSelection = None
		
	def rowCount(self, parent=QtCore.QModelIndex()):
		extracted_indices = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
		if extracted_indices:
			first = extracted_indices[0]
			return len(self.runs[first].dirs)
		else:
			return 1
		
	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
			row=index.row()
			extracted_indices = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
			if extracted_indices:
				first = extracted_indices[0]
				dir = self.runs[first].dirs[row]
				if dir == '1':
					dirs = 'X'
				elif dir == '2':
					dirs = 'Y'
				elif dir == '3':
					dirs = 'Z'
				return dirs
			else:
				return ""

class Dynkpage:
	def __init__(self,tabwidget,label):
		self.dir = ''
		self.dirs = ''
		self.node = ''
		self.num_rows = 0
		self.num_cols = 0
		self.type = 'group'
		self.label = label
		self.page = QWidget()
		self.gridlayout = QGridLayout(self.page)
		self.vlayout = QVBoxLayout()
		self.gridlayout.addLayout(self.vlayout, 0, 0, 1, 1)
		self.tabwidget = tabwidget
		self.tabwidget.addTab(self.page, label)
		self.figopt = True
	
	def addfig(self,num_rows,num_cols):
		self.num_rows = num_rows
		self.num_cols = num_cols
		self.fig, self.axarr  = plt.subplots(nrows=self.num_rows, ncols=self.num_cols, squeeze=False, sharex=False, sharey=False)
		self.canvas = FigureCanvas(self.fig)
		self.vlayout.addWidget(self.canvas)
		
	def __del__(self):
		index = self.tabwidget.indexOf(self.page)
		self.tabwidget.removeTab(index)
	
	def addNodeDirSelectors(self,runs):
		self.type = 'single'
		self.hlayout = QHBoxLayout()
		self.vlayout.addLayout(self.hlayout)
		
		self.nodeComboBox = QComboBox()
		self.nodeComboBox.setGeometry(QtCore.QRect(40, 40, 491, 31))
		self.hlayout.addWidget(self.nodeComboBox)
		self.dirComboBox = QComboBox()
		self.dirComboBox.setGeometry(QtCore.QRect(40, 40, 491, 31))
		self.hlayout.addWidget(self.dirComboBox)
		
		# MODELS
		self.nodeComboModel = dynkNodeListModel(runs)
		self.nodeComboBox.setModel(self.nodeComboModel)
		self.nodeComboBox.setCurrentIndex(0)
		self.dirComboModel = dynkDirListModel(runs)
		self.dirComboBox.setModel(self.dirComboModel)
		self.dirComboBox.setCurrentIndex(0)
		
		# SIGNALS
		self.nodeComboBox.currentTextChanged.connect(self.on_node_changed)
		self.dirComboBox.currentTextChanged.connect(self.on_dir_changed)
		
	def figure_optimise(self):
		try:
			self.fig.tight_layout(h_pad=0.0,rect=[0,0,1,0.95])
		except:
			self.figopt = False
		else:
			self.fig.canvas.draw()
			self.fig.canvas.flush_events()
			self.figopt = True
				
	def save_all_single_pictures(self,progressBar):
		nodeindex = self.nodeComboBox.currentIndex()
		dirindex = self.dirComboBox.currentIndex()
		
		count = 0
		maxcount = self.nodeComboModel.rowCount()*self.dirComboModel.rowCount()
		for i_n in range(self.nodeComboModel.rowCount()):
			self.nodeComboBox.setCurrentIndex(i_n)
			for i_d in range(self.dirComboModel.rowCount()):
				self.dirComboBox.setCurrentIndex(i_d)
				self.plotsingle(savefig=True)
				count += 1
				progressBar.setValue(int((count*100)/maxcount))
				
		self.nodeComboBox.setCurrentIndex(nodeindex)
		self.dirComboBox.setCurrentIndex(dirindex)
	
	def on_node_changed(self, value):
		self.node = value
		self.plotsingle()
		 
	def on_dir_changed(self, value):
		self.dirs = value
		if value == 'X':
			self.dir = '1'
		elif value == 'Y':
			self.dir = '2'
		elif value == 'Z':
			self.dir = '3'
		
		self.plotsingle()
		 
	def plotsingle(self,savefig=False,subcase=None):
		if savefig == True:
			fig, axarr  = plt.subplots(nrows=self.num_rows, ncols=self.num_cols, squeeze=True, sharex=False, sharey=False)
		else:
			axarr = self.axarr[0][0]
			fig = self.fig
		
		axarr.cla()
		if not subcase:
			subcase = self.node + self.dir
		
		title_label = self.node + '-' + self.dirs
		
		axarr.set_title(title_label, fontsize=9)
		axarr.set_xlabel('Freq. [Hz]', fontsize=8)
		axarr.set_ylabel('DynK [kN/mm]', fontsize=8)
		grey = (0.7,0.7,0.7)
		
		for run in self.selected_runs:
			freq=run.df_dynk.index.tolist()
			dynk=run.df_dynk[subcase].tolist()
			color = run.color
			r = float(color[0])/255.0
			g = float(color[1])/255.0
			b = float(color[2])/255.0
			
			tmplabel = run.label
			if run.mass >= 0.0:
				strmass = "{0:.1f} kg".format(run.mass)
				tmplabel = tmplabel + ' (' + strmass + ')'
			if run.comment != "":
				tmplabel = tmplabel + ' - ' + run.comment
				
				
			axarr.semilogy(freq, dynk, label=tmplabel, color = (r,g,b), linestyle='solid', linewidth=1.0) 
			# 'solid' | 'dashed', 'dashdot', 'dotted' 
			
		
		# AXIS FORMATTING
		axarr.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
		axarr.set_yticks([1,10,100,1000,1000])
		axarr.set_xlim([80,400])
		axarr.set_ylim([1,1000])
		
		# TICKS
		#axarr.axarr[0][0].minorticks_on()
		axarr.tick_params(axis = 'both', which = 'major', labelsize = 6)
		axarr.tick_params(axis = 'both', which = 'minor', labelsize = 6)
		
		# GRIDS
		axarr.grid(color=grey, which='major', linestyle=':', linewidth=1)
		axarr.grid(color=grey, which='minor', linestyle=':', linewidth=1)
			
		handles, labels = axarr.get_legend_handles_labels()
		fig.legend(handles, labels, loc='upper center', fancybox=True, shadow=True, ncol=3, prop={'size': 6})
		fig.tight_layout(h_pad=0.0,rect=[0,0,1,0.95])
		
		if savefig == True:
			# Get path
			fig_label = 'dynk-	' + self.node + self.dir
			path = nt.join(self.selected_runs[-1].dir, subcase_label)
			
			# set desired size and optimise
			figw = 1208
			figh = 768
			figdpi = self.fig.dpi
			fig.set_size_inches(figw/figdpi,figh/figdpi)
			fig.tight_layout(h_pad=0.0,rect=[0,0,1,0.95])
			
			# save picture
			fig.savefig(path, dpi=figdpi)
			plt.close(fig)
		else:
			fig.canvas.draw()
			fig.canvas.flush_events()

	def plotgroup(self,subc=None,savefig=False):
		if savefig == True:
			fig, axarr  = plt.subplots(nrows=self.num_rows, ncols=self.num_cols, squeeze=False, sharex=False, sharey=False)
		else:
			axarr = self.axarr
			fig = self.fig
			
		if subc:
			self.subcases = subc

		for row in range(self.num_rows):
			for col in range(self.num_cols):
				subcase = self.subcases[row][col]
				if subcase[-1] == '1':
					subcase_label = subcase[0:-1] + '-X'
				elif subcase[-1] == '2':
					subcase_label = subcase[0:-1] + '-Y'
				elif subcase[-1] == '3':
					subcase_label = subcase[0:-1] + '-Z'
				
				axarr[row][col].set_title(subcase_label, fontsize=9)
				axarr[row][col].set_xlabel('Freq. [Hz]', fontsize=8)
				axarr[row][col].set_ylabel('DynK [kN/mm]', fontsize=8)
				grey = (0.7,0.7,0.7)
				
				for run in self.selected_runs:
					freq=run.df_dynk.index.tolist()
					dynk=run.df_dynk[subcase].tolist()
					color = run.color
					r = float(color[0])/255.0
					g = float(color[1])/255.0
					b = float(color[2])/255.0
					
					tmplabel = run.label
					if run.mass >= 0.0:
						strmass = "{0:.1f} kg".format(run.mass)
						tmplabel = tmplabel + ' (' + strmass + ')'
					if run.comment != "":
						tmplabel = tmplabel + ' - ' + run.comment
					
					axarr[row][col].semilogy(freq, dynk, label=tmplabel, color = (r,g,b), linestyle='solid', linewidth=1.0) 
					# 'solid' | 'dashed', 'dashdot', 'dotted' 
					
				
				# AXIS FORMATTING
				axarr[row][col].yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
				axarr[row][col].set_yticks([1,10,100,1000,1000])
				axarr[row][col].set_xlim([80,400])
				axarr[row][col].set_ylim([1,1000])
				
				# TICKS
				#self.dynkpages[-1].axarr[row][col].minorticks_on()
				axarr[row][col].tick_params(axis = 'both', which = 'major', labelsize = 6)
				axarr[row][col].tick_params(axis = 'both', which = 'minor', labelsize = 6)
				
				# GRIDS
				axarr[row][col].grid(color=grey, which='major', linestyle=':', linewidth=1)
				axarr[row][col].grid(color=grey, which='minor', linestyle=':', linewidth=1)
					
		#plt.legend(loc='center top', bbox_to_anchor=(1, 0.5))
		handles, labels = axarr[row][col].get_legend_handles_labels()
		fig.legend(handles, labels, loc='upper center', fancybox=True, shadow=True, ncol=3, prop={'size': 6})
		fig.tight_layout(h_pad=0.0,rect=[0,0,1,0.95])
		
		if savefig == True:
			# Get path
			path = nt.join(self.selected_runs[-1].dir,'dynk-',self.label)
			
			# set desired size and optimise
			figw = 1208
			figh = 768
			figdpi = self.fig.dpi
			fig.set_size_inches(figw/figdpi,figh/figdpi)
			fig.tight_layout(h_pad=0.0,rect=[0,0,1,0.95])
			
			# save picture
			fig.savefig(path, dpi=figdpi)
			plt.close(fig)
	
# MISC CLASSES
class NVHrun:
	def __init__(self,file):
		# INITIALIZE
		self.dynk_extracted = False
		self.mass_extracted = False
		self.comment = ''
		self.mass = 0
		self.Qcolor = QtGui.QColor(0,0,0)
		self.color = self.Qcolor.getRgb()[0:3]
		self.subcases = []
		self.nodes = []
		self.dirs = []
		self.femfile_short = ''
		self.pchfile_short = ''
		self.outfile_short = ''
		self.dynkfile_short = ''
		
		extension = nt.basename(file).split('.')[1]
		if extension == "csv":
			self.filename_noext = file.split('_dynk.')[0]
		else:
			self.filename_noext = file.split('.')[0]
		
		# FILENAMES
		self.dir = nt.dirname(file)
		self.label = nt.basename(self.filename_noext)	
		self.femfile = self.filename_noext +".fem"
		self.pchfile = self.filename_noext +".pch"
		self.outfile = self.filename_noext +".out"
		self.dynkfile = self.filename_noext +"_dynk.csv"
		
		self.femfile_short = nt.basename(self.femfile)
		self.pchfile_short = nt.basename(self.pchfile) 
		self.outfile_short = nt.basename(self.outfile)
		self.dynkfile_short = nt.basename(self.dynkfile)
		
		# AUTO EXTRACT ON CREATION
		if extension == "csv":
			self.dynk_extracted = True
			self.readDynK()
		else:
			self.extractDynK()
		self.extractMass()
		self.extractComment()
		
	def extractComment(self):
		if os.path.exists(self.femfile):
			self.comment = ''
		
	def extractDynK(self):
		extractDynkFromPch(self.pchfile,self.dynkfile)
		self.dynk_extracted = True
		self.readDynK()
		
	def readDynK(self):
		if self.dynk_extracted:
			if os.path.exists(self.dynkfile):
				temp = pd.read_csv(self.dynkfile)
				self.df_dynk = temp.set_index("freq")
				self.subcases = self.df_dynk.columns.values.tolist()
				self.nodes = []
				for subcase in self.subcases:
					node = subcase[0:-1]
					dir = subcase[-1]
					if node not in self.nodes:
						self.nodes.append(node)
					if dir not in self.dirs:
						self.dirs.append(dir)
	
	def exportBandedDynk(self):
		file = self.filename_noext +"_dynk_rms.csv"
		bands = [[60,180],[180,280],[280,400]]
		freqs=self.df_dynk.index.tolist()
		
		# GET INDICES AT BREAKPOINTS
		bandids = []
		counter = 0
		for band in bands:
			bandids.append([])
			index_lb = min(range(len(freqs)), key=lambda i: abs(freqs[i]-band[0]))
			index_ub = min(range(len(freqs)), key=lambda i: abs(freqs[i]-band[1]))
			bandids[counter] = [index_lb,index_ub]
			counter += 1
		
		# OPEN FILE AND WRITE HEADER
		fout = open(file, 'w')
		fout.write("id")
		for dir in ['X-','Y-','Z-']:
			for band in bands:
				fout.write(","+dir+str(band[0])+'-'+str(band[1]))
		
		# WRITE BODY
		for subcase in self.subcases:
			# GET NODE AND DIR
			node = subcase[0:-1]
			dir = subcase[-1]
			
			# IF X THEN NEW LINE
			if dir == '1':
				fout.write('\n')
				fout.write(node)
			
			# GET BANDED VALUE
			band_dynk = []
			dynk=self.df_dynk[subcase].tolist()
			for [index_lb,index_ub] in bandids:
				sqrts = [i**2 for i in dynk[index_lb:index_ub]]
				n = index_ub - index_lb + 1
				band_dynk.append(math.sqrt(sum(sqrts)/float(n)))
			
			for val in band_dynk:
				fout.write(","+str(val))
		
		# CLOSE FILE
		fout.close()
	
	def extractMass(self):
		success = False
		if os.path.exists(self.outfile):
			with open(self.outfile) as fid:
				for line in fid:
					if "Mass     " in line:
						self.mass = float(line.split()[-1])*1000.0
						success = True
			
		if not success:
			self.mass = -1.0 # -1 is used to identify that mass could not be extracted
		
		self.mass_extracted = True
		
	def changeColor(self,Qcolor):
		self.Qcolor = Qcolor
		self.color = self.Qcolor.getRgb()[0:3]

# MAIN WINDOW	
class MainWindow(QMainWindow, des.Ui_MainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi(self)
		self.scriptDir = os.path.dirname(os.path.realpath(__file__))
		self.setWindowIcon(QtGui.QIcon(self.scriptDir + os.path.sep + 'nvh.ico'))
		self.title = 'NVH POST V0.2'
		self.setWindowTitle(self.title)
		self.defaultdir = os.path.expanduser('~')
		self.currdir = self.defaultdir
		self.keywordfile = '_nvhtool'
		
		### TREE VIEW STUFFS ###
		rootNode   = Node("Hips")
		childNode0 = TransformNode("RightPirateLeg",        rootNode)
		childNode1 = Node("RightPirateLeg_END",    childNode0)
		childNode2 = CameraNode("LeftFemur",             rootNode)
		childNode3 = Node("LeftTibia",             childNode2)
		childNode4 = Node("LeftFoot",              childNode3)
		childNode5 = LightNode("LeftFoot_END",          childNode4)
		print(rootNode)
		
		model = treeModel(rootNode)
		self.treeView.setModel(model)
		right = model.index(0,0,QtCore.QModelIndex())
		model.insertRows(0, 5, right)
		model.removeRows(0, 3, right)
		
		
		### APP DRAG AND DROP###
		self.setAcceptDrops(True)
		
		###   RUNS  TAB   ###
		self.projectfilename = ""
		self.projectfilename_short = ""
				
		###   RUNS  TAB   ###
		self.runs_headers = ["Label", "pch file", "dynk file", "Mass", "Comment"]
		self.new_project()
		
		######################
		###### RUNS TAB ######
		######################
		# RUNS TABLE
		self.run_table_model = RunTableModel(self.runs,self.runs_headers)
		self.runsTable.setModel(self.run_table_model)
		#self.runsTable.clicked.connect(self.test)
		self.runsTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.runsTable.customContextMenuRequested.connect(self.on_runtablerightclick)
		self.runsTable.setAlternatingRowColors(False)
		self.runsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.runsTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.run_table_selModel = QtCore.QItemSelectionModel(self.run_table_model)
		self.runsTable.setSelectionModel(self.run_table_selModel)
		
		######################
		###### GROUP TAB #####
		######################
		
		# MODELS SHARING SAME DATA
		self.dynk_set_groupList_model = dynkSetGroupListModel(self.dynkGroups)
		self.dynk_set_groupTable_model = dynkSetGroupTableModel(self.dynkGroups)
		self.dynk_group_List_model = dynkGroupListModel(self.dynkGroups)
		
		
		# GROUP LIST
		self.dynk_set_groupList.setModel(self.dynk_set_groupList_model)		
		self.dynk_set_groupList.selectionModel().currentChanged.connect(self.groupChanged)
		self.dynk_set_groupList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.dynk_set_groupList.customContextMenuRequested.connect(self.on_dynk_set_groupList_rightclick)
		
		# GROUP TABLE
		self.dynk_set_groupTable_model = dynkSetGroupTableModel(self.dynkGroups)
		self.dynk_set_groupTable.setModel(self.dynk_set_groupTable_model)
		
		######################
		###### DYNK TAB ######
		######################
		
		# GROUP LIST
		self.dynk_group_List.setModel(self.dynk_set_groupList_model)
		self.dynk_group_List.setSelectionMode(QAbstractItemView.ExtendedSelection)
		
		# RUN LIST
		self.run_list_model = dynkRunListModel(self.runs)
		self.dynkRunsList.setModel(self.run_list_model)
		self.dynkRunsList.setSelectionMode(QAbstractItemView.ExtendedSelection)
		
		### PLOT STUFF ###
		# PLOT BUTTON
		self.dynk_plotButton.clicked.connect(self.dynk_plot)
		
		## UP/DOWN BUTTONS ##
		self.runs_upbtn.clicked.connect(self.dynk_upbtn_click)
		self.runs_downbtn.clicked.connect(self.dynk_downbtn_click)
				
		### MENUBAR STUFF ###
		self.actionNew_project.triggered.connect(lambda: self.new_project_ask())
		self.actionOpen_Project.triggered.connect(lambda: self.open_project())
		self.actionSave_project.triggered.connect(lambda: self.save_project())
		self.actionSave_project.setShortcut('Ctrl+S')
		self.actionSave_project_as.triggered.connect(lambda: self.save_project_as())
		self.actionExit.triggered.connect(lambda: self.close())
		
		### GROUP SPINBOXES ###
		self.group_spinBox_rows.valueChanged.connect(lambda: self.groupSpinValuechange('rows'))
		self.group_spinBox_cols.valueChanged.connect(lambda: self.groupSpinValuechange('cols'))
		
		### TAB BAR ###
		self.dynkTabs.tabBar().installEventFilter(self)
		self.dynkTabs.currentChanged.connect(self.onDynkTabChanged)
		self.previousRightIndex = -1
		
		### RESIZING TIMER ###
		self.delayEnabled = True
		self.delayTimeout = 100
		self.resizeTimer = QtCore.QTimer(self)
		self.resizeTimer.timeout.connect(self.delayedUpdate)
		
		### PROGRESS BAR STUFF ###
		self.progressLabel.hide()
		self.progressBar.hide()
		
	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
			for url in event.mimeData().urls():
				# Workaround for OSx dragging and dropping
				#if op_sys == 'Darwin':
				#	fname = str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
				#else:
				fname = str(url.toLocalFile())
				if fname.lower().endswith(('.fem', '.pch', '.csv')):
					self.run_table_model.add_run(fname)
				self.run_list_model.refresh(self.runs)
		else:
			event.ignore()

	def groupChanged(self,current):
		index = current.row()
		self.dynk_set_groupTable_model.changeGroup(current)
		self.group_spinBox_rows.setValue(self.dynkGroups[index].nrows)
		self.group_spinBox_cols.setValue(self.dynkGroups[index].ncols)
		
	def groupSpinValuechange(self,key):
		if self.dynkGroups:
			index = self.dynk_set_groupTable_model.groupIndex
			if key == 'rows':
				nrows = self.group_spinBox_rows.value()
				self.dynkGroups[index].rowChange(nrows)
			elif key == 'cols':
				ncols = self.group_spinBox_cols.value()
				self.dynkGroups[index].colChange(ncols)
			self.dynk_set_groupTable_model.refresh(self.dynkGroups)
	
	def progressBarStart(self,action_label):
		self.progressLabel.setText(action_label)
		self.progressBar.setValue(0)
		self.progressLabel.show()
		self.progressBar.show()
		
	def progressBarSetProgress(self,val,maxval):
		progress = int((val*100)/maxval)
		self.progressBar.setValue(progress)
		if val == maxval:
			self.progressLabel.hide()
			self.progressBar.hide()
			
	def eventFilter(self, object, event):
		if object == self.dynkTabs.tabBar() and event.type() in [QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease] and event.button() == QtCore.Qt.RightButton:
			tabIndex = object.tabAt(event.pos())
			if event.type() == QtCore.QEvent.MouseButtonPress:
				self.previousRightIndex = tabIndex
			else:
				if tabIndex != -1 and tabIndex == self.previousRightIndex:
					self.onTabRightClick(tabIndex)
				self.previousRightIndex = -1
			return True
		return False
	
	def resizeEvent(self, event):
		# IF DYNK TAB
		if self.mainTabs.currentIndex() == 2:
			if self.dynkTabs.currentIndex() != -1:
				self.resizeTimer.start(self.delayTimeout)
				return super(MainWindow, self).resizeEvent(event)

	def onDynkTabChanged(self,index):
		if index != -1:
			if index <= len(self.dynkpages)-1:
				if not self.dynkpages[index].figopt:
					self.dynkpages[index].figure_optimise()
			
	def delayedUpdate(self):
		for dynkpage in self.dynkpages:
			dynkpage.figopt = False
		id = self.dynkTabs.currentIndex()
		self.dynkpages[id].figure_optimise()
		self.resizeTimer.stop()
		self.setUpdatesEnabled(True)

	def closeEvent(self, event):
		reply = QMessageBox.question(
			self, "Message",
			"Are you sure you want to close application? Any unsaved work will be lost.",
			QMessageBox.Close | QMessageBox.Cancel,
			QMessageBox.Cancel)
	
		if reply == QMessageBox.Close:
			event.accept()
		else:
			event.ignore()
	
	def onTabRightClick(self, index):
		# CREATE MENU
		menu = QMenu(self)
		
		# ITEMS ALWAYS PRESENT
		save_picture_action = QAction('Save picture', self)
		save_picture_action.triggered.connect(lambda: self.dynk_save_pic(index))
		menu.addAction(save_picture_action)
		
		save_all_pictures_action = QAction('Save all pictures', self)
		save_all_pictures_action.triggered.connect(lambda: self.dynk_save_all_pictures())
		menu.addAction(save_all_pictures_action)
		
		close_tab_action = QAction('Close tab', self)
		close_tab_action.triggered.connect(lambda: self.closeTab(index))
		menu.addAction(close_tab_action)
		
		close_alltabs_action = QAction('Close all tabs', self)
		close_alltabs_action.triggered.connect(lambda: self.closeAllTabs())
		menu.addAction(close_alltabs_action)	
						
		menu.popup(QtGui.QCursor.pos())
	
	def dynk_save_pic(self,index):
		if self.dynkpages[index].type == 'group':
			self.dynkpages[index].plotgroup(savefig=True)
		else:
			self.dynkpages[index].plotsingle(savefig=True)
		
	def dynk_save_all_pictures(self):
		self.progressBarStart('Saving all tab figures..')
		count = 0
		maxcount = len(self.dynkpages)
		for index in reversed(range(maxcount)):
			if self.dynkpages[index].type == 'group':
				self.dynk_save_pic(index)
			else:
				self.progressLabel.setText('Saving individual picures..')
				self.progressBar.setValue(0)
				self.dynkpages[index].save_all_single_pictures(self.progressBar)
				self.progressLabel.setText('Saving all tab figures..')
				
			count += 1
			self.progressBarSetProgress(count,maxcount)

	def closeTab(self,index):
		del self.dynkpages[index]
		
	def closeAllTabs(self):
		for index in reversed(range(len(self.dynkpages))):
			self.closeTab(index)
	
	def refresh_all(self):
		self.run_table_model.refresh(self.runs)
		self.run_list_model.refresh(self.runs)
		self.dynk_group_List_model.refresh(self.dynkGroups)
		self.dynk_set_groupList_model.refresh(self.dynkGroups)
		self.dynk_set_groupTable_model.refresh(self.dynkGroups)
	
	def setProjectFilename(self,filename):
		self.projectfilename = filename
		self.projectfilename_short = nt.basename(self.projectfilename)
		self.setWindowTitle(self.title + ' [' + self.projectfilename_short+ ']')
		self.currdir = nt.dirname(filename)
		self.writeKeyword('defaultdir',self.currdir)
	
	# reads keyword from default file and returns answer.
	def readKeyword(self,keyword):
		# Set default answer
		answer = ''
		# open default file in default dir
		file = nt.join(self.defaultdir, self.keywordfile)
		if os.path.exists(file):
			with open(file) as fid:
				for line in fid:
					if keyword in line:
						answer = os.path.normcase(line.split('=')[-1])
						
		return answer
		
	# replaces keyword in default file.
	def writeKeyword(self,keyword,value):
	
		# open default file in default dir
		file = nt.join(self.defaultdir, self.keywordfile)
		keyword_dict = {}
		success=False
		if os.path.exists(file):
			with open(file) as fid:
				for line in fid:
					currkeyword = line.split('=')[0]
					answer = line.split('=')[1]
					if currkeyword == keyword:
						answer = value
						success=True
					else:
						answer = os.path.normcase(line.split('=')[-1])
					keyword_dict[currkeyword] = answer
		
		# Keyword not in current file
		if not success:
			keyword_dict[keyword] = value
			
		# write file
		with open(file, 'w') as fid: 
			for key, val in keyword_dict.items():
				fid.write(key+'='+val)
	
	# creates new project
	def new_project_ask(self):
		if (len(self.runs) > 0 or len(self.dynkGroups) >1):
			reply = QMessageBox.question(
				self, "Message",
				"Are you sure you want to open a new project? Any unsaved work will be lost.",
				QMessageBox.Yes | QMessageBox.Cancel,
				QMessageBox.Cancel)
		else:
			reply = QMessageBox.Yes
			
		if reply == QMessageBox.Yes:
			del self.dynkGroups
			del self.runs
			del self.dynkpages
			self.new_project()
			self.closeAllTabs()
			self.refresh_all()

	# creates new project
	def new_project(self):
		self.dynkpages = []
		self.runs = []
		self.dynkGroups = []
		self.dynkGroups.append(dynkGroup('Single plots'))
		self.dynkGroups[0].nrows = 0
		self.dynkGroups[0].ncols = 0
		self.dynkGroups[0].type = 'single'
			
	# opens existing project
	def open_project(self):
	
		if (len(self.runs) > 0 or len(self.dynkGroups) >0):
			reply = QMessageBox.question(
				self, "Message",
				"Are you sure you want to open a project? Any unsaved work will be lost.",
				QMessageBox.Yes | QMessageBox.Cancel,
				QMessageBox.Cancel)
		else:
			reply = QMessageBox.Yes
	
		if reply == QMessageBox.Yes:
		
			# Get default path
			path = self.readKeyword('defaultdir')
			if path=='':
				path = self.defaultdir
				
			# Open file and get data
			options = QFileDialog.Options()
			filename, _ = QFileDialog.getOpenFileName(None,"Select .nvhproj file", path,"NVH project files (*.nvhproj);;All Files (*)", options=options)
			if filename:
				f = open(filename, "rb")
				[self.dynkGroups, self.runs] = pickle.load(f)
				f.close()	
	
				# Set project filename
				self.setProjectFilename(filename)
				
				# Refresh all widgets
				self.refresh_all()

	# save current project
	def save_project(self):
		if self.projectfilename == "":
			self.save_project_as()
		else:
			f = open(self.projectfilename, "wb")
			pickle.dump([self.dynkGroups, self.runs], f)
			f.close()
			
			self.projectfilename_short = nt.basename(self.projectfilename)
			self.setWindowTitle(self.title + ' [' + self.projectfilename_short+ ']')
	
	# save current project as
	def save_project_as(self):
		# Get default path
		path = self.readKeyword('defaultdir')
		if path=='':
			path = self.defaultdir
	
		options = QFileDialog.Options()
		filename, _ = QFileDialog.getSaveFileName(None,"Select .nvhproj file", path,"NVH project files (*.nvhproj);;All Files (*)", options=options)
		if filename:
			f = open(filename, "wb")
			pickle.dump([self.dynkGroups, self.runs], f)
			f.close()
			
			# Set project filename
			self.setProjectFilename(filename)
	
	def on_dynk_set_groupList_rightclick(self,point):
		index = self.dynk_set_groupList.indexAt(point)
		if index:	
			
			row = index.row()
			self.menu = QMenu(self)
			
			if row >= 0:
				add_item_action = QAction('Add group', self)
				del_item_action = QAction('Del group', self)
				add_item_action.triggered.connect(lambda: self.on_dynk_set_groupList_add(row))
				del_item_action.triggered.connect(lambda: self.on_dynk_set_groupList_delete(row))
				self.menu.addAction(add_item_action)
				self.menu.addAction(del_item_action)
			else:	
				ngroups = len(self.dynkGroups)-1
				add_item_action = QAction('Add group', self)
				add_item_action.triggered.connect(lambda: self.on_dynk_set_groupList_add(ngroups))
				self.menu.addAction(add_item_action)
				
			self.menu.popup(QtGui.QCursor.pos())
			
			# EMIT
			self.dynk_set_groupList.model().layoutChanged.emit()
		
	def on_dynk_set_groupList_add(self, row):
		# DELETE ITEM
		self.dynk_set_groupList_model.insertRow(row+1)
				
		# SELECT ITEM
		idx = self.dynk_set_groupList_model.index(row+1)
		self.dynk_set_groupList.setCurrentIndex(idx)
		self.dynk_set_groupList.edit(idx)			
	
	def on_dynk_set_groupList_delete(self, row):
		# Unless first row, decrement new current row
		if row > 0:
			new_row = row -1
		else:
			new_row = row
			
		idx = self.dynk_set_groupList_model.index(new_row-1)
		self.dynk_set_groupList.setCurrentIndex(idx)
		self.dynk_set_groupTable.groupIndex = new_row
		
		# DELETE ITEM
		self.dynk_set_groupList_model.removeRow(row)

	def dynk_upbtn_click(self):
		total_selection = None
		for index in self.runsTable.selectedIndexes():
			row = index.row()
			row_to = self.run_table_model.internal_swap(row,row-1)
			self.runsTable.selectRow(row_to)
			rowindex = self.run_table_model.index(row_to, 0)
			item_selection = QtCore.QItemSelection(rowindex,rowindex)
			if total_selection:
				total_selection.merge(item_selection,QtCore.QItemSelectionModel.Select)
			else:
				total_selection = item_selection
			
		self.run_table_selModel.select(total_selection, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.Select)
	
	def dynk_downbtn_click(self):
		total_selection = None
		for index in self.runsTable.selectedIndexes():
			row = index.row()
			row_to = self.run_table_model.internal_swap(row,row+1)
			self.runsTable.selectRow(row_to)
			rowindex = self.run_table_model.index(row_to, 0)
			item_selection = QtCore.QItemSelection(rowindex,rowindex)
			if total_selection:
				total_selection.merge(item_selection,QtCore.QItemSelectionModel.Select)
			else:
				total_selection = item_selection
			
		self.run_table_selModel.select(total_selection, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.Select)

	def dynk_plot(self):
		extracted_indexes = [ i for i in range(len(self.runs)) if self.runs[i].dynk_extracted ]
		ax = []
		if extracted_indexes:
		
			for index in self.dynk_group_List.selectedIndexes():
				group_id = index.row()
				
				# Get selected runs
				selected_runs = []
				for index in self.dynkRunsList.selectedIndexes():
					run_id = extracted_indexes[index.row()]
					selected_runs.append(self.runs[run_id])
				
				# Create new tab
				label = self.dynkGroups[group_id].label
				
				if self.dynkGroups[group_id].type == 'group':
					self.dynkpages.append(Dynkpage(self.dynkTabs,label))
					self.dynkpages[-1].selected_runs = selected_runs
					num_rows = self.dynkGroups[group_id].nrows
					num_cols = self.dynkGroups[group_id].ncols
					#num_rows = len(self.dynkGroups[group_id].subcases)
					#num_cols = len(self.dynkGroups[group_id].subcases[0])
					self.dynkpages[-1].addfig(num_rows,num_cols)
					self.dynkpages[-1].plotgroup(self.dynkGroups[group_id].subcases)
				else:
					self.dynkpages.append(Dynkpage(self.dynkTabs,label))
					self.dynkpages[-1].selected_runs = selected_runs
					self.dynkpages[-1].addNodeDirSelectors(self.runs)
					self.dynkpages[-1].addfig(1,1)
					self.dynkpages[-1].node = '101'
					self.dynkpages[-1].dir = '1'
					self.dynkpages[-1].dirs = 'X'
					self.dynkpages[-1].plotsingle()

	def on_runtablerightclick(self, point):
		selected_rows = []
		for index in self.runsTable.selectedIndexes():
			row = index.row()
			if (row not in selected_rows):
				selected_rows.append(row)
				
		nselected_rows = len(selected_rows)
		
		# CREATE MENU
		self.menu = QMenu(self)
		
		# ITEMS ALWAYS PRESENT
		add_run_action = QAction('Add run', self)
		add_run_action.triggered.connect(lambda: self.run_table_model.add_run_browse())
		self.menu.addAction(add_run_action)
		
		add_target_action = QAction('Add target', self)
		add_target_action.triggered.connect(lambda: self.run_table_model.add_target_browse())
		self.menu.addAction(add_target_action)
		
		# ITEMS ONLY PRESENT IF ROWS SELECTED
		if (nselected_rows > 0):
			ext_dynk_action = QAction('Extract dynk', self)
			ext_band_dynk_action = QAction('Extract dynk (RMS)', self)
			ext_mass_action = QAction('Extract mass', self)
			if (nselected_rows == 1):
				change_color_action = QAction('Change color', self)
				change_color_action.triggered.connect(lambda: self.run_table_model.change_color(selected_rows[0]))
				self.menu.addAction(change_color_action)
				del_run_action = QAction('Delete run', self)
			else:
				del_run_action = QAction('Delete runs', self)
				
			ext_dynk_action.triggered.connect(lambda: self.run_table_model.ext_dynk(selected_rows))
			self.menu.addAction(ext_dynk_action)
			ext_band_dynk_action.triggered.connect(lambda: self.run_table_model.ext_banded_dynk(selected_rows))
			self.menu.addAction(ext_band_dynk_action)
			ext_mass_action.triggered.connect(lambda: self.run_table_model.ext_mass(selected_rows))
			self.menu.addAction(ext_mass_action)
			del_run_action.triggered.connect(lambda: self.run_table_model.del_runs(selected_rows))
			self.menu.addAction(del_run_action)
							
		self.menu.popup(QtGui.QCursor.pos())
		
		# EMIT
		self.runsTable.model().layoutChanged.emit()
		self.dynkRunsList.model().layoutChanged.emit()

class PchParser:
	def reset_current_frame(self):
		self.cur_data_chunks = []
		self.is_frequency_response = False
		self.output_sort = 0
		self.cur_subcase = 0
		self.cur_output = 0
		self.current_frequency = 0
		self.cur_entity_id = 0
		self.cur_entity_type_id = 0

	def __init__(self, filename):		
		# define the dictionary
		self.parsed_data = {'FREQUENCY': {}, 'SUBCASES': set(), 'SUBCASELABELS': set()}
		for request in CONST_VALID_REQUESTS:
			self.parsed_data[request] = {}

		# initiate current frame
		self.reset_current_frame()

		is_header = True

		# start reading
		with open(filename, 'r') as pch:
			# read only first 72 characters from the punch file
			for line in pch:
				line = line[0:72]

				# reset all variables
				if line.startswith('$TITLE   ='):
					is_header = False
					# insert the last frame remaining in memory
					self.insert_current_frame()
					# reset the frame
					self.reset_current_frame()

				# skip everything before TITLE
				if is_header:
					continue

				# parse the subcase
				if line.startswith('$SUBCASE ID ='):
					self.cur_subcase = int(line[13:].strip())
					self.parsed_data['SUBCASES'].add(self.cur_subcase)
					
				# label
				if line.startswith('$LABEL   ='):
					self.cur_subcaselab = line[10:].strip()
					self.parsed_data['SUBCASELABELS'].add(self.cur_subcaselab)

				# identify NASTRAN request
				if line.startswith('$DISPLACEMENTS'):
					self.cur_request = 'DISPLACEMENTS'
				elif line.startswith('$ACCELERATION'):
					self.cur_request = 'ACCELERATION'
				elif line.startswith('$MPCF'):
					self.cur_request = 'MPCF'
				elif line.startswith('$SPCF'):
					self.cur_request = 'SPCF'
				elif line.startswith('$ELEMENT FORCES'):
					self.cur_request = 'ELEMENT FORCES'
				elif line.startswith('$ELEMENT STRAINS'):
					self.cur_request = 'ELEMENT STRAINS'

				# identify output type
				if line.startswith('$REAL-IMAGINARY OUTPUT'):
					self.cur_output = 'REAL-IMAGINARY'
				elif line.startswith('$MAGNITUDE-PHASE OUTPUT'):
					self.cur_output = 'MAGNITUDE-PHASE'
				elif line.startswith('REAL OUTPUT'):
					self.cur_output = 'REAL'

				# parse of frequency response results
				if line.find('IDENTIFIED BY FREQUENCY') != -1:
					self.is_frequency_response = True
					self.output_sort = 2
				elif line.find('$FREQUENCY =') != -1:
					self.is_frequency_response = True
					self.output_sort = 1

				# parse entity id
				if line.startswith('$POINT ID ='):
					self.cur_entity_id = int(line[11:23].strip())
				elif line.startswith('$ELEMENT ID ='):
					self.cur_entity_id = int(line[13:23].strip())
				elif line.startswith('$FREQUENCY = '):
					self.current_frequency = float(line[12:28].strip())

				# parse element type
				if line.startswith('$ELEMENT TYPE ='):
					self.cur_entity_type_id = int(line[15:27].strip())

				# ignore other comments
				if line.startswith('$'):
					continue

				# check if everything ok
				self.validate()

				# start data parsing
				line = line.replace('G', ' ')
				if line.startswith('-CONT-'):
					line = line.replace('-CONT-', '')
					self.cur_data_chunks += [float(_) for _ in line.split()]
				else:
					# insert the last frame
					self.insert_current_frame()

					# update the last frame with a new data
					self.cur_data_chunks = [float(_) for _ in line.split()]

			# last block remaining in memory
			self.insert_current_frame()

	def validate(self):
		if self.cur_request not in CONST_VALID_REQUESTS:
			raise NotImplementedError("Request %s is not implemented", self.cur_request)

		if self.cur_request == 'ELEMENT FORCES' and self.cur_entity_type_id not in [12, 102]:
			raise NotImplementedError("Element forces parser is implemented only for CELAS2 and CBUSH elements!")

	def insert_current_frame(self):
		# last block remaining in memory
		if len(self.cur_data_chunks) > 0:
			# ensure that subcase is allocated in the dataset
			if self.cur_subcase not in self.parsed_data[self.cur_request]:
				self.parsed_data[self.cur_request][self.cur_subcase] = {}
				self.parsed_data['FREQUENCY'][self.cur_subcase] = {}

			values = dispatch_parse(self.cur_output, self.cur_data_chunks[1:])
			if self.is_frequency_response:
				# incremented by frequency, entity is given
				if self.output_sort == 2:
					self.current_frequency = self.cur_data_chunks[0]
				# incremented by entity, frequency is given
				elif self.output_sort == 1:
					self.cur_entity_id = int(self.cur_data_chunks[0])
					
				# insert frequency in the database
				if self.current_frequency not in self.parsed_data['FREQUENCY'][self.cur_subcase]:
					self.parsed_data['FREQUENCY'][self.cur_subcase][self.current_frequency] = \
						len(self.parsed_data['FREQUENCY'][self.cur_subcase])

				# ensure that dictionary for the entity exists
				if self.cur_entity_id not in self.parsed_data[self.cur_request][self.cur_subcase]:
					self.parsed_data[self.cur_request][self.cur_subcase][self.cur_entity_id] = []

				self.parsed_data[self.cur_request][self.cur_subcase][self.cur_entity_id].append(values)
			else:
				self.cur_entity_id = int(self.cur_data_chunks[0])
				self.parsed_data[self.cur_request][self.cur_subcase][self.cur_entity_id] = values

	def health_check(self):
		frequency_steps = []
		for subcase in self.parsed_data['SUBCASES']:
			frequency_steps.append(len(self.parsed_data['FREQUENCY'][subcase]))
		assert min(frequency_steps) == max(frequency_steps)

	def get_subcases(self):
		return sorted(self.parsed_data['SUBCASES'])
		
	def get_subcaselabels(self):
		return sorted(self.parsed_data['SUBCASELABELS'])

	def __get_data_per_request(self, request, subcase):
		self.health_check()
		if subcase in self.parsed_data[request]:
			return self.parsed_data[request][subcase]
		else:
			raise KeyError('%s data for subase %d is not found' % (request, subcase))

	def get_accelerations(self, subcase):
		return self.__get_data_per_request('ACCELERATION', subcase)

	def get_displacements(self, subcase):
		return self.__get_data_per_request('DISPLACEMENTS', subcase)

	def get_mpcf(self, subcase):
		return self.__get_data_per_request('MPCF', subcase)

	def get_spcf(self, subcase):
		return self.__get_data_per_request('SPCF', subcase)

	def get_forces(self, subcase):
		return self.__get_data_per_request('ELEMENT FORCES', subcase)

	def get_frequencies(self, subcase):
		return sorted(self.parsed_data['FREQUENCY'][subcase])

def extractDynkFromPch(pchfile,csvfile):	
	# FOR GIANMARIA
	dispfile = pchfile.split('.')[0]+"_disp.csv"

	# Create pch file parser and parse pc file
	parser = PchParser(pchfile)
	
	# Get subcases & labels
	subcases = parser.get_subcases()
	subcaselabels = parser.get_subcaselabels
	
	# Get dictionary containing displacements
	dicts = []
	counter = -1
	for subcase in subcases:
		dict = parser.get_displacements(subcase)
		dicts.append(dict)
	
	# Write to file
	fout = open(csvfile, 'w')
	fout.write("freq")
	for item in subcases:
		fout.write(","+str(item))
	fout.write('\n')
	for freq in dicts[0].keys():
		fout.write(str(freq))
		counter = -1
		for subcase in subcases:
			counter += 1
			dir = int(str(subcase)[-1])
			dynk = (0.001/dicts[counter][freq][dir-1])
			fout.write(","+str(dynk))
		fout.write('\n')
	fout.close()
	
	# FOR GIANMARIA
	fout = open(dispfile, 'w')
	fout.write("")
	for item in subcases:
		fout.write(","+str(item))
	fout.write('\n')
	for freq in dicts[0].keys():
		fout.write(str(freq))
		counter = -1
		for subcase in subcases:
			counter += 1
			dir = int(str(subcase)[-1])
			disp = (dicts[counter][freq][dir-1])
			fout.write(","+str(disp))
		fout.write('\n')
	fout.close()
	
	del parser

def dynkFromBandedFile(filein):
	extension = nt.basename(filein).split('.')[1]
	if extension == "csv":
		filename_noext = filein.split('.')[0]
	else:
		return None

	# open file
	if os.path.exists(filein):
		fileout = filename_noext +"_dynk.csv"
		bands = []
		dynk = {}
		with open(filein) as fid:
			counter = 0
			for line in fid:
				line_split = line.rstrip().split(',')
				if counter == 0:
					# header line
					for item in line_split[1:]:
						item_split = item.split('-')
						dir = item_split[0]
						lb = item_split[1]
						ub = item_split[2]
						if dir == 'X':
							bands.append([lb,ub])
				else:
					node = line_split[0]
					dynk[node] = line_split[1:]
				counter += 1
		
		fout = open(fileout, 'w')
		fout.write("freq")
		for node in dynk.keys():
			for dir in ['1','2','3']:
				subcase = node + dir
				fout.write(','+subcase)
		
		counter = -1
		nbands = len(bands)
		for band in bands:
			counter += 1
			for f in band:
				fout.write('\n')
				fout.write(f)
				for node in dynk.keys():
					k = dynk[node]
					for dir in [1,2,3]:
						d = k[(dir-1)*nbands+counter]
						fout.write(','+d)
			
		
		# CLOSE FILE
		fout.close()
		
		return fileout
	else:
		return None

def dispatch_parse(output, data_chunks):
    if output == 'MAGNITUDE-PHASE' or output == 'REAL-IMAGINARY':
        num = int(len(data_chunks) / 2)
        if len(data_chunks) % 2 != 0:
            raise ValueError('Wrong number of chunks!', 'Output: %s, num of chunks: %d' % (output, len(data_chunks)))
    else:
        num = len(data_chunks)
    if output == 'MAGNITUDE-PHASE':
    		#return [data_chunks[i]*cmath.exp(1j*data_chunks[i+num]*cmath.pi/180.0) for i in range(num)]
    		return [data_chunks[i] for i in range(num)]
    elif output == 'REAL-IMAGINARY':
        return [data_chunks[i] + 1j*data_chunks[i+num] for i in range(num)]
    else:
        return [data_chunks[i] for i in range(num)]

def main():
	# CHECK DATE
	now = datetime.datetime.now()
	end = datetime.datetime(2020, 1, 1)
	if end > now:
		app = QApplication(sys.argv)
		form = MainWindow()
		form.show()
		app.exec_()
	else:
		print('Error')


if __name__ == '__main__':
    main()