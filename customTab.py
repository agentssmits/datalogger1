from PyQt5 import QtCore, QtWidgets

from MplWidget import MplWidget

def addCustomTabs(self, count, start = 3):
	self.gridLayout4 = {}
	self.horizontalLayout2 = {}
	self.gridLayout6 = {}
	self.horizontalLayout10 = {}
	self.label21 = {}
	self.label22 = {}
	self.horizontalLayout9 = {}
	self.onlineCustomModeCheckBoxArr = {}
	
	for i in range (1, count+1):
		customSelectionCheckBoxArr = {}

		tab = QtWidgets.QWidget()
		
		# exp
		tab.setObjectName("customTab")
		self.gridLayout4[i] = QtWidgets.QGridLayout(tab)
		self.gridLayout4[i].setObjectName("gridLayout4_"+str(start+i))
		self.horizontalLayout2[i] = QtWidgets.QHBoxLayout()
		self.horizontalLayout2[i].setObjectName("horizontalLayout2_"+str(start+i))
		spacerItem28 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout2[i].addItem(spacerItem28)
		self.gridLayout6[i] = QtWidgets.QGridLayout()
		self.gridLayout6[i].setObjectName("gridLayout6_"+str(start+i))
		customSelectionCheckBoxArr[5] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[5].setObjectName("checkBox6_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[5], 1, 2, 1, 1)
		customSelectionCheckBoxArr[6] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[6].setObjectName("checkBox7_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[6], 0, 3, 1, 1)
		customSelectionCheckBoxArr[7] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[7].setObjectName("checkBox8_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[7], 1, 3, 1, 1)
		customSelectionCheckBoxArr[1] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[1].setObjectName("checkBox2_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[1], 1, 0, 1, 1)
		customSelectionCheckBoxArr[8] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[8].setObjectName("checkBox9_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[8],  0, 4, 1, 1)
		customSelectionCheckBoxArr[9] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[9].setObjectName("checkBox10_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[9], 1, 4, 1, 1)
		customSelectionCheckBoxArr[4] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[4].setObjectName("checkBox5_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[4], 0, 2, 1, 1)
		customSelectionCheckBoxArr[3] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[3].setObjectName("checkBox4_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[3], 1, 1, 1, 1)
		customSelectionCheckBoxArr[2] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[2].setObjectName("checkBox3_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[2], 0, 1, 1, 1)
		customSelectionCheckBoxArr[0] = QtWidgets.QCheckBox(tab)
		customSelectionCheckBoxArr[0].setObjectName("checkBox1_"+str(start+i))
		self.gridLayout6[i].addWidget(customSelectionCheckBoxArr[0], 0, 0, 1, 1)
		self.horizontalLayout2[i].addLayout(self.gridLayout6[i])
		spacerItem29 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout2[i].addItem(spacerItem29)
		self.gridLayout4[i].addLayout(self.horizontalLayout2[i], 0, 0, 1, 1)
		self.customMplWidgetArr[i] = MplWidget(tab)
		self.customMplWidgetArr[i].setObjectName("customMplWidgetArr_"+str(start+i))
		self.gridLayout4[i].addWidget(self.customMplWidgetArr[i], 2, 0, 1, 1)
		self.horizontalLayout10[i] = QtWidgets.QHBoxLayout()
		self.horizontalLayout10[i].setObjectName("self.horizontalLayout10_"+str(start+i))
		spacerItem30 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout10[i].addItem(spacerItem30)
		self.label21[i] = QtWidgets.QLabel(tab)
		self.label21[i].setObjectName("self.label21_"+str(start+i))
		self.horizontalLayout10[i].addWidget(self.label21[i])
		# self.customStartDateTimeButtonArr[i] = QtWidgets.QPushButton(tab)
		# self.customStartDateTimeButtonArr[i].setObjectName("self.customStartDateTimeButtonArr_"+str(start+i))
		# self.horizontalLayout10[i].addWidget(self.customStartDateTimeButtonArr[i])
		spacerItem31 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout10[i].addItem(spacerItem31)
		self.label22[i] = QtWidgets.QLabel(tab)
		self.label22[i].setObjectName("self.label22_"+str(start+i))
		self.horizontalLayout10[i].addWidget(self.label22[i])
		# self.customEndDateTimeButtonArr[i] = QtWidgets.QPushButton(tab)
		# self.customEndDateTimeButtonArr[i].setEnabled(True)
		# self.customEndDateTimeButtonArr[i].setObjectName("self.customEndDateTimeButtonArr_"+str(start+i))
		# self.horizontalLayout10[i].addWidget(self.customEndDateTimeButtonArr[i])
		spacerItem32 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout10[i].addItem(spacerItem32)
		self.gridLayout4[i].addLayout(self.horizontalLayout10[i], 3, 0, 1, 1)
		self.horizontalLayout9[i] = QtWidgets.QHBoxLayout()
		self.horizontalLayout9[i].setObjectName("self.horizontalLayout9_"+str(start+i))
		spacerItem33 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout9[i].addItem(spacerItem33)
		# self.onlineCustomModeCheckBoxArr[i] = QtWidgets.QCheckBox(tab)
		# self.onlineCustomModeCheckBoxArr[i].setObjectName("self.onlineCustomModeCheckBoxArr_"+str(start+i))
		# self.horizontalLayout9[i].addWidget(self.onlineCustomModeCheckBoxArr[i])
		spacerItem34 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout9[i].addItem(spacerItem34)
		self.gridLayout4[i].addLayout(self.horizontalLayout9[i], 4, 0, 1, 1)
		
		_translate = QtCore.QCoreApplication.translate
		customSelectionCheckBoxArr[5].setText(_translate("MainWindow", "channel 6"))
		customSelectionCheckBoxArr[6].setText(_translate("MainWindow", "channel 7"))
		customSelectionCheckBoxArr[7].setText(_translate("MainWindow", "channel 8"))
		customSelectionCheckBoxArr[1].setText(_translate("MainWindow", "channel 2"))
		customSelectionCheckBoxArr[8].setText(_translate("MainWindow", "channel 9"))
		customSelectionCheckBoxArr[9].setText(_translate("MainWindow", "channel 10"))
		customSelectionCheckBoxArr[4].setText(_translate("MainWindow", "channel 5"))
		customSelectionCheckBoxArr[3].setText(_translate("MainWindow", "channel 4"))
		customSelectionCheckBoxArr[2].setText(_translate("MainWindow", "channel 3"))
		customSelectionCheckBoxArr[0].setText(_translate("MainWindow", "channel 1"))
		# self.onlineCustomModeCheckBoxArr[i].setText(_translate("MainWindow", "continiously update"))
		# self.label21[i].setText(_translate("MainWindow", "Start:"))
		# self.label22[i].setText(_translate("MainWindow", "End:"))
		
		self.tabWidget.addTab(tab, "")
		name = "Group" + str(start-2+i)
		self.tabWidget.insertTab(start+i-1, tab, name)
		
		self.customSelectionCheckBoxArr[i] = customSelectionCheckBoxArr.copy()