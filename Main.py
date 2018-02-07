import wx
import wx.lib.buttons as buttons
from wx.lib.delayedresult import startWorker
import time
from pyModbusTCP.client import ModbusClient
import threading
import numpy as np
from collections import deque

class MainForm:
    maxHR = 256
    maxCR = 256

    mbHR = [9999] * maxHR
    mbCR = [True] * maxCR

    manQ = []

    pollcount = 0

    d = {
        'Heat Override': ['heatoverride', 'button', 'w', 'sc', 1, 1],
        'Heat Control': ['heatcontrol', 'button', 'w', 'sc', 2, 1],
    }

    port = 502  # 1504
    host = "10.0.0.193"
    #port = 1504
    #host = "10.0.0.11"
    c = ModbusClient(host=host, port=port, auto_open=True, debug=True, auto_close=True, timeout=5)

    def __init__(self, *args, **kwargs):

        self.n = 100
        self.xqueue = deque('')
        self.runningMean = 0
        self.current_time = 0
        self.elapsed_time = 0
        self.saved_time = 0
        self.millis = 0
        self.frame = wx.Frame(*args, **kwargs, size=(1280, 1024), )
        self.frame.Center()
        self.panel = wx.Panel(self.frame)
        self.jobID = 0
        self.packetIterator = 0

        # fonts
        largeFont = wx.Font(34, wx.ROMAN, wx.NORMAL, wx.NORMAL)

        # labels
        # self.miscLbl = wx.StaticText(self.panel, -1, pos=(10,30),size = (120,20))
        self.tmpLbl_1 = wx.StaticText(self.panel, -1, pos=(10, 10), size=(120, 20))
        self.tmpLbl_1.SetLabel('Temperature')
        self.temperatureLbl = wx.StaticText(self.panel, -1, pos=(30, 20), size=(120, 20))
        self.temperatureLbl.SetFont(largeFont)

        self.tmpLbl_2 = wx.StaticText(self.panel, -1, pos=(20, 60), size=(120, 20))
        self.tmpLbl_2.SetLabel('Humdity')
        self.humidityLbl = wx.StaticText(self.panel, -1, pos=(30, 70), size=(120, 20))
        self.humidityLbl.SetFont(largeFont)

        self.tmpLbl_2 = wx.StaticText(self.panel, -1, pos=(10, 110), size=(120, 20))
        self.tmpLbl_2.SetLabel('Light Sensor')
        self.lightLbl = wx.StaticText(self.panel, -1, pos=(30, 130), size=(120, 20))
        self.lightLbl.SetFont(largeFont)

        self.tmpLbl_3 = wx.StaticText(self.panel, -1, pos=(10, 250), size=(120, 20))
        self.tmpLbl_3.SetLabel('Packet Time')
        self.packetTime = wx.StaticText(self.panel, -1, pos=(100, 250), size=(120, 20))

        self.tmpLbl_4 = wx.StaticText(self.panel, -1, pos=(10, 280), size=(120, 20))
        self.tmpLbl_4.SetLabel('Poll Count')
        self.pollCount = wx.StaticText(self.panel, -1, pos=(100, 280), size=(120, 20))

        self.tmpLbl_5 = wx.StaticText(self.panel, -1, pos=(10, 310), size=(120, 20))
        self.tmpLbl_5.SetLabel('ESP ID')
        self.lbl_espID = wx.StaticText(self.panel, -1, pos=(100, 310), size=(120, 20))

        #comment

        # bitmaps
        self.PilotLightGreenOn = wx.Image("PilotLightGreenOn.bmp")
        self.PilotLightGreenOn = self.PilotLightGreenOn.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)

        self.PilotLightRedOn = wx.Image("PilotLightRedOn.bmp")
        self.PilotLightRedOn = self.PilotLightRedOn.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)

        self.ctrlsHreg = []
        self.ctrlsHreg.append('')
        for i in range(1, 42):
            setattr(self, "labelCtrlHreg%s" % (i),
                    wx.StaticText(self.panel, -1, label='hReg' + str(i), pos=(300, 20 * (i - 1)), name='lblHreg' + str(i)))
            self.ctrlsHreg.append(wx.StaticText(self.panel, -1, label='', pos=(400, 20 * (i - 1)),
                                                name=''))

        for i in range(42, 85):
            setattr(self, "labelCtrlHreg%s" % (i),
                    wx.StaticText(self.panel, -1, label='hReg' + str(i), pos=(500, 20 * (i - 43)), name='lblHreg' + str(i)))
            self.ctrlsHreg.append(wx.StaticText(self.panel, -1, label='', pos=(600, 20 * (i - 43)),
                                                name=''))

        for i in range(85, 129):
            setattr(self, "labelCtrlHreg%s" % (i),
                    wx.StaticText(self.panel, -1, label='hReg' + str(i), pos=(700, 20 * (i - 86)), name='lblHreg' + str(i)))
            self.ctrlsHreg.append(wx.StaticText(self.panel, -1, label='', pos=(800, 20 * (i - 86)),
                                                name=''))
        self.labelCtrlHreg1.SetLabel("Light sensor")
        self.labelCtrlHreg2.SetLabel("Temperature")
        self.labelCtrlHreg3.SetLabel("Humidity")
        self.labelCtrlHreg4.SetLabel("Heat pulse")
        self.labelCtrlHreg5.SetLabel("Cool pulse")
        self.labelCtrlHreg6.SetLabel("Fan pulse")
        self.labelCtrlHreg100.SetLabel("DHT TimeOut")
        self.labelCtrlHreg101.SetLabel("DHT Checksum")
        self.labelCtrlHreg102.SetLabel("DHT Status")
        self.labelCtrlHreg103.SetLabel("Error BLINK")
        self.labelCtrlHreg104.SetLabel("Wifi Status")
        self.labelCtrlHreg105.SetLabel("Therm Status")
        self.labelCtrlHreg106.SetLabel("Reset Rsn")
        self.labelCtrlHreg107.SetLabel("Chip ID")
        #self.labelCtrlHreg108.SetLabel("Chip ID low")

        self.ctrlsCoil = []
        for i in range(1, 33):
            setattr(self, "labelCtrlCoil%s" % i,
                    (wx.StaticText(self.panel, -1, label='Coil' + str(i), pos=(850, 20 * i), name='lblCoil' + str(i))))
            self.ctrlsCoil.append(wx.StaticText(self.panel, -1, label='', pos=(950, 20 * i),
                                                name=''))

        self.labelCtrlCoil1.SetLabel("Heat overrider")
        self.labelCtrlCoil2.SetLabel("Heat control")
        self.labelCtrlCoil3.SetLabel("Cool override")
        self.labelCtrlCoil4.SetLabel("Cool control")
        self.labelCtrlCoil5.SetLabel("Fan overrride")
        self.labelCtrlCoil6.SetLabel("Fan control")
        self.labelCtrlCoil7.SetLabel("Heat call")
        self.labelCtrlCoil8.SetLabel("Cool call")
        self.labelCtrlCoil9.SetLabel("Fan call")
        self.labelCtrlCoil10.SetLabel("Heat call")

        self.ctrlsBitmaps = []
        for i in range(1, 33):
            self.ctrlsBitmaps.append(
                wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap(self.PilotLightRedOn), pos=(265, i * 25),
                                size=(20, 20)))

        # buttons
        self.btn_heatoverrride = buttons.GenButton(self.panel, name="Heat Override", pos=(140, 25), size=(120, 20))
        self.btn_heatcontrol = buttons.GenButton(self.panel, name='Heat Control', pos=(140, 50), size=(120, 20))
        self.btn_cooloverrride = buttons.GenButton(self.panel, name="Cool Override", pos=(140, 75),
                                                   size=(120, 20))
        self.btn_coolcontrol = buttons.GenButton(self.panel, name='Cool Control', pos=(140, 100), size=(120, 20))
        self.btn_fanoverrride = buttons.GenButton(self.panel, name="Fan Override", pos=(140, 125), size=(120, 20))
        self.btn_fancontrol = buttons.GenButton(self.panel, name='Fan Control', pos=(140, 150), size=(120, 20))

        #self.btn_restartESP = buttons.GenButton(self.panel, name='Restart ESP', pos=(500, 30), size=(120, 20))
        #self.btn_restartESP.SetLabel("Restart ESP")

        self.btn_heatoverrride.SetLabel("Heat Override")
        self.btn_heatcontrol.SetLabel("Heat Control")
        self.btn_cooloverrride.SetLabel("Cool Override")
        self.btn_coolcontrol.SetLabel("Cool Control")
        self.btn_fanoverrride.SetLabel("Fan Override")
        self.btn_fancontrol.SetLabel("Fan Control")
        #self.btn_restartESP.SetLabel("Restart ESP")

        self.lightGauge = wx.Gauge(self.panel, range=1024, pos=(10, 115), size=(100, 25), style=wx.GA_HORIZONTAL)

        # events
        self.btn_heatoverrride.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.btn_heatcontrol.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.btn_cooloverrride.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.btn_coolcontrol.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.btn_fanoverrride.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.btn_fancontrol.Bind(wx.EVT_BUTTON, self.OnClicked)
        #self.btn_restartESP.Bind(wx.EVT_BUTTON, self.OnPress)

        # start thread
        startWorker(self.modbusAutoPollingOver, self.modbusAutoPolling)


    # **********************************************************************************************************************
    def rolling_avg(self, x):
        # if the queue is empty then fill it with values of x
        if (self.xqueue == deque([])):
            for i in range(self.n):
                self.xqueue.append(x)
        self.xqueue.append(x)
        self.xqueue.popleft()
        avg = 0
        for i in self.xqueue:
            avg += i
        avg = avg / float(self.n)
        #print("Rolling Avg:")
        #for i in self.xqueue:
        #    print(i)
        #    print("avg: %f" % avg)
        return avg

    # **********************************************************************************************************************
    def OnPress(self, event):
        btn = event.GetEventObject().GetName()
        print("Name of pressed button = ", btn)

        if btn == "Restart ESP":
            wx.CallAfter(self.sendModbus, 'w', 'sc', 11, 1, 1)
            wx.CallAfter(self.sendModbus, 'r', 'sc', 11, 1, 1)

    # **********************************************************************************************************************
    def OnClicked(self, event):
        btn = event.GetEventObject().GetName()
        print("Name of pressed button = ", btn)

        if btn == "Heat Override":
            value = self.mbCR[1]
            print('mbCR value', value)
            value = not value
            print('mbCR new value', value)
            t = (['w', 'sc', 1, 1, value])

        if btn == "Heat Control":
            value = self.mbCR[2]
            print('mbCR value', value)
            value = not value
            print('mbCR new value', value)
            t = (['w', 'sc', 2, 1, value])

        if btn == "Cool Override":
            value = self.mbCR[3]
            print('mbCR value', value)
            value = not value
            print('mbCR new value', value)
            t = (['w', 'sc', 3, 1, value])

        if btn == "Cool Control":
            value = self.mbCR[4]
            print('mbCR value', value)
            value = not value
            print('mbCR new value', value)
            t = (['w', 'sc', 4, 1, value])

        if btn == "Fan Override":
            value = self.mbCR[5]
            print('mbCR value', value)
            value = not value
            print('mbCR new value', value)
            t = (['w', 'sc', 5, 1, value])

        if btn == "Fan Control":
            value = self.mbCR[6]
            print('mbCR value', value)
            value = not value
            print('mbCR new value', value)
            t = (['w', 'sc', 6, 1, value])

        self.manQ.append(t)

    # **********************************************************************************************************************
    def modbusAutoPolling(self):

        wx.Yield()

        self.millis = int(round(time.time() * 1000))
        self.elapsed_time = self.millis - self.saved_time
        self.saved_time = self.millis
        self.runningMean = self.rolling_avg(self.elapsed_time)

        print('Average packet time :', self.runningMean)
        print("Modbus Auto Poll", self.elapsed_time)
        self.packetTime.SetLabel(str(self.runningMean))

        self.pollCount.SetLabel(str(self.pollcount))
        self.pollcount = self.pollcount + 1
        print('Poll Count:' , self.pollcount)

        print('Auto Poll Running')

        self.packetIterator = self.packetIterator + 1

        if self.packetIterator == 1:
            t = (['r', "mh", 1, 32, 1])
            print('Updating Modbus hRegs 1 - 32')
        if self.packetIterator == 2:
            t = (['r', "mh", 33, 32, 1])
            print('Updating Modbus hRegs 33 - 65')
        if self.packetIterator == 3:
            t = (['r', "mh", 65, 32, 1])
            print('Updating Modbus hRegs 65 - 97')
        if self.packetIterator == 4:
            t = (['r', "mh", 97, 31, 1])
            print('Updating Modbus hRegs 97 - 129')
        if self.packetIterator == 5:
            t = (['r', "mc", 1, 32, 1])
            print('Updating Modbus Coils 1 - 32')
            self.packetIterator = 0

        ret = self.sendModbus(t)
        # print('Auto Poll Returned Data', ret)
        wx.CallAfter(self.updateScreen(t, ret))


    # **********************************************************************************************************************
    def modbusAutoPollingOver(self, something):

        print('Something:', something)
        print('Checking for Queued Items')
        if self.manQ:
            print('Sending queued item...')
            temp = self.manQ.pop()
            ret = self.sendModbus(temp)
            # print('Queue process returned data' , ret)
            wx.CallAfter(self.updateScreen, temp, ret)
            print('Starting worker in poll over queued item...')
            startWorker(self.modbusAutoPollingOver, self.modbusAutoPolling)
        else:
            print('No queued items...')
            print('Starting worker in poll over no queued item...')
            startWorker(self.modbusAutoPollingOver, self.modbusAutoPolling)

    # **********************************************************************************************************************
    def updateScreen(self, mbData, returnData):

        print("Updating screen...")

        readWrite = mbData[0]
        mbType = mbData[1]
        mbAddress = mbData[2]
        numRegs = mbData[3]
        mbData = mbData[4]

        # print('R/W:' + readWrite + ' Type:' + mbType + ' Addr:' + str(mbAddress) + ' numRegs:' + str(
        #   numRegs) + ' mbData:' + str(mbData))

        print('Data sent to screen update:'),
        # print(returnData)

        if mbType == 'sc':  # single coil
            if readWrite == 'w':
                print('not sure what to do with write data')
            if readWrite == 'r':
                tmpArray = np.array(returnData)
                for x in range(mbAddress, mbAddress + numRegs):
                    self.mbCR[x] = tmpArray[x - mbAddress]
                    self.ctrlsCoil[x - 1].SetLabel(str(tmpArray[x - mbAddress]))
                    if self.mbCR[x] == True:
                        self.ctrlsBitmaps[x - 1].SetBitmap(wx.Bitmap(self.PilotLightGreenOn))
                    if self.mbCR[x] == False:
                        self.ctrlsBitmaps[x - 1].SetBitmap(wx.Bitmap(self.PilotLightRedOn))

        if mbType == 'mc':  # MULITPLE coil
            if readWrite == 'w':
                print('not sure what to do with write data')
            if readWrite == 'r':
                tmpArray = np.array(returnData)
                for x in range(mbAddress, mbAddress + numRegs):
                    # print('mbCR:', x, "  ", self.mbCR[x])
                    self.mbCR[x] = tmpArray[x - mbAddress]
                    self.ctrlsCoil[x - 1].SetLabel(str(tmpArray[x - mbAddress]))
                    if self.mbCR[x] == True:
                        self.ctrlsBitmaps[x - 1].SetBitmap(wx.Bitmap(self.PilotLightGreenOn))
                    elif self.mbCR[x] == False:
                        self.ctrlsBitmaps[x - 1].SetBitmap(wx.Bitmap(self.PilotLightRedOn))

        if mbType == 'sh':  # single holding
            if readWrite == 'r':
                # print('Ret Data:')
                # print(returnData)
                tmpArray = np.array(returnData)
                for x in range(mbAddress, mbAddress + numRegs):
                    MainForm.mbHR[x] = tmpArray[x - 1]
                    self.ctrlsHreg[x].SetLabel(str(self.mbHR[x]))
                self.lightLbl.SetLabel(str(self.mbHR[1]))
                self.lightGauge.SetValue(self.mbHR[1])
                self.humidityLbl.SetLabel(str(self.mbHR[2]))
                self.temperatureLbl.SetLabel(str(self.mbHR[3]))
                espID = self.ctrlsHreg[107] * 256 + self.ctrlsHreg[108]
            if readWrite == 'w' and mbType == 'sh':
                print('not sure what to do with write data')

        if mbType == 'mh':  # mutiple  holding
            if readWrite == 'r':
                # print('Ret Data:')
                # print(returnData)
                tmpArray = np.array(returnData)
                for x in range(mbAddress, mbAddress + numRegs):
                    MainForm.mbHR[x] = tmpArray[x - mbAddress]
                    self.ctrlsHreg[x].SetLabel(str(self.mbHR[x]))
                self.lightLbl.SetLabel(str(self.mbHR[1]))
                self.lightGauge.SetValue(self.mbHR[1])
                self.humidityLbl.SetLabel(str(self.mbHR[2]))
                self.temperatureLbl.SetLabel(str(self.mbHR[3]))
                self.espID = self.mbHR[107] * 65536 + self.mbHR[108]
                self.lbl_espID.SetLabel(str(self.espID))
            if readWrite == 'w' and mbType == 'sh':
                print('not sure what to do with write data')


        if self.mbHR[3] > 100:
            while True:
                time.sleep(1)
    # **********************************************************************************************************************
    def sendModbus(self, temp):  # mbTypes = sh mh sc mc


        print('Sending modbus data')

        self.c.open()

        if self.c.is_open():

            print('Coomunication established...')
            readWrite = temp[0]
            mbType = temp[1]
            mbAddress = temp[2]
            numRegs = temp[3]
            mbData = temp[4]

            # print('R/W:' + readWrite+ ' Type:' + mbType + ' Addr:' + str(mbAddress) + ' numRegs:' + str(numRegs) + ' mbData:' + str(mbData))
            if mbType == 'sc':  # single coil
                if readWrite == 'w':
                    temp = self.c.write_single_coil(mbAddress, mbData)
                    print(temp)
                if readWrite == 'r':
                    temp = self.c.read_coils(mbAddress, numRegs)
                    # print('Ret Data:')
                    # print(temp)

            if mbType == 'mc':  # MULITPLE coil
                if readWrite == 'w':
                    temp = self.c.write_multiple_coils(mbAddress, mbData)
                if readWrite == 'r':
                    temp = self.c.read_coils(mbAddress, numRegs)
                    # print('Ret Data:')
                    # print(temp)

            if mbType == 'sh':  # single holding
                if readWrite == 'r':
                    temp = self.c.read_holding_registers(mbAddress, numRegs)
                    print('Ret Data:')
                    print(temp)
                if readWrite == 'w' and mbType == 'sh':
                    temp = self.c.write_single_register(mbAddress, 1)

            if mbType == 'mh':  # mutiple  holding
                if readWrite == 'r':
                    temp = self.c.read_holding_registers(mbAddress, numRegs)
                    print('Ret Data:')
                    print(temp)
                if readWrite == 'w' and mbType == 'sh':
                    temp = self.c.write_multiple_registers(mbAddress, mbData)

            if self.c.is_open():
                self.c.close()
            print('Modbus error', self.c.last_error())
            if self.c.last_error() > 0:
                print('*******************************************************************************************')
            return temp

        else:
            while not self.c.is_open():
                print('Trying to reestablish communication...')
                self.c.open()
                status = self.c.last_error()
                time.sleep(1)
                print('Status:', status)




if __name__ == '__main__':
    app = wx.App()
    hform = MainForm(None, title='Thermostat Test Suite')
    hform.frame.Show()
    app.MainLoop()
