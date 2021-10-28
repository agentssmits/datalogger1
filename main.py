from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import QTime, QDateTime, QSettings
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QLineEdit, QSpinBox, QCheckBox, QComboBox, QHBoxLayout, QLabel

import warnings
warnings.filterwarnings("ignore", "(?s).*MATPLOTLIBDATA.*", category=UserWarning)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import matplotlib as mpl

from MplWidget import MplWidget
from customTab import addCustomTabs
from DateTimePicker import DateTimePicker

import argparse
import logging as log
import sys
import os
from functools import partial
import threading

import numpy as np
import pandas as pd

from ltc2986 import *
from dataloader import *
from telegram import *

DEFAULT_IDEALITY = 1.05
DEFAULT_RESISTANCE = 2930.0

TELEGARM_MODE = False

# specify *.ui file location for main window
Ui_MainWindow, QtBaseClass = uic.loadUiType("datalogger.ui")

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self, offline = False):
		"""The constructor"""
		self.channelSettingWidgetsArr = [ [] for _ in range(CH_COUNT) ]
		self.channelLabelWidgetsArr = [ [] for _ in range(CH_COUNT) ]
		self.channelEnabledArr = [False]*CH_COUNT
		self.channelsToRead = []
		
		self.settings = QSettings(".GUI_settings", QSettings.IniFormat)
		
		QtWidgets.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		
		# deactivate start sampling button 
		self.start_sampling_btn.setEnabled(False)
		
		# restore  settings of General widgets
		for widget in self.settingsTab.findChildren(QLineEdit):
			if ("_val" not in widget.objectName()) and ("_status" not in widget.objectName()):
				value = self.settings.value("settings/"+str(widget.objectName()), "none", type=str)
				if value != "none":
					widget.setText(value)
				widget.textChanged.connect(partial(self.saveQLineEdit, widget))
		
		for widget in self.settingsTab.findChildren(QSpinBox):		
			value = self.settings.value("settings/"+str(widget.objectName()), 1, type=int)
			widget.setValue(value)
			widget.textChanged.connect(partial(self.saveQSpinBox, widget))
		
		# comboboxes for chanel mode selection
		for widget in self.settingsTab.findChildren(QComboBox):	
			if "mode_sel" in widget.objectName():
				widget.currentTextChanged.connect(partial(self.chModeSet, widget))
					
		# checkboxes for chanel enabling
		for widget in self.settingsTab.findChildren(QCheckBox):	
			if "datalogger" in widget.objectName() and "enabled" in widget.objectName():
				widget.stateChanged.connect(partial(self.chEnable, widget))
				value = self.settings.value("settings/"+str(widget.objectName()), False, type=bool)
				widget.setChecked(value)
				
		# restore saved settings for checkboxes
		for widget in self.settingsTab.findChildren(QCheckBox):	
			if "datalogger" in widget.objectName() and "enabled" in widget.objectName():
				value = self.settings.value("settings/"+str(widget.objectName()), False, type=bool)
				if value == True:
					widget.setChecked(value)
					
		# restore saved settings for comboboxes
		for widget in self.settingsTab.findChildren(QComboBox):	
			if "mode_sel" in widget.objectName():
				value = self.settings.value("settings/"+str(widget.objectName()), -1, type=int)
				if value != -1:
					widget.setCurrentIndex(value)
		
		# set up shortcut q to exit
		self.actionQuit.triggered.connect(self.quit)
		self.actionQuit.setShortcut('Q')
		
		# assign functions to buttons
		self.apply_settings_btn.clicked.connect(self.applySettings)
		self.start_sampling_btn.clicked.connect(self.startSampling)
		
		# plot data on tab "All"
		self.headers = genHeaders(self.channelEnabledArr)
		self.allMplWidget.canvas.setLayout(self.headers)
		
		self.dataToPlot = np.empty((1, 5+1))
		
		self.customSelectionCheckBoxArr = {}
		self.customMplWidgetArr = {}
		self.customStartDateTimeButtonArr = {}
		self.customEndDateTimeButtonArr = {}
		self.selectedHeaders = {}
		# add custom tabs needed after tab "All"
		self.tabWidget.setCurrentIndex(self.tabWidget.count()-1)
		addCustomTabs(self, self.customTabCount.value()-1)
		self.restoreTabNames()
		
		# get settings to restore checkboxes 
		self.selectedPlotNo = {}
		# collect checkboxes from 1st custom tab
		checkBoxes = {}
		for i in range(self.gridLayout_6.count()):
			checkBoxes[i] = self.gridLayout_6.itemAt(i).widget()
		self.customSelectionCheckBoxArr[0] = checkBoxes.copy()
			
		for i in range(len(self.customSelectionCheckBoxArr)):
			for j in range(len(self.customSelectionCheckBoxArr[i])):
				checkBox = self.customSelectionCheckBoxArr[i][j]
				attr = "custom_tab_%d_selection/" % (i)
				checkBox.setChecked(self.settings.value(attr+checkBox.text(), False, type=bool))
				# connect the slot to the signal by clicking the checkbox to save the state settings
				checkBox.clicked.connect(partial(self.saveCheckBoxSettings, checkBox, i))
				checkBox.stateChanged.connect(self.checkCheckboxes)
			
			
		self.customTabCount.valueChanged.connect(self.updateCustomTabCount)
		# plot custom plots according to checkboxes
		self.checkCheckboxes()
		
		# enable renaming custom tabs
		self.tabNameEditor = QLineEdit(self)
		self.tabNameEditor.setWindowFlags(QtCore.Qt.Popup)
		self.tabNameEditor.setFocusProxy(self)
		self.tabNameEditor.editingFinished.connect(self.handleTabEditingFinished)
		self.tabNameEditor.installEventFilter(self)
		self.tabWidget.tabBarDoubleClicked.connect(self.tabDoubleClickEvent)
		
		self.customMplWidgetArr[0] = self.customMplWidget
		self.showMaximized()
		
		
	def restoreTabNames(self):
		# Get settings to restore tab names 	
		for id in range(2, self.tabWidget.count()-1):
			name = self.settings.value("tab_names/tab"+str(id), "none", type=str)
			if name != "none":
				self.tabWidget.tabBar().setTabText(id, name)
			
	"""
	Detects double click on tab name and enables renaming
	This method does not affect tabs 0-1 and last tab
	"""
	def tabDoubleClickEvent(self):
		id = self.tabWidget.tabBar().currentIndex()
		if id >= 2 and id < self.tabWidget.count()-1:
			self.editTab(id)
		
	def editTab(self, id):
		rect = self.tabWidget.tabBar().tabRect(id)
		self.tabNameEditor.setFixedSize(rect.size())
		self.tabNameEditor.move(self.mapToGlobal(rect.topLeft()))
		self.tabNameEditor.setText(self.tabWidget.tabBar().tabText(id))
		if not self.tabNameEditor.isVisible():
			self.tabNameEditor.show()
			
	def handleTabEditingFinished(self):
		id = self.tabWidget.tabBar().currentIndex()
		if id >= 0:
			self.tabNameEditor.hide()
			self.tabWidget.tabBar().setTabText(id, self.tabNameEditor.text())
			self.saveTabNames(id, self.tabNameEditor.text())
			
	def saveCheckBoxSettings(self, checkBox, index):
		attr = "custom_tab_%d_selection/" % (index)
		self.settings.setValue(attr+checkBox.text(), checkBox.isChecked())
		self.settings.sync()
		
	def saveTabNames(self, id, name):
		self.settings.setValue("tab_names/tab"+str(id), name)
		self.settings.sync()
		
	def checkCheckboxes(self):
		for j in range(0, len(self.customSelectionCheckBoxArr)):
			checkBoxes = self.customSelectionCheckBoxArr[j]
			try:
				tabSelection = self.selectedPlotNo[j]
			except:
				tabSelection = []
					
			for i in range(0, len(checkBoxes)):
				
				index = int(checkBoxes[i].text().split(" ")[1])-1
				if checkBoxes[i].isChecked():
					if index not in tabSelection:
						tabSelection.append(index)
				else:
					if index in tabSelection:
						tabSelection.remove(index)
			
			self.selectedHeaders[j] = [self.headers[0]]
			tabSelection.sort()
			for i in tabSelection:
				self.selectedHeaders[j].append(channelNumbering[i])
		
			self.selectedPlotNo[j] = tabSelection
			
			
		#self.plotCustomData()
		
	def plotCustomData(self):
		for i in self.getCustomTabRange():
			#try:
			widget = self.customMplWidgetArr[i]
			widget.canvas.cla()
			widget.canvas.draw()
			# do not plot if only time series provided
			if len(self.selectedHeaders[i]) == 1:
				continue
			if self.selectedHeaders[i] != []:
				widget.canvas.initAxes()
				widget.canvas.setLayout(self.selectedHeaders[i])
				log.debug("Will plot for tab %d: %s", i, str(self.selectedHeaders[i]))
				widget.canvas.plot3(self.selectedHeaders[i], self.dataToPlot)
			# except Exception as e:
				# log.error("Something failed at plotting %d tab" % (i))
				# log.error(str(e))
		
	def getCustomTabRange(self):
		endIndex = self.tabWidget.count() - 3
		return range(0, endIndex)
		
	def updateCustomTabCount(self):
		oldCustomTabCount = self.tabWidget.count() - 3
		if self.customTabCount.value() > oldCustomTabCount:
			# add additional tabs
			tabsToAdd = self.customTabCount.value() - oldCustomTabCount
			startIndex = oldCustomTabCount + 2
			addCustomTabs(self, tabsToAdd, startIndex)
			self.restoreTabNames()
			#self.plotCustomData()
		elif self.customTabCount.value() < oldCustomTabCount:
			# delete tabs
			tabsToDelete =  oldCustomTabCount - self.customTabCount.value()
			indexTo = oldCustomTabCount + 2
			indexFrom = indexTo - tabsToDelete
			
			for i in range(indexFrom, indexTo):
				self.tabWidget.removeTab(i)
				
		self.setupCustomTabs()
		
	def setupCustomTabs(self):
		pass
		# for i in self.getCustomTabRange():
			# self.customStartDateTimePickerArr[i] = DateTimePicker(self, self.customStartDateTimeButtonArr[i], self.defaultStartDateTime, title = "Select start datetime for plotting custom data") 
			# self.customEndDateTimePickerArr[i] = DateTimePicker(self, self.customEndDateTimeButtonArr[i], self.defaultEndDateTime, title = "Select end datetime for plotting custom data") 
			# self.customStartDateTimeButtonArr[i].clicked.connect(partial(self.onCustomStartDateTimeClicked, picker = self.customStartDateTimePickerArr[i]))
			# self.customEndDateTimeButtonArr[i].clicked.connect(partial(self.onCustomEndDateTimeClicked, picker = self.customEndDateTimePickerArr[i]))
			
			# self.customStartDateTimePickerArr[i].dateTimeEdit.dateTimeChanged.connect(self.onCustomDateTimeChanged)
			# self.customEndDateTimePickerArr[i].dateTimeEdit.dateTimeChanged.connect(self.onCustomDateTimeChanged)
		
	def chEnable(self, checkbox):
		ch = checkbox.objectName().split('_')[1]
		self.channelEnabledArr[channelMapping[ch]-1] = checkbox.isChecked()
		
		self.settings.setValue("settings/"+ checkbox.objectName(), checkbox.isChecked())
		self.settings.sync()
		
	def chModeSet(self, comboBox):	
		self.settings.setValue("settings/"+ comboBox.objectName(), comboBox.currentIndex())
		self.settings.sync()
		
		ch = comboBox.objectName().split('_')[-1]	
		mode = comboBox.currentText()
		self.removeOptions(ch)
		if mode == "Diode":
			self.insertDiodeOptions(ch, mode)
		elif mode == "RTD PT-1000":
			self.insertRTDOptions(ch, mode)
		elif mode == "Sense Resistor":
			self.insertResistorOptions(ch, mode)
			
	def insertResistorOptions(self, ch, mode):
		if self.channelSettingWidgetsArr[channelMapping[ch]-1] != []:
			return
			
		resistanceLineEdit = QtWidgets.QLineEdit(objectName = "resQLineEdit_%s" % ch)
		resistanceLineEdit.setText("%f" % (DEFAULT_RESISTANCE))
		
		settingsWidgets = [mode, resistanceLineEdit]
		
		self.channelSettingWidgetsArr[channelMapping[ch]-1] = settingsWidgets
		
		layouts = self.settingsTab.findChildren(QHBoxLayout)
		for layout in layouts:	
			if ch+"_" in layout.objectName() and "settings_layout" in layout.objectName():
				no = int(layout.objectName().split("_")[-1])
				if no == 1:
					label = QtWidgets.QLabel()
					label.setText("R (Ohm) = ")
					layout.addWidget(label)
					self.channelLabelWidgetsArr[channelMapping[ch]-1].append(label)
					layout.addWidget(settingsWidgets[no])
					settingsWidgets[no].textChanged.connect(partial(self.saveQLineEdit, settingsWidgets[no]))
					break
										
		# restore channel settings widgets if possible
		for widget in settingsWidgets:
			if type(widget) == str:
				continue
			elif isinstance(widget, QLineEdit):
				value = self.settings.value("settings/"+str(widget.objectName()), "", type=str)
				if value != "":
					widget.setText(value)
		
	def insertRTDOptions(self, ch, mode):
		if self.channelSettingWidgetsArr[channelMapping[ch]-1] != []:
			return
		
		senseResComboBox = QtWidgets.QComboBox(objectName = "senseResQComboBox_%s" % ch)
		senseResComboBox.addItems([
							"Sense R @ CH2-CH1", 
							"Sense R @ CH3-CH2", 
							"Sense R @ CH4-CH3", 
							"Sense R @ CH5-CH4", 
							"Sense R @ CH6-CH5", 
							"Sense R @ CH7-CH6", 
							"Sense R @ CH8-CH7", 
							"Sense R @ CH9-CH8", 
							"Sense R @ CH10-CH9",
						])
						
		numWireComboBox = QtWidgets.QComboBox(objectName = "numWireQComboBox_%s" % ch)
		numWireComboBox.addItems([
							"2-wire", 
							"3-wire", 
							"4-wire", 
							"4-wire, Kelvin Rsense", 
						])
						
		excitModeComboBox = QtWidgets.QComboBox(objectName = "excitModeQComboBox_%s" % ch)
		excitModeComboBox.addItems([
							"No rotation/sharing",
							"No rotation/no sharing",
							"Rotation/sharing",
						])
						
		excitCurrentComboBox = QtWidgets.QComboBox(objectName = "excitCurrentQComboBox_%s" % ch)
		excitCurrentComboBox.addItems([
							"100uA",
							"external",
							"5uA",
							"10uA",
							"25uA",
							"50uA",
							"250uA",
							"500uA",
							"1mA",
						])
						
		standardComboBox = QtWidgets.QComboBox(objectName = "standardQComboBox_%s" % ch)
		standardComboBox.addItems(["European", "American", "Japanese", "ITS-90"])
		
		settingsWidgets = [mode, senseResComboBox, numWireComboBox, excitModeComboBox, excitCurrentComboBox, standardComboBox]
		self.channelSettingWidgetsArr[channelMapping[ch]-1] = settingsWidgets
		
		layouts = self.settingsTab.findChildren(QHBoxLayout)
		for layout in layouts:	
			if ch+"_" in layout.objectName() and "settings_layout" in layout.objectName():
				no = int(layout.objectName().split("_")[-1])
				layout.addWidget(settingsWidgets[no])
				settingsWidgets[no].currentIndexChanged.connect(partial(self.saveQComboBox, settingsWidgets[no]))
				
		# restore channel settings widgets if possible
		for widget in settingsWidgets:
			if type(widget) == str:
				continue
			elif isinstance(widget, QComboBox):
				value = self.settings.value("settings/"+str(widget.objectName()), -1, type=int)
				if value != -1:
					widget.setCurrentIndex(value)
		
	def insertDiodeOptions(self, ch, mode):
		if self.channelSettingWidgetsArr[channelMapping[ch]-1] != []:
			return
			
		diffComboBox = QtWidgets.QComboBox(objectName = "diffQComboBox_%s_%s" % (mode, ch))
		diffComboBox.addItems(["Single", "Diff"])
		numReadingsComboBox = QtWidgets.QComboBox(objectName = "numReadingsQComboBox_%s_%s" % (mode, ch))
		numReadingsComboBox.addItems(["3 readings", "2 readings"])
		averagingComboBox = QtWidgets.QComboBox(objectName = "averagingQComboBox_%s_%s" % (mode, ch))
		averagingComboBox.addItems(["AVG on", "AVG off"])
		currentComboBox = QtWidgets.QComboBox(objectName = "currentQComboBox_%s_%s" % (mode, ch))
		currentComboBox.addItems([
							"10uA/40uA/80uA", 
							"20uA/80uA/160uA",
							"40uA/160uA/320uA",
							"80uA/320uA/640uA"
						])
		idealityLineEdit = QtWidgets.QLineEdit(objectName = "idealityComboBox_%s_%s" % (mode, ch))
		idealityLineEdit.setText("%f" % (DEFAULT_IDEALITY))
		
		settingsWidgets = [mode, diffComboBox, numReadingsComboBox, averagingComboBox, currentComboBox, idealityLineEdit]
		self.channelSettingWidgetsArr[channelMapping[ch]-1] = settingsWidgets

		layouts = self.settingsTab.findChildren(QHBoxLayout)
		for layout in layouts:	
			if ch+"_" in layout.objectName() and "settings_layout" in layout.objectName():
				no = int(layout.objectName().split("_")[-1])
				if no == 5:
					label = QtWidgets.QLabel()
					label.setText("Ideality = ")
					self.channelLabelWidgetsArr[channelMapping[ch]-1].append(label)
					layout.addWidget(label)
				layout.addWidget(settingsWidgets[no])
				if isinstance(settingsWidgets[no], QComboBox):
					settingsWidgets[no].currentIndexChanged.connect(partial(self.saveQComboBox, settingsWidgets[no]))
				elif isinstance(settingsWidgets[no], QLineEdit):
					settingsWidgets[no].textChanged.connect(partial(self.saveQLineEdit, settingsWidgets[no]))
					
		# restore channel settings widgets if possible
		for widget in settingsWidgets:
			if type(widget) == str:
				continue
			elif isinstance(widget, QComboBox):
				value = self.settings.value("settings/"+str(widget.objectName()), -1, type=int)
				if value != -1:
					widget.setCurrentIndex(value)	
			elif isinstance(widget, QLineEdit):					
				value = self.settings.value("settings/"+str(widget.objectName()), "", type=str)
				if value != "":
					widget.setText(value)
					
	def removeOptions(self, ch):
		settingsWidgets = self.channelSettingWidgetsArr[channelMapping[ch]-1]
		for widget in settingsWidgets:
			if type(widget) == str:
				continue
			widget.deleteLater()
			
		labelWidgets = self.channelLabelWidgetsArr[channelMapping[ch]-1]
		for widget in labelWidgets:
			widget.deleteLater()
			
		self.channelLabelWidgetsArr[channelMapping[ch]-1] = []
		self.channelSettingWidgetsArr[channelMapping[ch]-1] = []	
	
	def applySettings(self):
		self.start_sampling_btn.setEnabled(True)
		self.appendDataloggerTextBox("Applying following settings")
		with LTC2986(port = self.datalogger_port.text()) as datalogger:
			for i in range(0, len(self.channelSettingWidgetsArr)):
				settings = self.channelSettingWidgetsArr[i]
				if settings == []:
					continue
					
				ch = channelNumbering[i]
				mode = settings[0]
				if mode == "Sense Resistor":
					resistance = float(settings[1].text())
					self.appendDataloggerTextBox("%s set as %s with \n\tR = %f" % (ch, mode, resistance))
					datalogger.setResitor(ch, resistance)
				elif mode == "RTD PT-1000":
					senseResistor = senseResMapping[settings[1].currentText()]
					wire = wireMapping[settings[2].currentText()]
					excitationMode = excitationMapping[settings[3].currentText()]
					excitationCurrent = excitationCurrentMapping[settings[4].currentText()]
					rtdCurve = rtdCurveMapping[settings[5].currentText()]
					self.appendDataloggerTextBox("%s set as %s with \n\tsenseResistor = %s \n\twire = %s \n\texcitationMode = %s \n\texcitationCurrent = %s \n\trtdCurve = %s" % (ch, mode, senseResistor, wire, excitationMode, excitationCurrent, rtdCurve))
					datalogger.setRTD(ch, 
									senseResistor = senseResistor, 
									wire = wire,
									excitationMode = excitationMode, 
									excitationCurrent = excitationCurrent, 
									rtdCurve = rtdCurve)
				elif mode == "Diode":
					single = diffMapping[settings[1].currentText()]
					readCount = numReadingsMapping[settings[2].currentText()]
					avgOn = averagingMapping[settings[3].currentText()]
					excitationCurrent = diodeCurrentMapping[settings[4].currentText()]
					ideality = float(settings[5].text())
					self.appendDataloggerTextBox("%s set as %s with \n\tsingle = %s \n\treadCount = %s \n\tavgOn = %s \n\texcitationCurrent = %s \n\tideality = %f" % (ch, mode, single, readCount, avgOn, excitationCurrent, ideality))
					datalogger.setDiode(ch, 
							single = single,
							readCount = readCount,
							avgOn = avgOn,
							excitationCurrent = excitationCurrent,
							ideality = ideality)
							
			self.appendDataloggerTextBox("Settings applied")
			
			self.channelsToRead = []
			for i in range(0, len(self.channelEnabledArr)):
				status = self.channelEnabledArr[i]
				if status:
					ch = channelNumbering[i]
					self.appendDataloggerTextBox("Will enable %s" % (ch))
					self.channelsToRead.append(ch)
		
			datalogger.selectChannels(self.channelsToRead)
			
	def displayResult(self, resultArr):
		for i in range(0, len(resultArr)):
			ch = self.channelsToRead[i]
			r = resultArr[i]
			widget = getattr(self, "%s_val" % ch)
			widget.setText("%.10f" % r)

	def statusListToString(self, statusList):
		retVal = ""
		for s in statusList:
			retVal += (s + '; ')
		retVal = retVal[:-2] 
		return retVal
		
	def rawListToString(self, rawList):
		retVal = ""
		for r in rawList:
			retVal += str(r)+","
			
		retVal = retVal[:-1] 
		return retVal
	
	def displayStatus(self, statusArr):
		for i in range(0, len(statusArr)):
			ch = self.channelsToRead[i]
			s = statusArr[i]
			widget = getattr(self, "%s_status" % ch)
			widget.setText(s)		
	
	def _samplingThread(self):
		with LTC2986(port = self.datalogger_port.text()) as datalogger:
			firstTime = True
			newLinesAdded = 0
			totalLinesAdded = 0
			while self.start_sampling_btn.text() == "Stop sampling":	
				datalogger.initiateCorvesion("multiple")
				datalogger.waitConversion()
				resultArr = []
				statusArr = []
				rawArr = []
				for ch in self.channelsToRead:
					data = datalogger.readChannelData(ch)
					resultArr.append(datalogger.convertRawToTemperature(data))
					statusArr.append(self.statusListToString(datalogger.getStatusMsg(data)))
					rawArr.append(data)
					
				###
				time = np.datetime64(datetime.now())
				newrow = [time, resultArr[0], resultArr[1], resultArr[2], resultArr[3], resultArr[4]]
				if firstTime:
					self.dataToPlot  = np.array([newrow])
					firstTime = False
				else:
					self.dataToPlot = np.vstack([self.dataToPlot, newrow])
				newLinesAdded += 1
				totalLinesAdded += 1
				
				if newLinesAdded == 3:
					self.allMplWidget.canvas.plot2(self.headers, self.dataToPlot)
					self.plotCustomData()
					newLinesAdded = 0
				
				if totalLinesAdded > 50000:
					totalLinesAdded = 0
					newLinesAdded = 0
					firstTime = True
					self.dataToPlot = np.empty((1, 5+1))
				
				###			
				self.displayResult(resultArr)
				self.displayStatus(statusArr)
				
				measurString = ""
				for r in resultArr:
					measurString += ",%.10f" % (r)
					
				statusString = ""
				for s in statusArr:
					statusString += (s)+","
				if "range" in statusString or "fault" in statusString:
					if TELEGARM_MODE:
						telegram_bot_sendtext("Some faulty measurements: %s" % (statusString))
				statusString = statusString[:-1] 
					
				raw = self.rawListToString(rawArr)
				logMeasurement(measurString, statusString, raw = raw, expName = self.expName.text())
	
	def startSampling(self):
		if self.start_sampling_btn.text() == "Start sampling":
			self.apply_settings_btn.setEnabled(False)
			self.appendDataloggerTextBox("Starting sampling")
			self.samplingThread = threading.Thread(target=self._samplingThread)
			self.samplingThread.daemon = True
			self.start_sampling_btn.setText("Stop sampling")
			self.samplingThread.start()
		elif self.start_sampling_btn.text() == "Stop sampling":
			self.appendDataloggerTextBox("Stopping sampling")
			self.start_sampling_btn.setText("Start sampling")
			try:
				self.samplingThread.join()
			except Exception as e:
				log.warning(str(e))
			self.apply_settings_btn.setEnabled(True)
			
	
	def saveQLineEdit(self, widget):
		self.settings.setValue("settings/"+ widget.objectName(), widget.text())
		self.settings.sync()
		
	def saveQComboBox(self, widget):
		self.settings.setValue("settings/"+ widget.objectName(), widget.currentIndex())
		self.settings.sync()
		
	def saveQSpinBox(self, widget):
		self.settings.setValue("settings/"+ widget.objectName(), widget.value())
		self.settings.sync()
		
	def appendDataloggerTextBox(self, text):
		verScrollBar = self.dataloggerTextResponse.verticalScrollBar()
		horScrollBar = self.dataloggerTextResponse.horizontalScrollBar()
		scrollIsAtEnd = verScrollBar.maximum() - verScrollBar.value() <= 10
		
		self.dataloggerTextResponse.append(text)
		
		if scrollIsAtEnd:
			verScrollBar.setValue(verScrollBar.maximum()) # Scrolls to the bottom
			horScrollBar.setValue(0) # scroll to the left
			
		logString(text, expName = self.expName.text(), telemetry = True)
		if TELEGARM_MODE:
			telegram_bot_sendtext(text)
	
	def quit(self):
		try:
			self.datalogger.close()
			self.datalogger_connect_btn.setText("Open connection")
		except:
			pass
		sys.exit(0)

