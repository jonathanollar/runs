# PYQT5
from PyQt5 import QtGui, QtCore, uic
from PyQt5.QtWidgets import *
from data import *
from copy import deepcopy

class RunTreeModel(QtCore.QAbstractItemModel):
	sortRole = QtCore.Qt.UserRole
	filterRole = QtCore.Qt.UserRole + 1

	def __init__(self, root, parent=None):
		super().__init__(parent)
		self._rootNode = root
		self.mimetype = 'move_run_node'

	def rowCount(self,parent=QtCore.QModelIndex()):
		if parent.isValid():
			parentNode = parent.internalPointer()
		else:
			parentNode = self._rootNode

		#if isinstance(parentNode,VersionNode):
		#	return 0

		return parentNode.childCount()

	def columnCount(self,parent):
		return 3

	def flags(self,index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

	def supportedDropActions(self):
		return QtCore.Qt.MoveAction

	def data(self,index,role):
		if not index.isValid():
			return None

		node = index.internalPointer()

		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
			return node.data(index.column())

		elif role == QtCore.Qt.DecorationRole:
			if index.column() == 0:
				resource = node.resource()
				return QtGui.QIcon(QtGui.QPixmap(resource))

		elif role == RunTreeModel.sortRole:
			return node.name

		elif role == RunTreeModel.filterRole:
			return node.name

	def setData(self, index, value, role=QtCore.Qt.EditRole):
		if index.isValid():
			node = index.internalPointer()
			if role == QtCore.Qt.EditRole:
				node.setData(index.column(), value)
				self.dataChanged.emit(index,index)
				return True
		return False

	def headerData(self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole:
			if section == 0:
				return "Node"
			elif section == 1:
				return "Type"
			elif section == 2:
				return "Directory"

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

	def getNode(self, index=QtCore.QModelIndex()):
		if index.isValid():
			node = index.internalPointer()
			if node:
				return node

		return self._rootNode

	def add_node(self, type, parentIndex=QtCore.QModelIndex()):
		parent = self.getNode(parentIndex)
		position = self.rowCount(parentIndex)
		self.beginInsertRows(parentIndex, position, position)

		childCount = parent.childCount()
		if type is 'project': childNode = ProjectNode(parent=parent)
		if type is 'version': childNode = VersionNode(parent=parent)
		if type is 'run': childNode = RunNode(parent=parent)
		if type is 'nvh_run': childNode = NVHRunNode(parent=parent)
		if type is 'crash_run': childNode = CrashRunNode(parent=parent)

		self.endInsertRows()
		return childNode

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
			success = parentNode.removeChild(position)
		self.endRemoveRows()
		return success

	def mimeTypes(self):
		types = []
		#types.append('text/plain')
		types.append(self.mimetype)
		return types

	def mimeData(self, index):
		# Only interested in row so get first index only
		ind = index[0]
		row = ind.row()
		text = str(row)

		# Get all parents rows
		parent_index = self.parent(ind)
		while parent_index.isValid():
			text =  text +',' + str(parent_index.row())
			parent_index = self.parent(parent_index)

		# mimeData
		mimeData = QtCore.QMimeData()
		ba = QtCore.QByteArray()
		ba.append(text)
		mimeData.setData(self.mimetype,ba)
		#mimeData.setText()
		return mimeData

	def getChildIndexFromMimeData(self,data):
		if data.hasFormat(self.mimetype):
			ba = data.data(self.mimetype)

		# Get data from mimeData
		if data.hasFormat(self.mimetype):
			text = ba.data().decode('utf8')
		else:
			return None

		if text is not "0":
			row_list = text.split(",")
			child_index = QtCore.QModelIndex() # root
			for row_str in reversed(row_list):
				parent_index = child_index
				row = int(row_str)
				child_index = self.index(row, 0, parent_index)
			return child_index
		else:
			return None

	def	canDropMimeData(self, data, action, new_row, new_column, new_parent_index=QtCore.QModelIndex()):
		if action == QtCore.Qt.IgnoreAction:
			return True

		# Get child
		child_index = self.getChildIndexFromMimeData(data)
		if child_index:
			child = self.getNode(child_index)
			child_type = child.typeInfo()

			# Get new parent node
			new_parent = self.getNode(new_parent_index)
			new_parent_type = new_parent.typeInfo()

			# Illegal places to drop returns False
			if new_parent.isRoot(): return False
			if child_type is 'project': return False
			if new_parent_type is not 'project' and new_parent_type is not 'version': return False

			return True
		else:
			return False

	def dropMimeData(self, data, action, new_row, new_column, new_parent_index=QtCore.QModelIndex()):
		if action == QtCore.Qt.IgnoreAction:
			return True

		# Get child
		child_index = self.getChildIndexFromMimeData(data)
		child = self.getNode(child_index)
		child_type = child.typeInfo()

		# Get new parent node
		new_parent = self.getNode(new_parent_index)
		new_parent_type = new_parent.typeInfo()

		# Make copy of child node (old one will be deleted automatically)
		new_child = deepcopy(child)

		# Figure out where to insert
		if new_row == -1: # IF -1 it is dropped directly on a node
			new_row = new_parent.childCount()

		# Insert child in new parent
		self.beginInsertRows(new_parent_index, new_row, new_row)
		new_parent.insertChild(new_row, new_child)
		self.endInsertRows()

		# Drop successful returns True
		return True

class RunTreeProxyModel(QtCore.QSortFilterProxyModel):

	def __init__(self, source_model, parent=None):
		super().__init__()
		self.source_model = source_model
		self.setSourceModel(self.source_model)
		self.setDynamicSortFilter(True)
		self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.setSortRole(self.source_model.sortRole)
		self.setFilterRole(self.source_model.filterRole)
		self.setFilterKeyColumn(0)

class RunTreeView(QTreeView):

	def __init__(self, proxy_model, parent=None):
		super().__init__()

		self.proxy_model = proxy_model
		self.source_model = proxy_model.sourceModel()

		self.setModel(proxy_model)
		self.setAlternatingRowColors(True)
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.on_tree_rightclick)
		self.setAlternatingRowColors(True)
		#self.setSortingEnabled(True)
		#self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setAcceptDrops(True)
		self.setDropIndicatorShown(True)
		self.setDragDropMode(QAbstractItemView.InternalMove)

	def mousePressEvent(self, event):
		self.clearSelection()
		QTreeView.mousePressEvent(self, event)

	def add_node(self,type,source_index=QtCore.QModelIndex()):
		# ADD NEW NODE TO SOURCE MODEL
		new_node = self.source_model.add_node(type, source_index)

		# GET INDEX OF NEW NODE
		new_index = self.source_model.index(new_node.row(), 0, source_index)
		idx = self.proxy_model.mapFromSource(new_index)

		# TRIGGER EDIT EVENT ON NEW NODE
		self.setCurrentIndex(idx)
		self.edit(idx)

	def on_tree_rightclick(self):
		# FIND SELECTED INDICES
		indexes = self.selectedIndexes()
		if indexes:
			index = indexes[0] # only single selection allowed
			source_index = self.proxy_model.mapToSource(index)
			node = self.source_model.getNode(source_index)
			node_type = node.typeInfo()
		else:
			node = self.source_model.getNode()
			node_type = node.typeInfo()

		# CREATE MENU
		self.menu = QMenu(self)

		# ITEMS ALWAYS PRESENT
		add_project_action = QAction('Add project', self)
		add_project_action.triggered.connect(lambda: self.add_node('project'))
		self.menu.addAction(add_project_action)

		# ITEMS ONLY PRESENT IF SELECTION
		if indexes:
			add_action = {}
			types = node._allowed_children
			for i,type in enumerate(types):
				add_action[i] = QAction('Add '+types[i], self)
				#add_action[i].triggered.connect(lambda state, t=types[i]: self.source_model.add_node(t, source_index))
				add_action[i].triggered.connect(lambda state, t=types[i]: self.add_node(t, source_index))
				self.menu.addAction(add_action[i])

			# DEL NODE
			delstring = 'Delete '+str(node_type)
			del_node_action = QAction(delstring, self)
			del_node_action.triggered.connect(lambda: self.source_model.removeRows(source_index.row(), 1, source_index.parent()))

			self.menu.addAction(del_node_action)

		# SHOW MENU
		self.menu.popup(QtGui.QCursor.pos())
