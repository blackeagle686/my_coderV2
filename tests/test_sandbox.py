import sys
import os
import unittest

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.sandbox import execute_user_code, validate_code

class TestSandboxSecurity(unittest.TestCase):
    
    def test_allow_safe_code(self):
        code = "print('Hello')"
        result = execute_user_code(code)
        self.assertFalse(result['error'])
        self.assertIn("Hello", result['stdout'])

    def test_block_import_os(self):
        code = "import os"
        result = execute_user_code(code)
        self.assertTrue(result['error'])
        self.assertIn("Security Violation", result['stderr'])

    def test_block_import_sys(self):
        code = "import sys"
        result = execute_user_code(code)
        self.assertTrue(result['error'])
        self.assertIn("Security Violation", result['stderr'])
        
    def test_block_exec(self):
        code = "exec('print(1)')"
        result = execute_user_code(code)
        self.assertTrue(result['error'])
        self.assertIn("Security Violation", result['stderr'])

    def test_block_eval(self):
        code = "eval('1+1')"
        result = execute_user_code(code)
        self.assertTrue(result['error'])
        self.assertIn("Security Violation", result['stderr'])

    def test_block_open(self):
        code = "open('/etc/passwd')"
        result = execute_user_code(code)
        self.assertTrue(result['error'])
        self.assertIn("Security Violation", result['stderr'])
        
    def test_block_dunder_attributes(self):
        code = "print([].__class__)"
        result = execute_user_code(code)
        self.assertTrue(result['error'])
        self.assertIn("Security Violation", result['stderr'])

    def test_timeout_infinite_loop(self):
        code = "while True: pass"
        result = execute_user_code(code, timeout=1) # 1 sec timeout
        self.assertTrue(result['error'])
        self.assertIn("timed out", result['stderr'])

if __name__ == '__main__':
    unittest.main()
