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
    "requests", "urllib", "ftplib", "smtplib", "telnetlib", "http", "multiprocessing", "threading"
}

BLACKLIST_FUNCTIONS = {
    "eval", "exec", "open", "compile", "globals", "locals", 
    "getattr", "setattr", "delattr", "input", "breakpoint", "help", 
    "exit", "quit"
}

# Essential dunder methods for classes to work correctly
ALLOWED_DUNDERS = {
    "__init__", "__str__", "__repr__", "__len__", "__getitem__", 
    "__setitem__", "__iter__", "__next__", "__enter__", "__exit__", 
    "__call__", "__add__", "__sub__", "__mul__", "__truediv__", "__name__"
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
        if node.attr.startswith("__") and node.attr not in ALLOWED_DUNDERS:
            raise SecurityViolation(f"Accessing private/dunder attribute '{node.attr}' is not allowed.")
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
                # We allow __import__ because we rely on the AST validation step 
                # to block malicious modules before execution.
                safe_builtins = {k: v for k, v in __builtins__.items() if k not in BLACKLIST_FUNCTIONS}
                
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
