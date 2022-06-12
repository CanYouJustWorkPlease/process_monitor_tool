#  Process monitoring tool

`process_monitor_tool` is a CLI python app that launches a specified process,  which then monitors it at a given interval and constantly writes the data to a file, while printing the data written to the file to the console in the form of a cli GUI.

#### Python version used:
Python 3.10.4 x64


#### Installing requirements:
Naviagate to the `process_monitor_tool` directory and issue the following command:

`pip install -r .\requirements.txt`

#### Usage:
```
process_monitor_tool.py [-h] -p   -i   [-hg] [-sp  | -rp ] [-d ]

Launch a process, monitor it at a given interval and constantly write the data to a file

options:
  -h  , --help          show this help message and exit
  -p  , --path          provide the ABSOLUTE path of the process that you want to launch
  -i  , --interval      set the interval as an integer or float value as seconds
  -hg , --hide_gui      hide cli gui
  -sp , --save_path     set the current path for storing the data. Provide the ABSOLUTE path
  -rp , --restore_path  restore default path for data storing
  -d  , --debug         display traceback and custom error message

Given that C: is the system drive, here are some examples:

process_monitor_tool.py -p "C:\Windows\System32\notepad.exe" -i 1
process_monitor_tool.py -p "C:\Windows\System32\notepad.exe" -i 1 -hg
process_monitor_tool.py -p "C:\Windows\System32\notepad.exe" -i 1 -sp "C:\Users\Public\Documents"
process_monitor_tool.py -p "C:\Windows\System32\notepad.exe" -i 1 -rp
process_monitor_tool.py -p "C:\Windows\System32\notepad.exe" -i 1 -d
```

#### Unit testing
To perform unit testing navigate to the `process_monitor_tool` directory and issue the following command:

`python.exe -m unittest -v .\process_monitor_tool_test.py`
