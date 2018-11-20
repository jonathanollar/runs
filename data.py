class Node(object):
	def __init__(self, name, parent=None):
		self._name = name
		self._children = []
		self._parent = parent
		self._type = 'NODE'
		
		if parent is not None:
			parent.addChild(self)
		
	def typeInfo(self):
		return self._type
	
	def addChild(self, child):
		self._children.append(child)
		child._parent = self

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
	
	def name():
		def fget(self): return self._name
		def fset(self, value): self._name = value
		return locals()
	name = property(**name())
		
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

	def serialise_children(self):
		output = ""
		output += str(self.row())
		
		if self.childCount() > 0:
			output += ":"

			for child in self._children:
				output += child.serialise_children()
				output += ","
		
		return output

	def data(self, column):
		if   column is 0: return self.name
		elif column is 1: return self.typeInfo()
		elif column is 2: 
			if self.parent():
				return self.parent().name
			else:
				return "N/A"

	def setData(self, column, value):
		if   column is 0: self.name = value #.toPyObject()
		elif column is 1: pass
		elif column is 2: pass

	def resource(self):
		return None
		
	def __repr__(self):
		return self.log()

class ProjectNode(Node):
	def __init__(self, name, parent=None):
		super(ProjectNode, self).__init__(name, parent)
		self._type = 'project'

	def data(self, column):
		r = super(ProjectNode, self).data(column)

		#if   column is 2:  r = self.x

		return r

	def setData(self, column, value):
		super(ProjectNode, self).setData(column, value)

		#if   column is 2: self.x = value

	def resource(self):
		return None

class VersionNode(Node):
	def __init__(self, name, parent=None):
		super(VersionNode, self).__init__(name, parent)
		self._type = 'version'

	def data(self, column):
		r = super(VersionNode, self).data(column)

		#if   column is 2:  r = self.x

		return r

	def setData(self, column, value):
		super(VersionNode, self).setData(column, value)

		#if   column is 2: self.x = value

	def resource(self):
		return None

class RunNode(Node):
	def __init__(self, name, parent=None):
		super(RunNode, self).__init__(name, parent)
		self._type = 'run'
		self._comment = ''

	def data(self, column):
		r = super(RunNode, self).data(column)

		#if     column is 2: r = self._light

		return r

	def setData(self, column, value):
		super(RunNode, self).setData(column, value)
		#if   column is 2: self._light = value

	def resource(self):
		return None
	
	def light():
		def fget(self): return self._light
		def fset(self, value): self._light = value
		return locals()
	light = property(**light())

class NVHRunNode(RunNode):
	def __init__(self, name, parent=None):
		super(NVHRunNode, self).__init__(name, parent)
		self._type = 'nvh_run'
		self._comment = ''

	def data(self, column):
		r = super(NVHRunNode, self).data(column)

		#if     column is 2: r = self._light

		return r

	def setData(self, column, value):
		super(NVHRunNode, self).setData(column, value)
		#if   column is 2: self._light = value

	def resource(self):
		return None
	
	def light():
		def fget(self): return self._light
		def fset(self, value): self._light = value
		return locals()
	light = property(**light())

class CrashRunNode(RunNode):
	def __init__(self, name, parent=None):
		super(CrashRunNode, self).__init__(name, parent)
		self._type = 'crash_run'
		self._comment = ''

	def data(self, column):
		r = super(CrashRunNode, self).data(column)

		#if     column is 2: r = self._light

		return r

	def setData(self, column, value):
		super(CrashRunNode, self).setData(column, value)
		#if   column is 2: self._light = value

	def resource(self):
		return None
	
	def light():
		def fget(self): return self._light
		def fset(self, value): self._light = value
		return locals()
	light = property(**light())

