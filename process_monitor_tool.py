import argparse, asyncio, sys, psutil, configparser, datetime, os, json, locale, csv, warnings, pefile, traceback, re
from pathvalidate.argparse import validate_filepath_arg
from typing import Dict, List
from decimal import Decimal
# debug = True displays the traceback and custom error message
# debug = False displays only the custom error message
debug: bool = False

# Hides a warning message about deprecation related to asyncio.get_event_loop().run_until_complete(main())
warnings.filterwarnings("ignore", category=DeprecationWarning)

# I used mypy for type checking from Python Type Checking (Guide):
# https://realpython.com/python-type-checking/

PID = None
interval = 0

def parse_args(args):
    '''Defines all the arguments that the current cli app is going to use.'''
    parser = argparse.ArgumentParser(description="Launch a process, monitor it at a given interval and constantly write the data to a file",
            epilog=
            ('Given that C: is the system drive, here are some examples: \
            \n\nprocess_monitor_tool.py -p "C:\Windows\System32\calc.exe" -i 1 \
            \nprocess_monitor_tool.py -p "C:\Windows\System32\calc.exe" -i 1 -hg \
            \nprocess_monitor_tool.py -p "C:\Windows\System32\calc.exe" -i 1 -sp "C:\\Users\\Public\\Documents" \
            \nprocess_monitor_tool.py -p "C:\Windows\System32\calc.exe" -i 1 -rp')
            , formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", "--path", type=str, metavar=" ", help="provide the ABSOLUTE path of the process that you want to launch", required=True)
    parser.add_argument("-i", "--interval", type=float, metavar=" ", help="set the interval as an integer or float value as seconds", required=True)
    parser.add_argument("-hg", "--hide_gui", action="store_true", help="hide cli gui")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-sp", "--save_path", type=validate_filepath_arg, metavar="", help="set the current path for storing the data. Use RELATIVE or ABSOLUTE path")
    group.add_argument("-rp","--restore_path", action="store_true", help="restore default path for data storing")
    return parser.parse_args(args)



def validate(args):
    '''
    Contains conditions for the arguments to test against. This function is also used for unittest.
    '''

    # Checks if the path or save path exceed 256 characters
    if len(args.path) > 256:
        raise FileNotFoundError("Path name is too long, it exceeds 256 characters. Please make the path shorter.")
    elif args.save_path != None and len(args.save_path) > 256:
        raise FileNotFoundError("Save path name is too long, it exceeds 256 characters. Please make the path shorter.")

    # Checks if the path is not existing
    if not os.path.exists(args.path):
        raise FileNotFoundError(f'"{args.path}" file path does not exist. Please use an appropriate path.')
    
    # Checks if the system drive in the save path is not existing
    if args.save_path != None:
        regexp = re.compile(r'^[A-Z]:.+$')
        if regexp.search(args.save_path) and not os.path.exists(args.save_path[:2]):
            raise FileNotFoundError(f'"{args.save_path}" save path does not exist. Please use an appropriate save path.')

    # Checks if a folder is denied access from being created based on the path provided for save path
    if args.save_path != None:
        testpath = f"{args.save_path}\\test_directory\\"
        os.makedirs(testpath, exist_ok=True)
        if not os.path.exists(testpath):            
            raise PermissionError("Access denied. Please choose a different save path.")
        elif os.path.exists(testpath):
            os.rmdir(testpath)

    # Checks if a file is executable and if it does not end in .exe .
    if os.access(args.path, os.X_OK) and not args.path.endswith('.exe'):
        _, file = os.path.split(args.path)
        raise OSError(f'"{file}" is not a process. It does not end and in .exe . Please pick a file that ends in .exe .') 

    # Checks if a file is not a true .exe .
    try:
        if not pefile.PE(args.path):       
            raise pefile.PEFormatError
    except pefile.PEFormatError:
        _, file = os.path.split(args.path)
        raise OSError(f'"{file}" is not an executable file. This file was masked as a .exe . Please use a valid .exe file.')
    
    if args.interval < 0:
        raise ValueError(f"Interval has a negative value: {args.interval}. Please use a positive value.")

    if args.interval == 0:
        raise ValueError(f"Interval has a value of zero. Please use a positive value.")

    return

    

def print_data_csv_location():
    '''
    Prints the location of the data files as a result of monitoring.
    '''

    global abs_path_csv
    global abs_path_json
    print("\nMonitoring has finished!")
    print("\nProcess monitoring data is stored at: \n" + abs_path_csv)    
    print("\nStatic data is stored at: \n" + abs_path_json + "\n")    



async def start_process():
    '''
    Launches the process that has been provided as a value for the argument "path". It also stores the PID of the launched process.
    '''

    global PID
    global interval
    proc = await asyncio.create_subprocess_exec(path, stdin=asyncio.subprocess.PIPE, preexec_fn=None)
    PID = proc.pid
    await proc.communicate()



async def main():
    '''
    Validates the passed arguments, launches a specified process,
    which then monitors it at a given interval and constantly writes the data to a file,
    while printing the data written to the file to the console in the form of a cli GUI
    '''

    global args
    args = parse_args(sys.argv[1:])
    try:
        validate(args)
    except Exception as e:
        if debug:
            print(traceback.format_exc())
        elif not debug:
            print("\n\t", str(type(e).__name__) + ":", e.args[0], "\n")
        sys.exit(1)

    global interval
    interval = args.interval
    global path
    path = args.path
    task = asyncio.create_task(write_stats())
    await start_process()
    print_data_csv_location()
    task.cancel()



async def write_stats():
    '''
    Writes and/or prints the stats related to the launched process as long it exists.
    The data is written to data.csv and static_data.json.
    '''

    global interval

    # The cli GUI is shown by default.
    # if the hide_gui argument is used, the cli GUI will be hidden.
    show_gui: bool = not args.hide_gui

    # Checks if the save path is relative.
    # If it is relative, then it merges the path of the current directory where this very
    # script resides with the path specified in save path.
    if args.save_path != None:
        regexp = re.compile(r'^[A-Z]:.+$')
        if not regexp.search(args.save_path):
            base_path, _ = os.path.split(os.path.realpath(__file__))
            args.save_path = base_path + args.save_path

    # Sets current locale to en_US for adding the capability of displaying thousands separator for numbers.
    locale.setlocale(locale.LC_ALL, 'en_US')


    # Sets the default path to current user's "Documents" folder, regardless of the username.
    default_path: str = f"{os.path.expanduser('~')}\\Documents\\Process monitor data"
    if not os.path.exists(default_path):
        os.makedirs(default_path)

    current_path: str = ""

    # Reads the content of the settings.ini and assigns to new variables the values of the variables within the .ini .
    # settings.ini contains the path where to store the .csv file containing monitoring data,
    # it also contains the restore flag, which if used, restores the current path to the default path for storing .csv .
    config = configparser.ConfigParser()
    config.read("settings.ini")
    set_path_length: int = len(config.get("myvars", "set_path"))
    get_set_path = config.get("myvars", "set_path")
    get_restore_flag: int = int(config.get("myvars", "restore_path_flag"))

    def write_to_ini(var: str, value: str) -> None:
        '''
        Writes the value of the variable to settings.ini .
        '''

        config.set("myvars", var, value)
        with open("settings.ini", "w", newline='') as configfile:
            config.write(configfile)

    # Restores the default path for data storing
    if args.restore_path:    
        current_path = default_path
        write_to_ini("restore_path_flag", "1")
        write_to_ini("set_path", "")

    # Sets the current path to the path stored in the .ini if the restore flag is 0.
    elif set_path_length and get_restore_flag == 0 and args.save_path == None:
        current_path = get_set_path

    # Writes to the .ini the path that was provided as a value for the save_path argument, 
    # while also setting the current path to the same path passed as an argument
    # and setting the restore flag to 0. 
    elif args.save_path != None:
        parent_folder: str = f"{args.save_path}\Process monitor data"
        if not os.path.exists(parent_folder):
            os.makedirs(parent_folder)
        write_to_ini("set_path", f"{parent_folder}")
        current_path = config.get('myvars', 'set_path')
        write_to_ini("restore_path_flag", "0")

    # Sets the current path to user's "Documents" folder.    
    else:
        current_path = default_path

    # Sets the absoulute path for storing data.csv .
    global abs_path_csv
    abs_path_csv = f'{current_path}\data.csv'

    # Sets the absoulute path for storing static_data.json.
    global abs_path_json
    abs_path_json = f'{current_path}\static_data.json'

    def thousands_separator(value: float|str) -> str:
        '''
        Adds thousands separator.
        '''
        return '{0:n}'.format(Decimal(value))

    print("\n")
    print("Monitoring has started!")
    print("\n")
    print("Process monitoring data is currently being written to \"data.csv\" at: \n" + abs_path_csv + "\n")    
    print("Static data was written to \"static_data.json\" at: \n" + abs_path_json)    
    print("\n")

    # Draws the table headers of the cli GUI.
    if show_gui:    
        print("-" * 125)
        print("{:<28} {:<12} {:<17} {:<12} {:<13} {:<10} {:<10}".format(
            "     Elapsed time [24 h]",
            "|    Date",
            "|   Time [24 h]",
            "|   CPU [%]",
            "| Working set [MB]",
            "| Private bytes [MB]",
            "|  Handles")
            )
        print("-" * 125)

    process_path_info = os.path.split(args.path)

    # Static data related to the process gets stored in a dictionary and gets written to static_data.json .
    static_info: Dict[str, str|float|int] = {
        "process_path": process_path_info[0],
        "process_name": process_path_info[1],
        "interval": interval
    }
    with open(abs_path_json, 'w') as jsonfile:
        json.dump([static_info], jsonfile)   


    # Sets the header of the data.csv .
    titles: List[str] = ["elapsed_time", "date", "time", "CPU", "working_set", "private_bytes", "handles"]
    with open(abs_path_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = titles)
        writer.writeheader()


    # counter is used for counting how many lines were written to the data.csv .
    # The counter variable is used in conjunction with the interval to compute the elapsed time.
    counter: int = 0

    # repeats the process of writing/displaying the monitoring data by using the count of
    # seconds used as a value for the interval argument
    while True:
        def padStart(value: int, times: int, character: str) -> str:
            '''
            Pads the start of a string so the alignment of the cli GUI doesn't get affected.
            '''
            return str(value).rjust(times, character)

        def calculate_elapsed_time() -> str:
            '''
            Calculates the elapsed time based on the interval and counter.
            '''

            # I'm using counter - 1 to print the elapsed time starting from zero
            # when the first line of stats, which belongs to python.exe, gets skipped.
            time: float = interval * (counter - 1)
            day: float = time // (24 * 3600)
            time = time % (24 * 3600)
            hour: float = time // 3600
            time %= 3600
            minutes: float = time // 60
            time %= 60
            seconds: float = time
            time *= 1000
            milliseconds: int = round(time % 1000)

            return "{} day(s) {}:{}:{}.{}".format(
                thousands_separator(day),
                padStart(int(hour), 2, "0"), 
                padStart(int(minutes), 2, "0"), 
                padStart(int(seconds), 2, "0"), 
                padStart(milliseconds, 3, "0")
                )

        global PID
        process_stats = psutil.Process(PID)

        #  Dynamic data related to process monitoring gets stored in a dictionary
        dynamic_info: Dict[str, str|float|int] = {
        "elapsed_time": calculate_elapsed_time(),                
        "date": datetime.datetime.now().strftime("%d-%m-%Y"),
        "time": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],                  
        "CPU": float("{:.2f}".format(process_stats.cpu_percent(interval=0.1)/psutil.cpu_count())),
        "working_set": round(process_stats.memory_info().wset / (1024 * 1024), 2),
        "private_bytes": round(process_stats.memory_info().private / (1024 * 1024), 2),
        "handles": process_stats.num_handles()
        }

        # Prints all the data in the cli GUI related to the process after some formatting had been applied.
        if show_gui:
            # I'm using counter > 0 to not print the first line of stats, which belongs to python.exe .
            if counter > 0:
                print("{:<31} {:<15} {:<18} {:<11} {:<20} {:<17} {:<5}".format(
                dynamic_info["elapsed_time"].rjust(29, " "),                     
                dynamic_info["date"], 
                dynamic_info["time"],
                str(dynamic_info["CPU"]).rjust(6, " "), 
                thousands_separator(str(dynamic_info["working_set"])).rjust(13, " "), 
                thousands_separator(str(dynamic_info["private_bytes"])).rjust(13, " "), 
                thousands_separator(str(dynamic_info["handles"])).rjust(7, " "), 
                ))  

        # Writes all the data related to the process to the data.csv .
        # I had previously implemented a data.json, but I realized that if a processes is monitored for years
        # the csv format is more suitable since it takes less size by not storing the same data over and over, hence it takes
        # less write/read time than json .
        with open(abs_path_csv, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = titles)
            # I'm using counter > 0 to not write the first line of stats, which belongs to python.exe .
            if counter > 0:
                writer.writerows([dynamic_info])
            counter += 1
        await asyncio.sleep(interval)



try:
    if __name__ == '__main__':
        asyncio.get_event_loop().run_until_complete(main())
except KeyboardInterrupt:
    # Closes the launched program by hitting CTRL + C 
    # and prints the location of data.csv and static_data.json
    print_data_csv_location()