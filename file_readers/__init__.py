import os
import importlib.util

# Automatically import all modules in the current directory (except __init__.py)
current_dir = os.path.dirname(__file__)
modules = {}

for filename in os.listdir(current_dir):
	if filename.endswith('.py') and filename != '__init__.py':
		module_name = os.path.splitext(filename)[0]  # Strip the .py extension
		file_path = os.path.join(current_dir, filename)

		# Dynamically import the module
		spec = importlib.util.spec_from_file_location(module_name, file_path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)

		# Store the imported module in the modules dictionary
		modules[module_name] = module

		# Optionally, add the module to globals() to make it available directly
		globals()[module_name] = module
