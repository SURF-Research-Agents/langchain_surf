import os
from dotenv import load_dotenv 
from langchain_surf.tools.utils.hpc_func import HPCFunc

load_dotenv('../../../.env')

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