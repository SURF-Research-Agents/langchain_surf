import dill
import json
with open('serialized_func.pkl', 'rb') as fopen:
    exec_tool = dill.load(fopen)
status = exec_tool()