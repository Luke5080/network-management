"""
IsAlive Conceptual Script
Not intended to be used in production environments
A purely expiremental project
Author: Luke Marshall
GitHub: https://github.com/Luke5080
Python file needs to run in the repo directory
"""

import os
import getpass
import time
import socket
import ast
import threading
import platform
import colorama
from pyfiglet import figlet_format
from cryptography.fernet import Fernet
from netmiko import ConnectHandler
from colorama import Fore, Style


colorama.init(autoreset=True)

working_dir = os.getcwd()

user_system = platform.system()

## Check first if .invlist exists - by default it should be in the directory
## if it has been deleted for some reason create it in the current directory
if os.path.isfile(".invlist.txt"):
    if os.path.getsize(".invlist.txt") > 0:

        with open("mykey.key", "rb") as keyfile:
            inv_key = keyfile.read()

        f = Fernet(inv_key)

        with open(".invlist.txt","rb") as file:
            updated_encrypted = file.read()
        
        updated = f.decrypt(updated_encrypted)
        updated = updated.decode("utf-8")

        inv_list = ast.literal_eval(updated)

    else:
        inv_list = {}
else:
    with open(".invlist.txt","w") as f:
        pass

    inv_list = {}

load_slide = f"{Style.BRIGHT}="*20

class DeviceTasks():
    '''
    class to create an object for a device based on the device creds + IP
    can then perform all SSH operations on the created object
    '''
    def __init__(self, username, password, ip):
        self.username = username
        self.password = password
        self.ip = ip

        self.device_attr = ConnectHandler(
        device_type="cisco_ios",
        host= ip,
        username= username,
        password= password,
        )

    def health_check(self):
        """gathers info for health check such as CPU usage/memory usage
        /uptime of switch/environmental info"""

        uptime = self.device_attr.send_command("sh version | inc uptime | Last")

        cpu_usage = self.device_attr.send_command("sh process cpu sorted")

        cpu_usage = cpu_usage.split("\n")

        cpu_usage_sort = list(cpu_usage[1:5])

        cpu_history = self.device_attr.send_command("sh process cpu history")

        memory_info = self.device_attr.send_command("sh process memory sorted")

        memory_info = memory_info.split("\n")

        mem_in_nums = memory_info[0]

        mem_in_nums = mem_in_nums.split(" ")

        for word in mem_in_nums:
            if word == "":
                mem_in_nums.remove(word)

        mem_in_nums.remove("Processor")
        mem_in_nums.remove("Pool")

        total_mem = int(mem_in_nums[1])
        used_mem = int(mem_in_nums[3])

        total_mem_use = (used_mem / total_mem) * 100

        return uptime, cpu_usage_sort, cpu_history, total_mem_use, total_mem, used_mem

    def check_all_int(self) -> str:
        """function to check all interfaces of a device"""
        output = self.device_attr.send_command("sh ip int br")
        return output
    
    def check_int(self,int_name:str) -> str:
        """function to check a specific interface on a device"""
        command = f"sh int {int_name}"
        output = self.device_attr.send_command(command)
        return output
    
    def cdp_neigh(self) -> str:
        """function to check cdp neighbour from a device"""
        output = self.device_attr.send_command("sh cdp neigh")
        return output
    
    def ospf_check(self) -> str:
        """function to check ospf configurations on a device"""
        output = self.device_attr.send_command("sh ip ospf")
        return output
    
    def bgp_check(self) -> str:
        """function to check bgp configuration on a device"""
        output = self.device_attr.send_command("sh ip bgp")
        return output
    
    def test_connec(self, end_ip: str) -> str: #ToDo: Not implemented
        command = f"ping {end_ip}"
        output = self.device_attr.send_command(command)
        return output


    def get_facts(self) -> list:
        """function to grab device make/model details"""

        output = self.device_attr.send_command("sh version | inc Model Number")

        count_model = output.count("Model Number")

        if count_model > 1:
            model_info = []
            refactor_output = output.split("\n")
            for item in refactor_output:
                item = item.strip("Model Number").strip(":").strip(" ")
                model_info.append(item)

            model_info = list(set(model_info)) 

        else:
            model_info = []

            refactor_output = output.strip("Model Number").strip(":").strip(" ")

            model_info.append(model_info)

        return model_info

