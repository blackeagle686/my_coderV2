import ast
import contextlib
import io
import multiprocessing
import sys
import time
import traceback

# Security: List of disallowed modules and functions
BLACKLIST_IMPORTS = {
    "os", "sys", "subprocess", "shutil", "builtins", "importlib", "socket", 
    "requests", "urllib", "ftplib", "smtplib", "telnetlib", "http"
}

BLACKLIST_FUNCTIONS = {
    "eval", "exec", "open", "compile", "globals", "locals", "super", 
    "getattr", "setattr", "delattr", "input", "breakpoint", "help", 
    "exit", "quit"
}

class SecurityViolation(Exception):
    pass

class SafeVisitor(ast.NodeVisitor):
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] in BLACKLIST_IMPORTS:
                raise SecurityViolation(f"Importing '{alias.name}' is not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] in BLACKLIST_IMPORTS:
            raise SecurityViolation(f"Importing from '{node.module}' is not allowed.")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLACKLIST_FUNCTIONS:
                raise SecurityViolation(f"Calling '{node.func.id}' is not allowed.")
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        # Prevent accessing some dangerous attributes directly if possible, though strict typing makes this hard
        # This is a basic MVP check.
        if node.attr.startswith("__"):
            raise SecurityViolation("Accessing private/dunder attributes is not allowed.")
        self.generic_visit(node)

def validate_code(code: str):
    """
    Parses the code into AST and validates against the blacklist.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax Error: {str(e)}"
    
    visitor = SafeVisitor()
    try:
        visitor.visit(tree)
    except SecurityViolation as e:
        return f"Security Violation: {str(e)}"
    return None

def execute_user_code(code: str, timeout: int = 2):
    """
    Executes the code in a separate process to enforce timeout and capture output.
    This is NOT a full OS-level sandbox, but uses AST checks + multiprocessing.
    """
    
    # 1. First validate the code
    validation_error = validate_code(code)
    if validation_error:
        return {"stdout": "", "stderr": validation_error, "error": True}

    # 2. Define the execution wrapper
    def target(code, result_dict):
        # Redirect stdout/stderr
        out_buffer = io.StringIO()
        err_buffer = io.StringIO()
        
        with contextlib.redirect_stdout(out_buffer), contextlib.redirect_stderr(err_buffer):
            try:
                # Execute in a restricted scope
                # We give it a limited set of builtins to further restrict
                safe_builtins = {k: v for k, v in __builtins__.items() if k not in BLACKLIST_FUNCTIONS and k != '__import__'}
                # We can allow __import__ but wrap it, or rely on AST check. 
                # AST check is safer for "import os", but runtime __import__ can bypass AST.
                # For this MVP, we remove __import__ from builtins which effectively kills all imports 
                # unless we restore specific ones. 
                # BUT, users might need math, datetime, random. 
                # So we should probably allow __import__ but rely on AST to catch malicious ones.
                # However, malicious users can do `__builtins__['__import__']('os')`.
                # So we remove `__import__` and pre-import allowed modules if needed, OR we trust AST + specific runtime checks.
                # For an MVP, we will rely on AST check + removing `open`, `exec`, `eval` from builtins.
                
                restricted_globals = {"__builtins__": safe_builtins}
                exec(code, restricted_globals)
            except Exception:
                traceback.print_exc()
        
        result_dict["stdout"] = out_buffer.getvalue()
        result_dict["stderr"] = err_buffer.getvalue()

    manager = multiprocessing.Manager()
    result = manager.dict()
    result["stdout"] = ""
    result["stderr"] = ""
    
    p = multiprocessing.Process(target=target, args=(code, result))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return {"stdout": result["stdout"], "stderr": "Error: Execution timed out.", "error": True}
    
    return {"stdout": result["stdout"], "stderr": result["stderr"], "error": bool(result["stderr"])}
