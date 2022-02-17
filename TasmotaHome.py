from ipaddress import ip_network
from time import time
import requests
import json
import Tasmota
from Tasmota import Device
from requests_html import HTMLSession
from datetime import datetime
import socket
import math
import colorsys

from flask import Flask, render_template, redirect, request
app = Flask(__name__)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

devices = json.load(open("devicedatabase.ini"))
log = json.load(open("log.ini"))

#Configuration loading
config = json.load(open("config.ini"))
_instance_name = config.get("InstanceName")
_port = int(config.get("Port"))

#Navivates user to the device list page when the navigate to http://url/ by render the page with the create_device_page method
@app.route('/')
def navigate_devices_page():
   return create_devices_page()

#This method creates the page displaying all the devices, i.e. the 'home page'
def create_devices_page():
    start_time = datetime.now()

    page_content = ""
    ip_list = list(devices.keys())
    power_states = Tasmota.get_all_power_states(ip_list)
    for device in devices:
        icon_type = ""
        device_type_string = devices.get(device).split(";")[1]
        if device_type_string == "light":
            if power_states.get(device) == "ON":
                icon_type = "lightbulb"
            else:
                icon_type = "lightbulb-off"
        else:
            if power_states.get(device) == "ON":
                icon_type = "power-plug"
            else:
                icon_type = "power-plug-off"
        
        power_button_type = ""
        if power_states.get(device) == "ON":
            power_button_type = 'success'
        else:
            power_button_type = 'danger'

        # I feel like there's a way to duplicate the div in php maybe rather than having a bunch of html in the code but idk
        page_content += """<div class='card bg-light mb-3' style='width: 10rem;'>
                                <div class='card-body'>
                                    <h5 class='card-title' style='margin-bottom: -5px;'><i id='device_icon-"""+device+"""' class="mdi mdi-"""+icon_type+""""></i><br>""" + devices.get(device).split(";")[0] +"""</h5>
                                </div>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item">
                                        <button class='cb btn btn-"""+power_button_type+"""'
                                            onclick="toggle_power('"""+device+"""')"
                                            id="btn_toggle_power-"""+device+""""
                                            style='margin:0px; margin-top:-2px; margin-bottom: 10px;' aria-label="Lightbulb"><i id="btn_toggle_power_icon-"""+device+"""" class="mdi mdi-power"
                                            aria-hidden="true"></i> <span id="btn_toggle_power_text-"""+device+"""">""" + power_states.get(device).title() +"""</span></button>
                                    </li>
                                    <li class="list-group-item"><a name='device_button'
                                        href='/devices/""" + device + """'
                                        text='button'
                                        class='btn btn-primary cb'>Control</a>
                                    </li>
                                </ul>
                            </div>"""
    end_time = datetime.now()
    time_to_generate = truncate((end_time-start_time).total_seconds(), 2)
    return render_template("devices_page.html", Devices=page_content, InstanceName=_instance_name, GenTime=time_to_generate)

@app.route('/devices/<ip>/')
def navigate_control_pages(ip):
    if ip == "add":
        return create_add_page()
    else:
        device = ip
        return create_control_page(device)

#This method creates the 'add device page'
def create_add_page():
    return render_template("add_device_page.html", InstanceName=_instance_name)

#This method creates the individual control page for each device
def create_control_page(ip):
    start_time = datetime.now()
    tasmota = Device(ip)
    status = tasmota.GetStatus()
    mac = status.get("Mac")
    power_status = ""
    version = status.get("Version").split("(")[0]
    signal_strength = int(status.get("Signal"))
    signal_level = ""

    power_button_type = ""

    if signal_strength >= -50:
        signal_level = "4"
    elif signal_strength >= -60:
        signal_level = "3"
    elif signal_strength >= -70:
        signal_level = "2"
    else:
        signal_level = "1"

    device_icon = ""
    if "Color" in status:
        device_icon = "lightbulb"
    else:
        device_icon = "power-plug"

    if status.get("Power") == "0":
        power_status = "Off"
        power_button_type = "danger"
        if "Color" in status:
            device_icon = "lightbulb-off"
        else:
            device_icon = "power-plug-off"
    else:
        power_status = "On"
        power_button_type = "success"
        if "Color" in status:
            device_icon = "lightbulb"
        else:
            device_icon = "power-plug"

    status_print = ""
    for key in status:
        if key == "Power":
            status_print += "<p><span>" + key + "</span>: <span id='status_power_num'>" + status.get(key) + "</span></p>"
        elif key == "POWER":
            status_print += "<p><span>" + key + "</span>: <span id='status_power_text'>" + status.get(key) + "</span></p>"
        else:
            status_print += "<p><span>" + key + "</span>: <span>" + status.get(key) + "</span></p>"
    end_time = datetime.now()
    time_to_generate = truncate((end_time-start_time).total_seconds(), 2)
    return render_template("control_page.html", IP=ip, WifiStrength = str(signal_strength), WifiStrengthLevel = signal_level, Title=status.get("FriendlyName"), GenTime=time_to_generate, InstanceName=_instance_name, PowerStatus = power_status, PowerButtonType=power_button_type, Status=status_print, DeviceIcon = device_icon, MAC = mac, Version=version)

