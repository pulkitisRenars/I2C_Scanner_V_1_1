#I2C and ControlUnit scanner tool meant for testing TTunits and ControlUnits. The tool tests I2C devices(Real-Time-Clock, EEPROM, Buzzer),
#also the ControlUnit(connected relays, Alarm state), Wiegand RFID card reader(all 4 pin addresses, card data, reader functionality)

import machine
from display.ili934xnew import ILI9341, color565
from machine import Pin, SPI, UART
import tools.m5stack as m5stack
from tools.eeprom import EEPROM
import display.glcdfont as glcdfont
from micropython import const
import display.tt14 as tt14
import display.tt24 as tt24
import random
import display.tt32 as tt32
import os
import utime
import json
import sys
from tools.MSG import MSG
from tools.Wiegand import Wiegand
from ComponentTests import ComponentTests


def AddToHistory(data):
    CT.history_conf["history"].append(data)
    with open('/conf.json', 'w') as file:
        json.dump(CT.history_conf, file)


def newFrame(page):#Function for a new frame on the LCD display
    device=CT.i2c.scan()

    CT.display.erase()
    CT.display.fill_rectangle(0 , 0, 240, 320, 65535)
    CT.display.fill_rectangle(0 , 0, 240, 50, 008000)
    CT.display.fill_rectangle(0 , 50, 240, 5, 000033)

    if check_uart is not None and device != [] and check_uart != b'\x00':#Checks if there is a ControlUnit connected
        CT.display.set_pos(120, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write("ControlUnit")

    elif check_uart==b'\x00' and device != []:#Otherwise it shows that there is a TTunit connected
        CT.display.set_pos(165, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write("TTunit")

    elif device == [] and page != "pc":#If there aren't any devices connected to RPi
        CT.display.set_pos(110, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
        print(CT.current_language)
        CT.display.write(CT.language_dict[CT.current_language][0]["no_device"])

    if page == "pc":
        CT.display.set_pos(130, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write(CT.language_dict[CT.current_language][0]["pc_connected"])

    CT.display.fill_rectangle(10 , 16, 85, 30, 808080)
    CT.display.fill_rectangle(5 , 11, 85, 30, 65535)

    CT.display.set_font(tt24)
    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    CT.display.set_pos(10, 15)
    CT.display.write('IN')

    CT.display.set_color(color565(0, 255, 0), color565(255, 255, 255))
    CT.display.set_pos(30, 15)
    CT.display.write('PASS')

    CT.display.set_font(tt14)
    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

    if page != 0 and page != "res" and page != "pc":#If there are any test numbers set it sets to needed test number
        CT.display.set_pos(10, 300)
        CT.display.write(str(CT.page)+CT.language_dict[CT.current_language][0]["test_numbering"])

    elif page == "res":#If there is given a result signal it will set it as Results on frame
        CT.display.set_pos(10, 300)
        CT.display.write(CT.language_dict[CT.current_language][0]["test_results"])

CT = ComponentTests(newFrame)

check_uart = CT.UartComPreTest()
check_eeprom = CT.EepromPreTest()

def TestSuccess():

    string_to_send = ""
    print(CT.i2c_devices)
    for val in CT.results_list_to_send:
        string_to_send = string_to_send + val 

    string_to_send = string_to_send.rstrip(string_to_send[-1])

    if CT.used_device == "ATmega":

        if CT.i2c_devices[0][2]=="True" and CT.i2c_devices[1][2]=="True":

            if CT.language_dict[CT.current_language][0]["cu_write_ok"] in CT.results_list  and CT.rfid_res==['1.','2.','3.','4.']:

                string_to_send = "cu-true:"+string_to_send

                AddToHistory(string_to_send)

                return True
            
        string_to_send = "cu-false:"+string_to_send

        AddToHistory(string_to_send)

        return False

    elif CT.used_device == "I2C":

        if CT.i2c_devices[0][2]=="True" and CT.i2c_devices[1][2]=="True":
            print("in tt true")
            string_to_send = "tt-true:"+string_to_send

            AddToHistory(string_to_send)

            return True
        
        string_to_send = "tt-false:"+string_to_send

        AddToHistory(string_to_send)

        return False

    
def scan_i2c():#The main scanner function
    devices = CT.i2c.scan()
    x=0
    print(devices)
    if devices:#If there are I2C hardware used
        newFrame(0)
        CT.display.set_pos(10, 60)
        CT.display.print(CT.language_dict[CT.current_language][0]["i2c_devices_found"])

        print("Found I2C devices")

        col = 60

        for device in devices:

            CT.display.set_pos(135, col)
            CT.display.print(f"{hex(device)};")

            col = col+15

        if check_uart is not None and check_uart!=b'\x00':#Checks if there is a ControlUnit connected

            CT.used_device="ATmega"#Names the Unit according to the test

            col = col+10

            CT.display.set_pos(10, col)
            CT.display.print(CT.language_dict[CT.current_language][0]["cu_device_found"])

            print("Found ControlUnit device")

        elif check_uart==b'\x00':
            CT.used_device="I2C"#Names the Unit according to the test

            col = col+10

            CT.display.set_pos(10, col)
            CT.display.print(CT.language_dict[CT.current_language][0]["tt_device_found"])

            print("Found TTunit device")

        utime.sleep(2)

        newFrame(0)
        col = 30

        for device in devices:#Makes the I2C hardware status true for further results identification
            x=0
            for hexs, name, status in CT.i2c_devices:

                if hexs == str(device):
                    col+=30

                    CT.display.set_pos(10, col)
                    CT.display.print('* '+name+CT.language_dict[CT.current_language][0]["connected_comp"])

                    CT.i2c_devices[x][2]='True'

                x+=1

        if check_uart is not None and check_uart!=b'\x00':#Checks if there is a ControlUnit connected

            col+=30
            CT.display.set_pos(10, col)
            CT.display.print(CT.language_dict[CT.current_language][0]["cu_device_found"])

        print(str(x)+" I2C devices were found")

        utime.sleep(1)

        for device in CT.i2c_devices:
            if 'True' in device:#Checks if the device has a "True" value
                i2c_found = True

                break
        if i2c_found:#If there is at least one "True"  
                          
                        CT.page = 1
                        CT.RTC_check()#Runs the RTC_check function, y is used for the storing of the display location

                        CT.page=2
                        CT.EEPROM_check()#Runs the EEPROM_check function, y is used for the storing of the display location

                        if check_uart is not None and check_uart!=b'\x00':#Checks if there is a ControlUnit connected

                            CT.page=3
                            CT.ATmega_check()#Runs the ATmega_check function, y is used for the storing of the display location
                            
                            CT.display.set_pos(130, 10)
                            CT.display.set_font(tt14)
                            CT.display.write(CT.language_dict[CT.current_language][0]["press_button_r"])

                            while True:
                                button_pressed = CT.main_button.value() == 0  # Check if the button is pressed
                                if button_pressed:

                                    CT.page = 4
                                    CT.ATmega_relay_check()

                                    CT.page = 9
                                    CT.RFID_check()

                                    break


                        utime.sleep(0.3)
                        print(check_uart, device)
                        if check_uart is not None and check_uart !=b'\x00':

                            CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            CT.display.set_pos(170, 10)
                            CT.display.set_font(tt14)
                            CT.display.write(CT.language_dict[CT.current_language][0]["press_button_o"])

                            CT.display.set_pos(10, 265)
                            CT.display.print(CT.language_dict[CT.current_language][0]["alarm_to_confirm"])
                        
                        elif check_uart==b'\x00' and device != []:

                            CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            CT.display.set_pos(170, 10)
                            CT.display.set_font(tt14)
                            CT.display.write(CT.language_dict[CT.current_language][0]["press_button_b"])

                            CT.display.set_pos(10, 265)
                            CT.display.print(CT.language_dict[CT.current_language][0]["buzz_to_confirm"])

        else:#If there isn't any "True" found
          
          col = 60
          newFrame(0)

          for hexs, names, status in CT.i2c_devices:
            if status=="False":#Checks the I2C hardware for "False" values

                CT.display.set_pos(0, col)
                CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
                CT.display.print('* '+names+CT.language_dict[CT.current_language][0]["not_found"])

                print("The scanner didn't find "+names+" device")

                col+=30
           
    else:#If there aren't any I2C hardware found
        newFrame(0)

        print(devices)

        CT.display.set_pos(10, 60)
        CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
        CT.display.print(CT.language_dict[CT.current_language][0]["i2c_devices_not_found"])

        print("There weren't any I2C devices found")

        if check_eeprom == False:
            CT.display.set_pos(10, 90)
            CT.display.print(CT.language_dict[CT.current_language][0]["problem_eeprom"])

        CT.used_device = None

        CT.SendRecieveData()

def TestResults():
    if CT.used_device != None:
        print("inside results")
        while True:
            if CT.main_button.value() == 0:

                newFrame(0)

                if check_uart is not None and check_uart!=b'\x00':#If a ControlUnit is connected

                    CT.display.set_pos(10, 60)
                    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                    CT.display.print(CT.language_dict[CT.current_language][0]["alarming"])

                    print("Buzzing!")

                    CT.M.Queue("SET","alarm_on_state",value=1)
                    CT.M.Send(True)

                    utime.sleep(3)

                    CT.M.Queue("SET","alarm_on_state",value=0)
                    CT.M.Send(True)
                    
                    break

                elif check_uart==b'\x00':#If a TTunit is connected

                    CT.display.set_pos(10, 60)
                    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                    CT.display.print(CT.language_dict[CT.current_language][0]["buzzing"])

                    CT.display.set_pos(170, 10)
                    CT.display.set_font(tt14)

                    print("Buzzing!")

                    for x in range(5):
                        CT.TT_buzzer.on()
                        utime.sleep(0.1)

                        CT.TT_buzzer.off()
                        utime.sleep(0.1)
                        
                    break

        while True:     

                newFrame("res")

                CT.display.set_pos(160, 10)
                CT.display.set_font(tt14)
                CT.display.write(CT.language_dict[CT.current_language][0]["restart_button"])

                if TestSuccess():
                    #Checks the status of all of the hardware, if every hardware is found and tested successfully
                    col = 60

                    for i, stat in enumerate(CT.results_list):
                        i+=1

                        CT.display.set_pos(5, col)
                        CT.display.set_font(tt14)

                        if "ERR" in stat or "ERROR" in stat:
                            CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))

                            print("err")

                        CT.display.write(stat)

                        if (i < 7 and CT.used_device=="ATmega") or CT.used_device=="I2C":

                            CT.display.fill_rectangle(20 , col+15, 200, 2, 000033)

                        col+=25

                        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

                    CT.display.fill_rectangle(0 , 240, 240, 5, 008000)

                    CT.display.set_pos(30, 250)
                    CT.display.set_font(tt24)
                    CT.display.set_color(color565(0, 255, 0), color565(255, 255, 255))
                    CT.display.write(CT.language_dict[CT.current_language][0]["test_successful"])

                    print("The I2C scanner test was successful!")
                    
                    break
                else:#If the hardware status isn't successful

                    col=60

                    for i, stat in enumerate(CT.results_list):
                        i=i+1

                        CT.display.set_pos(5, col)
                        CT.display.set_font(tt14)

                        if CT.rfid_res != ['1.','2.','3.','4.'] and "readers" in stat:

                            CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))

                        elif ("ERR" in stat or "ERROR" in stat):

                            CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))

                        CT.display.write(stat)

                        if (i < 7 and CT.used_device=="ATmega") or CT.used_device=="I2C":

                            CT.display.fill_rectangle(20 , col+15, 200, 2, 000033)

                        col+=25

                        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

                    CT.display.fill_rectangle(0 , 240, 240, 5, 000030)

                    CT.display.set_pos(30, 250)
                    CT.display.set_font(tt24)
                    CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
                    CT.display.write(CT.language_dict[CT.current_language][0]["test_unsuccessful"])
                    print("The I2C scanner test was unsuccessful!")
                    
                    break

    else:
        print("not inside results")
    
newFrame(0)#The first starting frame

print("Starting program")

CT.display.set_pos(10, 60)
CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
CT.display.print(CT.language_dict[CT.current_language][0]["main_start"])

CT.display.set_pos(170, 10)
CT.display.set_font(tt14)
CT.display.write(CT.language_dict[CT.current_language][0]["press_button"])

while True:#If button is pressed restarts the main scanner function
    if CT.main_button.value() == 0:
        print("Test starting")

        CT.ResetForTest()

        scan_i2c()

        TestResults()
