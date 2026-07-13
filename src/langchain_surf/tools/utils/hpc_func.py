import dill
import json 


from langchain_surf.tools.utils.slurm_connector import SLURMAPIConnector
from langchain_surf.tools.utils.object_store_connector import ObjectStoreConnector

class HPCFunc:
    def __init__(self, 
                 func, 
                 slurm_data, 
                 os_data,
                 dill_file_name = 'serialized_func.pkl',
                 json_output_file_name='json_output.json',
                 python_file_name = 'execute_python_script.py'):
        
        self.func = func
        self.slurm_data = slurm_data
        self.os_data = os_data
        self.dill_file_name = dill_file_name
        self.json_output_file_name = json_output_file_name
        self.python_file_name = python_file_name

        slurm_default_settings = {
                    "output_file_name": "tool.out",
                    "error_file_name": "tool.err",
                    "jobname": "tool",
                    "time": 600,
                    "partition": "rome",
                    "nodes": 1,
                    "tasks": 1,
                    "cpus_per_task": 1,
                }

        self.slurm_connector = SLURMAPIConnector(slurm_data, slurm_default_settings)
        self.os_connector = ObjectStoreConnector(os_data)

    def _write_python_script(self):

        file_str = []
        file_str += ["import dill"]
        file_str += ["import json"]
        file_str += [f"with open('{self.dill_file_name}', 'rb') as fopen:"]
        file_str += ["    exec_tool = dill.load(fopen)"]
        file_str += ["status = exec_tool()"]
        
        with open(self.python_file_name, 'w') as file:
            file.write('\n'.join(file_str))
            
        return '\n'.join(file_str)

    def _bash_script(self):
        file_str = []
        file_str += ["#!/bin/bash"]
        file_str += ['source .venv/bin/activate']
        file_str += [f'mkdir {self.os_data["bucketname"]}']
        file_str += [f'cd {self.os_data["bucketname"]}']
        file_str += [f"aws s3 sync s3://{self.os_data['bucketname']}/ ."]
        file_str += [f"python {self.python_file_name}"]
        file_str += [f"aws s3 sync . s3://{self.os_data['bucketname']}/"]
        return '\n'.join(file_str)

    def __call__(self, *args, **kwargs):
        
        # defined the function to be serialized
        def serialized_call():
            try:
                with open(self.json_output_file_name, 'w') as file: 
                    json.dump(self.func(*args, **kwargs), file, indent=4)
                return True
            except Exception as e:
                print(e)
                return 
            
        # serialize the function
        with open(self.dill_file_name, 'wb') as fopen:
          dill.dump(serialized_call, fopen, recurse=False)

        # write the python script
        self._write_python_script()

        # upload all the files to the object store
        self.os_connector.create_bucket()
        self.os_connector.upload_files_to_os([self.python_file_name, 
                                              self.dill_file_name])
        
        
        # submit the job to the SLURM API
        self.slurm_connector.submit_and_monitor_slurm_job(job_script=self._bash_script(), 
                                                                monitor_interval=10)
        
        result = self.os_connector.read_files_from_os(self.json_output_file_name)
        print(result)

        return result


if __name__ == "__main__":

    import os
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="/Users/renau001/projects/hpml/ai4science_platform/rsa_langgraph/.env")
    
    slurm_jwt = os.getenv("SLURM_JWT")
    os_key = os.getenv("OS_KEY")
    os_secret = os.getenv("OS_SECRET_KEY")
    api_key = os.getenv("AIHUB_API_KEY")
    
    slurm_data = {
        "url": "https://slurm.snellius.surf.nl",
        "api_ver": "v0.0.43",
        "user_name": "nicolasr",
        "slurm_jwt": slurm_jwt,
    }

    os_data = {
        "url": "https://objectstore.surf.nl",
        "os_access_key": os_key,
        "os_secret_key": os_secret,
    }

    def sum(x,y): 
        return x+y

    hpc_sum = HPCFunc(sum, slurm_data=slurm_data, os_data=os_data)
    print(hpc_sum(1,2))