def welcome():
    """welcome function"""
    text = "Is Alive?"
    banner = figlet_format(text, font="big")
    print(Fore.BLUE + banner)
    print(f"{Fore.RED}U{Fore.YELLOW}S{Fore.GREEN}A{Fore.BLUE}G{Fore.MAGENTA}E: {Fore.BLUE}{Style.BRIGHT}README.md")
    print(f"{Fore.CYAN}{Style.BRIGHT}Author: Luke Marshall")
    print(f"{load_slide}\n")

def create_inv(inv_list):
    """Function to create inventory"""
    print(f"{Style.BRIGHT}Let's set up a new inventory\nWhat will we name this inventory?")
    inv_name = input(">>> ")

    # Ensure user doesn't create an inventory with name already in use
    inv_check = [key for key in inv_list]

    while inv_name in inv_check:
        print("Inventory already created with this name\nWhat will we name this inventory?")
        inv_name = input(">>>")

    print(f"Configuring inventory {Fore.BLUE}{Style.BRIGHT}{inv_name}")
    print(load_slide)
    print(f"{Style.BRIGHT}How many devices would you like to add to this inventory?")
    dev_amount = int(input(">>> "))

    devices = {}

    devices["vars"] = {}

    print(f"{Style.BRIGHT}What USERNAME will you be logging into to these devices with?")
    d_user = str(input(">>> "))
    devices["vars"]["user"] = d_user

    print(f"{Style.BRIGHT}What is the PASSWORD for this account? ")
    d_passw = getpass.getpass(">>>")
    devices["vars"]["pass"] = d_passw


    for i in range(dev_amount):
        print(load_slide)
        print(f"{Fore.BLUE}NEW DEVICE\nWhat is the name of the device you would like to configure?")

        device_name = input(">>> ")

        ## Ensure user doesn't enter a device name that was already configured
        dev_check = [key for key in devices if key != "vars"]

        while device_name in dev_check:
            print(f"{Fore.RED}Device already configured with this name")
            device_name = str(input(">>> "))


        print("What is the management IP of this device?")
        mgmt_ip = input(">>> ")

        ip_repeat = [value for key, value in devices.items() if key != "vars"]

        ## Check first if IP is valid

        try:
            socket.inet_aton(mgmt_ip)
        except socket.error:
            print(f"{Fore.RED}IP ADDRESS NOT VALID")
            mgmt_ip = input(">>> ")

        ## Ensure IP address is not the same as one configured for another device

        while mgmt_ip in ip_repeat:
            print(f"{Fore.RED}Device already configured with this IP")
            mgmt_ip = input(">>> ")


        devices[device_name] = mgmt_ip


        print(f"{Fore.GREEN}Check if this IP Address is reachable? (y/n)")

        while True:
            try:
                check_up = input(">>> ")
                if check_up.lower() == "y" or check_up.lower() == "n":
                    break
            except ValueError:
                print(f"{Fore.RED}Please enter a valid response")


        if check_up.lower() == "y":
            print(load_slide) 
            print(f"{Fore.GREEN}{Style.BRIGHT}\nPinging IP address ... sending 4 pings")

            if user_system != "Windows":
                status_ping = os.popen(f"ping -c 4 {mgmt_ip}").read()
            else:
                status_ping = os.popen(f"ping {mgmt_ip}").read()

            # If ping receives 4 replies, do nothing, else prompt the user to either 
            # continue anyway or remove current device
            if user_system != "Windows" and "4 received" in status_ping:
                print(f"{Fore.GREEN}{Style.BRIGHT}OK: IP Address reachable via ping")
                print(load_slide)
                print(f"{Style.BRIGHT}{Fore.BLUE}\nDevice Name: {device_name}\nMgmt IP Address: {mgmt_ip}\n")
            
            elif user_system == "Windows" and "Received = 4" in status_ping:
                print(f"{Fore.GREEN}{Style.BRIGHT}OK: IP Address reachable via ping")
                print(load_slide)
                print(f"{Style.BRIGHT}{Fore.BLUE}\nDevice Name: {device_name}\nMgmt IP Address: {mgmt_ip}\n")
            

            else:
                print(f"{Fore.RED}IP Address not reachable\nWould you like to:\n1: Continue Anyway 2: Remove this device")
                while True:
                    try:
                        choice = input(">>>")
                        if choice in ("1","2"):
                            break
                    except ValueError:
                        print(f"{Fore.RED}Please enter a valid response")

                if choice == "2":
                    del devices[device_name]  


    return devices, inv_name

