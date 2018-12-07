import os

class Node(object):
	def __init__(self, name='node', parent=None):
		self._name = name
		self._children = []
		self._parent = parent
		self._type = 'NODE'
		self._dir = ''

		if parent is not None:
			parent.addChild(self)
		else:
			self._type = 'ROOT'

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

	def isRoot(self):
		if self._parent is None:
			return True
		else:
			return False

	def log(self, tabLevel=-1):
		output = ""
		tabLevel += 1

		for i in range(tabLevel):
			output += "\t"

		output += "|-----" + self._name + '(' + self._type + ')' + "\n"

		for child in self._children:
			output += child.log(tabLevel)

		tabLevel -= 1
		output += "\n"

		return output

	def data(self, column):
		if   column is 0: return self.name
		elif column is 1: return self.typeInfo()
		elif column is 2: return self._dir

	def setData(self, column, value):
		if   column is 0: self.name = value
		elif column is 1: pass
		elif column is 2: self._dir = value

	def resource(self):
		return None

	def __repr__(self):
		return self.log()

#class RootNode(Node):
	#def __init__(self, name, parent=None):
		#super(RootNode, self).__init__(name, parent)
		#self._type = 'ROOT'

class ProjectNode(Node):
	def __init__(self, name='New project', parent=None):
		super(ProjectNode, self).__init__(name, parent)
		self._type = 'project'
		self._allowed_children = ['version','run']
		self._dir = ''

	def data(self, column):
		r = super(ProjectNode, self).data(column)

		if   column is 2:  r = self._dir

		return r

	def setData(self, column, value):
		super(ProjectNode, self).setData(column, value)

		if   column is 2: self.x = value

	def resource(self):
		return None

	def set_dir(self,dir):
		self._dir = dir

class VersionNode(Node):
	def __init__(self, name='New Version', parent=None):
		super(VersionNode, self).__init__(name, parent)
		self._type = 'version'
		self._allowed_children = ['version','run']
		self._dir = os.path.join(parent._dir,self._name)

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
	def __init__(self, name='New run', parent=None):
		super(RunNode, self).__init__(name, parent)
		self._type = 'run'
		self._dir = os.path.join(parent._dir,self._name)
		self._allowed_children = []

	def data(self, column):
		r = super(RunNode, self).data(column)

		#if     column is 2: r = self._light

		return r

	def setData(self, column, value):
		super(RunNode, self).setData(column, value)
		#if   column is 2: self._light = value

	def resource(self):
		return None

class Run(Node):
	def __init__(self, name='run', parent=None):
		super().__init__(name, parent)
		self._type = 'run'
		self._dir = os.path.join(parent._dir,self._name)

class DynkRun(Run):
	def __init__(self, name='DYNK', parent=None):
		super().__init__(name, parent)
		self._type = 'dynk_run'

		# INITIALIZE
		self.dynk_extracted = False
		self.mass_extracted = False
		self.comment = ''
		self.mass = 0
		#self.Qcolor = QtGui.QColor(0,0,0)
		self.color = [0,0,0]
		self.subcases = []
		self.nodes = []
		self.dirs = []
		self.femfile_short = ''
		self.pchfile_short = ''
		self.outfile_short = ''
		self.dynkfile_short = ''

	def set_pchfile(file):
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

class NVHRunNode(RunNode):
	def __init__(self, name, parent=None):
		super(NVHRunNode, self).__init__(name, parent)
		self._type = 'nvh_run'

	def data(self, column):
		r = super(NVHRunNode, self).data(column)

		#if     column is 2: r = self._light

		return r

	def setData(self, column, value):
		super(NVHRunNode, self).setData(column, value)
		#if   column is 2: self._light = value

	def resource(self):
		return None

class CrashRunNode(RunNode):
	def __init__(self, name, parent=None):
		super(CrashRunNode, self).__init__(name, parent)
		self._type = 'crash_run'

	def data(self, column):
		r = super(CrashRunNode, self).data(column)

		#if     column is 2: r = self._light

		return r

	def setData(self, column, value):
		super(CrashRunNode, self).setData(column, value)
		#if   column is 2: self._light = value

	def resource(self):
		return None