if __name__ == "__main__":
	#parse input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--verbosity', action="count", 
                        help="-v: WARNING, -vv: INFO, -vvv: DEBUG")
	parser.add_argument("-o", "--offline", action="store_true", default=False, 
						help="specify if exclude network communication")
	parser.add_argument("-t", "--telegram", action="store_true", default=False, 
						help="enable sending telegramm messsages to GUI author for debug")
	args = parser.parse_args()
	
	#setup verbosity level
	if args.verbosity:
		if args.verbosity >= 3:
			log.basicConfig(format=LOG_FORMAT,  datefmt=TIMESTAMP_FORMAT, level=log.DEBUG)
		elif args.verbosity == 2:
			log.basicConfig(format=LOG_FORMAT, datefmt=TIMESTAMP_FORMAT, level=log.INFO)
		elif args.verbosity == 1:
			log.basicConfig(format=LOG_FORMAT, datefmt=TIMESTAMP_FORMAT, level=log.WARNING)
		else:
			log.basicConfig(format=LOG_FORMAT, datefmt=TIMESTAMP_FORMAT, level=log.ERROR)
			
	if args.telegram:
		TELEGARM_MODE = True

	log.getLogger('matplotlib.font_manager').disabled = True
	app = QtWidgets.QApplication(sys.argv)
	window = MyApp(offline = args.offline)
	window.show()
	sys.exit(app.exec_())