def menu():
    print(Style.BRIGHT + "OPTIONS:\n1. Load Inventory. 2. Create New Inventory (Choose 1 or 2/ q to quit)")
    while True:
        try:
            menu_choice = input(">>> ")
            if menu_choice == "1" or menu_choice == "2" or menu_choice.lower() == "q":
                break
            else:
                print(f"{Fore.RED}Please enter option 1 or 2")
        except ValueError:
            print(f"{Fore.RED}Please enter option 1 or 2")

        
    
    return menu_choice

def upstatus(inv_name):
    working_inv = {}
    working_inv.update(inv_list[inv_name])
    print(f"{Fore.YELLOW}{Style.BRIGHT}Loading inventory.. This may take some time depending on num of devices..")
    
    dev_up_stat={}

    t = LoadAnim()
    t.start()

    not_good = ["0","1","2","3"]

    for dev, ip in working_inv.items():
        if dev != "vars":
            dev_up_stat[dev] = []

            if user_system != "Windows":
                status_ping = os.popen(f"ping -c 4 {ip}").read()
            else:
                status_ping = os.popen(f"ping {ip}").read()

            if user_system != "Windows" and "4 received" in status_ping:
                dev_up_stat[dev].append("UP - 0% packet loss")
                dev_up_stat[dev].append("1")
            
            elif user_system == "Windows" and "Received = 4" in status_ping:
                dev_up_stat[dev].append("UP - 0% packet loss")
                dev_up_stat[dev].append("1")

            else:
                for num in not_good:
                    if user_system != "Windows":
                        chk_str = f"{num} received"

                    elif user_system == "Windows":
                        chk_str = f"Received = {num}"

                    if num == "3":
                        if chk_str in status_ping:
                            dev_up_stat[dev].append("DOWN - 25% packet loss")
                            dev_up_stat[dev].append("0")

                    elif num == "2":
                        if chk_str in status_ping:
                            dev_up_stat[dev].append("DOWN - 50% packet loss")
                            dev_up_stat[dev].append("0")

                    elif num == "1":
                        if chk_str in status_ping:
                            dev_up_stat[dev].append("DOWN - 75% packet loss")
                            dev_up_stat[dev].append("0")

                    elif num == "0":
                        if chk_str in status_ping:
                            dev_up_stat[dev].append("DOWN - 100% packet loss")
                            dev_up_stat[dev].append("0")

                if user_system == "Windows":
                    os.popen(f"tracert {ip} > .tracert-{dev}.txt")

                elif user_system != "Windows":
                    os.popen(f"traceroute {ip} > .tracert-{dev}.txt")

    t.stop()
    t.join()

    return dev_up_stat

def do_tasks_menu():

    options = [
        "Run Health Check on a Device",
        "Check all interface statuses",
        "Check a specific interface status",
        "Check CDP neighbours on a device",
        "Check OSPF configuration on a device",
        "Check BGP configuration on a device",
        #"Ping a device from a certain device"
    ]

    print(load_slide)
    print(f"{Style.BRIGHT}What else would you like to do?\n")

    for num, option in enumerate(options):
        print(f"{num+1} : {option}")
    while True:
        choice = input(">>> (Choose from option 1-6 or q to quit) ")
        if choice in ['1','2','3','4','5','6']:
            break
        elif choice == "q":
            break
        else:
            print(f"{Fore.RED}Please enter a valid option")
    
    return choice
    
