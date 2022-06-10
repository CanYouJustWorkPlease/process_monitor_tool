import unittest, os
from process_monitor_tool import parse_args, validate

global sys_drive
sys_drive = os.environ['SYSTEMDRIVE']
global calculator
calculator = f"{sys_drive}\\Windows\\System32\\calc.exe"
global public_documents
public_documents = f'{sys_drive}\\Users\\Public\\Documents\\'

global testfile
def testfile(test_file: str) -> str:        
    if not os.path.exists(test_file):
        file = open(test_file, "x")
        file.close()
    return test_file

class TestCLIMonitor(unittest.TestCase):
    def test_parser(self):
        parser = parse_args(['-p', calculator, '-i', '1', '-sp', public_documents])
        self.assertEqual(parser.path, calculator)
        self.assertEqual(parser.interval, 1)    
        self.assertEqual(parser.save_path, public_documents)   
    


    def test_positive_interval(self):
        parsed_data1 = parse_args(['-p', calculator,'-i', '1'])
        parsed_data2 = parse_args(['-p', calculator,'-i', '99999999999999999999999999999999'])
        parsed_data3 = parse_args(['-p', calculator,'-i', '-1'])
        parsed_data4 = parse_args(['-p', calculator,'-i', '0'])
        parsed_data5 = parse_args(['-p', calculator,'-i', '0.25'])
        parsed_data6 = parse_args(['-p', calculator,'-i', '-99999999999999999999999999999999'])
        try:
            self.assertRaises(ValueError, validate, parsed_data1)
        except:
            pass 
        try:
            self.assertRaises(ValueError, validate, parsed_data2)
        except:
            pass 
        self.assertRaises(ValueError, validate, parsed_data3)
        self.assertRaises(ValueError, validate, parsed_data4)
        try:
            self.assertRaises(ValueError, validate, parsed_data5)
        except:
            pass 
        self.assertRaises(ValueError, validate, parsed_data6)


        
    def test_path(self):
        parsed_data1 = parse_args(['-p', calculator,'-i', '1'])
        parsed_data2 = parse_args(['-p', 'calc.exe','-i', '1'])
        parsed_data3 = parse_args(['-p', 'asd','-i', '1'])
        try:
            self.assertRaises(ValueError, validate, parsed_data1)
        except:
            pass 
        self.assertRaises(FileNotFoundError, validate, parsed_data2)
        self.assertRaises(FileNotFoundError, validate, parsed_data3)
        


    def test_save_path(self):
        parsed_data1 = parse_args(['-p', calculator,'-i', '1', '-sp', public_documents])
        parsed_data2 = parse_args(['-p', 'calc.exe','-i', '1', '-sp', "bzd\\bzd"])
        parsed_data3 = parse_args(['-p', 'asd','-i', '1', '-sp', 'D:\\Users\\Public\\Documents'])
        try:
            self.assertRaises(ValueError, validate, parsed_data1)
        except:
            pass 
        try:
            self.assertRaises(ValueError, validate, parsed_data2)
        except:
            pass 
        self.assertRaises(FileNotFoundError, validate, parsed_data3)



    def test_exe_path(self):
        parsed_data1 = parse_args(['-p', calculator,'-i', '1'])     
        try:
            self.assertRaises(OSError, validate, parsed_data1)
        except:
            pass
        try:
            non_exe_file = testfile(f'{sys_drive}\\Users\\Public\\Documents\\file.png')
            parsed_data2 = parse_args(['-p', non_exe_file,'-i', '1'])
            self.assertRaises(OSError, validate, parsed_data2)
        finally:
            os.remove(non_exe_file)



    def test_path_length(self):
        parsed_data1 = parse_args(['-p', calculator,'-i', '1'])
        # String length is 260 characters long for path.
        parsed_data2 = parse_args(
            ['-p', 
            'test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_\
             test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_\
             test_test_test_test_test_test_',
            '-i', 
            '1']
            )
        try:
            self.assertRaises(FileNotFoundError, validate, parsed_data1)
        except:
            pass
        self.assertRaises(FileNotFoundError, validate, parsed_data2)



    def test_save_path_permissions(self):
        parsed_data1 = parse_args(['-p', calculator,'-i', '1','-sp', public_documents])
        parsed_data2 = parse_args(['-p', calculator,'-i', '1','-sp', f'{sys_drive}\\Windows\\System32'])
        try:
            self.assertRaises(PermissionError, validate, parsed_data1)
        except:
            pass 
        self.assertRaises(PermissionError, validate, parsed_data2)    



    def test_is_file_true_exe(self):
        parsed_data1 = parse_args(['-p', calculator,'-i', '1'])
        try:
            self.assertRaises(OSError, validate, parsed_data1)
        except:
            pass
        try:
            fake_exe = testfile(f'{sys_drive}\\Users\\Public\\Documents\\example.exe')
            parsed_data2 = parse_args(['-p', fake_exe,'-i', '1'])
            self.assertRaises(OSError, validate, parsed_data2)
        finally:
            os.remove(fake_exe)



if __name__ == '__main__':
    unittest.main() 