#Renders the log page from template at url/logs/
@app.route('/logs/<ip>/')
def navigate_log_page(ip):
    start_time = datetime.now()
    if ip == "all":
        output = ""
        i = 0
        for item in reversed(log):
            i+=1
            output += """<tr>
                            <td style="width: 33%;">"""+item.split(".")[0]+"""</td>
                            <td style="width: 33%;"><a href='/logs/"""+log.get(item).split(';')[0]+"""/'>"""+log.get(item).split(';')[0]+"""</a></td>
                            <td style="width: 33%;">"""+log.get(item).split(';')[1]+"""</td>
                        </tr>"""
        #this page is fairly short so there is no real reason to seperate the rendering into a seperate method
        end_time=datetime.now()
        time_to_generate = truncate((end_time-start_time).total_seconds(), 2)
        return render_template("log_page.html", Logs=output, InstanceName=_instance_name, GenTime=time_to_generate)
    else:
        output = ""
        i = 0
        for item in reversed(log):
            if log.get(item).split(';')[0] == ip:
                i+=1
                output += """<tr>
                                <td style="width: 33%;">"""+item.split(".")[0]+"""</td>
                                <td style="width: 33%;">"""+log.get(item).split(';')[0]+"""</td>
                                <td style="width: 33%;">"""+log.get(item).split(';')[1]+"""</td>
                            </tr>"""
        #this page is fairly short so there is no real reason to seperate the rendering into a seperate method
        end_time=datetime.now()
        time_to_generate = truncate((end_time-start_time).total_seconds(), 2)
        return render_template("log_page.html", Logs=output, InstanceName=_instance_name, GenTime=time_to_generate)

def log_item(ip, value):
        now = str(datetime.now())
        #this is ugly, splits the datetime.now into just the time, also retrieves the visitors ip, gets the friendly name of the device from the device dictionary.... 
        print("[" + now.split(" ")[1].split(".")[0] + "] " + str(request.environ['REMOTE_ADDR']) + "//" + devices.get(ip).split(";")[0] + ": " + value)
        log[now] = ip+";"+value
        json.dump(log, open("log.ini",'w'))

#idk how tf this works i stole it from the internet (whats an integral)
def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

#this method sends the command (value) to the device (ip). Redirects afterwards back to the devices page. 
#because of Javascript, commands are usually sent using the JS fetch() method, which allows the user to send
#a command or press a button without the page directing the user to the /command/ip/value URL without the page reloading.
@app.route('/command/<ip>/<value>')
def send_command(ip, value):
    log_item(ip, value)
    response = requests.get("http://"+ip+"/cm?cmnd="+value)
    return redirect("/devices/" + ip)

#this method is called from the 'add device' page. This just grabs information about the device and dumps it into a database.
#todo: add devices without refreshing page via javascript?
@app.route('/add', methods=['POST', 'GET'])
def add_device():
    ip = request.form['ip']
    device = Device(ip)
    status = device.GetStatus()
    friendly_name = status.get("FriendlyName")
    type = ""
    if "Color" in status:
        type = "light"
    else:
        type = "switch"
    devices[ip] = friendly_name + ";" + type
    json.dump(devices, open("devicedatabase.ini",'w'))
    return redirect("/")

#Actually starts the webserver
app.run(host='0.0.0.0', port=_port)