def do_tasks(inv_name, choice, upstat_results):
    working_inv = {}
    working_inv.update(inv_list[inv_name])
        
    print("On which device would you like to perform this task?\n")

    devices = [key for key in working_inv if key != "vars"]

    dev_down = []

    for key, value in upstat_results.items():
        if value[1] == "0":
            dev_down.append(key)

    for num, device in enumerate(devices):
        print(f"{Fore.BLUE}{Style.BRIGHT}{num+1}:{device}")
                
    while True:
        device_choice = input("\n>>> (Enter device name): ")

        if device_choice in devices and device_choice not in dev_down:
            break

        elif device_choice not in devices:
            print(f"{Fore.RED}Please enter a valid choice. ")

        elif device_choice in dev_down:
            print(f"{Fore.RED}{device_choice} is DOWN. Cannot perform SSH operations")

               
    user = working_inv["vars"]["user"]
    password = working_inv["vars"]["pass"]
    ip = working_inv[device_choice]

    assign_task = DeviceTasks(user,password,ip)

    if choice == "1":
        model_info = assign_task.get_facts()

        print(f"{Style.BRIGHT}{Fore.GREEN}Device Model:")
        for model in model_info:
            print(f"{Style.BRIGHT}{Fore.GREEN}{model}\n")
                

        uptime, cpu_usage_sort, cpu_history, total_mem_use, total_mem, used_mem = assign_task.health_check()
        print(f"{Style.BRIGHT}{Fore.GREEN}{uptime}\n")

        print(f"{Style.BRIGHT}{Fore.GREEN}Processes with most CPU usage:")
        for cpu in cpu_usage_sort:
            print(f"{Style.BRIGHT}{Fore.GREEN}{cpu}")

        print(f"{Style.BRIGHT}{Fore.GREEN}CPU Utilisation Graph:")
        print(f"{Style.BRIGHT}{Fore.GREEN}{cpu_history}")

        if total_mem_use > 80.00:
            print(f"{Style.BRIGHT}{Fore.RED}Total Memory Used:")
            print(f"{Style.BRIGHT}{Fore.RED}{total_mem_use:.2f}%")
            print(f"{Style.BRIGHT}{Fore.RED}BAD: {used_mem}K out of {total_mem}K")
            print("WARNING: Memory Usage above 80%")
        else:
            print(f"{Style.BRIGHT}{Fore.GREEN}Total Memory Used:")
            print(f"{Style.BRIGHT}{Fore.GREEN}{total_mem_use:.2f}%")
            print(f"{Style.BRIGHT}{Fore.GREEN}GOOD: {used_mem}K out of {total_mem}K")

    elif choice == "2":
        choice_output = assign_task.check_all_int()
        print(load_slide)
        print(f"{Style.BRIGHT}Interface statuses on {device_choice}:")
        print(f"{Style.BRIGHT}{Fore.GREEN}{choice_output}")
        assign_task.health_check()
        
    elif choice == "3":
        print(f"{Style.BRIGHT} What interface would you like to check on the device? ")
        int_choice = input(">>>")
        choice_output = assign_task.check_int(int_choice)
        print(f"\n{Style.BRIGHT}Interface status for {int_choice}")
        print(f"{Style.BRIGHT}{Fore.GREEN}{choice_output}")

    elif choice == "4":
        choice_output = assign_task.cdp_neigh()
        print(load_slide)
        print(f"{Style.BRIGHT}CDP Neighbour command output on {device_choice}:")
        print(f"{Style.BRIGHT}{Fore.GREEN}{choice_output}")

    elif choice == "5":
        choice_output = assign_task.ospf_check()
        print(load_slide)
        print(f"{Style.BRIGHT}OSPF configurations on {device_choice}:")
        print(f"{Style.BRIGHT}{Fore.GREEN}{choice_output}")

    elif choice == "6":
        choice_output = assign_task.bgp_check()
        print(load_slide)
        print(f"{Style.BRIGHT}BGP Routing Table on {device_choice}:")
        print(f"{Style.BRIGHT}{Fore.GREEN}{choice_output}")

    ''' ToDo: Implement test connectivity feature by prompting users for an IP and pinging it from their chosen device.
    elif choice == "6":
        print(f"{Style.BRIGHT} What IP would you like to ping from {device_choice}")
        ping_choice = input(">>> ")
        choice_output = assign_task.test_connec(ping_choice)
        print(f"{Style.BRIGHT}Result of ping from {device_choice} to {ping_choice}:")
        print(f"{Style.BRIGHT}{Fore.GREEN}{choice_output}")'''

class LoadAnim(threading.Thread):
    """loading animation class"""
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        """frames used in loading anim"""
        frames = [
        "  o  ",
        " o   ",
        "o    ",
        " o   ",
        " "
        ]
        while not self._stop_event.is_set():
            for frame in frames:
                print(Fore.YELLOW + f"\r{frame}", end="", flush=True)
                time.sleep(0.2)

    def stop(self):
        """event to stop load animation thread"""
        self._stop_event.set()

def cleanup():
    working_dir_contents = os.listdir(working_dir)
    for f in working_dir_contents:
        if f.startswith(".tracert"):
            os.remove(f)
        else:
            pass

    exit(f"{Style.DIM}Goodbye")

