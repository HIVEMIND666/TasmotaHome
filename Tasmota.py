from requests_html import HTMLSession
import concurrent.futures
import re
class Device():
    ip = ""
    def __init__(self, ip):
        self.ip = ip

    def GetStatus(self):
        status = HTMLSession(verify=False).get("http://"+str(self.ip)+"/cm?cmnd=Status%200").text
        status = status.replace(",\"Wifi\":", "").replace("\"Status\":", "").replace("\"StatusPRM\":", "").replace("\"StatusFWR\":", "").replace("\"StatusLOG\":", "").replace("\"StatusMEM\":", "").replace("\"StatusNET\":", "").replace("\"StatusMQT\":", "").replace("\"StatusTIM\":", "").replace("\"StatusSNS\":", "").replace("\"StatusSTS\":", "").replace("\"FriendlyName\":[\"", "\"FriendlyName\":\"").replace("{", "").replace("}", "")
        status = re.sub('\[[^\]]+\]', '[]', status)
        status = status.replace("[","").replace("]","")
        status_split = status.split(",\"")
        status_array = {}
        for x in range(len(status_split)):
            split_data = status_split[x].split("\":")
            variable = split_data[0].replace("\"","")
            value = split_data[1].replace("\"","")
            if value != "[]":
                status_array[variable] = value
        return status_array

#This doesn't really need to be called in a device object, any use of the device object typically pulls the state anyway so no need for more requests.
def read_power_state(ip):
    status = HTMLSession(verify=False).get("http://"+str(ip)+"/cm?cmnd=Power").text.replace("}", "").replace("{", "").replace("\"", "").split(":")[1]
    return ip+"//"+status

def get_all_power_states(device_ips):
    power_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Start the load operations and mark each future with its URL
        future_get_power_state = {executor.submit(read_power_state, ip): ip for ip in device_ips}
        for future_result in concurrent.futures.as_completed(future_get_power_state):
            url = future_get_power_state[future_result]
            try:
                data = future_result.result() 
                ip = data.split("//")[0]
                result = data.split("//")[1]
                power_results[ip]=result
            except Exception as exc:
                pass
            else:
                pass
    return power_results

def is_tasmota(ip):
    return False

def scan_network():
    return False