def main(inv_list:dict):
    welcome()
    while True:

        usr_menu_choice = menu()
        
        if usr_menu_choice == "1":

            ## If the inv_list is empty, alert user there are no inventories and prompt to create a new one
            if len(inv_list) == 0:
                print(f"{Fore.YELLOW}{Style.BRIGHT}No inventories to load\nCreate a new inventory? (y/n)")
                choice = input(">>>")
                
                if choice.lower() == "y":
                    usr_inv, inv_name = create_inv(inv_list)
                    inv_list[inv_name] = usr_inv

                    inv_list = str(inv_list)

                    key = Fernet.generate_key()

                    with open("mykey.key", "wb") as file:
                        file.write(key)
                    
                    with open("mykey.key", "rb") as file:
                        encryption_key = file.read()

                    f = Fernet(encryption_key)

                    with open(".invlist.txt","w") as file:
                        file.write(inv_list)

                    with open(".invlist.txt","rb") as file:
                        unencrypted_inv_list = file.read()

                    encrypted_inv_list = f.encrypt(unencrypted_inv_list)

                    with open(".invlist.txt", "wb") as file:
                        file.write(encrypted_inv_list)
                    
            else:
                print(f"{load_slide}\n")

                with open("mykey.key", "rb") as keyfile:
                    key = keyfile.read()

                f = Fernet(key)

                with open(".invlist.txt", "rb") as file:
                    usr_inv_encrypted = file.read()

                inv_list = f.decrypt(usr_inv_encrypted)
                inv_list = inv_list.decode("utf-8")
                inv_list = ast.literal_eval(inv_list)

                print(Style.BRIGHT + "What inventory would you like to load?\n")
                for num, key in enumerate(inv_list):
                    print(f"{Fore.BLUE}{Style.BRIGHT}{num+1}: {key}")
                    
                print("Type name of inventory you would like to load:")

                while True:
                    load_inv = input(">>> ")

                    if load_inv in inv_list:
                        break
                    else:
                        print(Fore.RED + "Inventory not found. Type the name of inventory you would like to load")

                ping_results = upstatus(load_inv)
                
                print(f"\n\n{Style.BRIGHT}Status of devices for inventory {load_inv}:")
                for key,value in ping_results.items():

                    check_this = value[0]
                    if "DOWN" in check_this:
                        print(Fore.RED + f"\nDevice: {key}\nStatus: {value[0]}\n")
                        print(load_slide)

                    elif "UP" in check_this:
                        print(Fore.GREEN + f"\n\nDevice: {key}\nStatus: {value[0]}\n")
                        print(load_slide)

                print(f"To see traceroute output of a device which is down, {Fore.BLUE}{Style.BRIGHT}type the name of the device OR press q to do other tasks")
                while True:
                    sh_result = input(">>> ")

                    if os.path.isfile(f".tracert-{sh_result}.txt"):
                        with open(f".tracert-{sh_result}.txt","r") as f:
                            data = ""
                            for line in f:
                                data += f"{Fore.GREEN}{Style.BRIGHT}{line}"
                        print(data)

                        break
                    
                    elif sh_result == "q":
                    
                        working_dir_contents = os.listdir(working_dir)
                        for f in working_dir_contents:
                            if f.startswith(".tracert"):
                                os.remove(f)
                        break

                    else:
                        print(f"No traceroute output for device {sh_result} (press q to do other tasks)")


                while True:
                    task_choice = do_tasks_menu()
                    if task_choice == "q":
                        break
                    else:
                        do_tasks(load_inv,task_choice, ping_results)

        elif usr_menu_choice == "2":
            usr_inv, inv_name = create_inv(inv_list)

            inv_list[inv_name] = usr_inv
            inv_list = str(inv_list)

            with open("mykey.key", "rb") as keyfile:
                key = keyfile.read()

            f = Fernet(key)

            with open(".invlist.txt", "w") as file:
                file.write(inv_list)
            
            with open(".invlist.txt","rb") as file:
                unencrypted_inv_list = file.read()

            encrypted_inv_list = f.encrypt(unencrypted_inv_list)

            with open(".invlist.txt", "wb") as file:
                file.write(encrypted_inv_list)

        else:
            cleanup()

main(inv_list)
