import os
from dotenv import load_dotenv
from langchain_surf.tools.utils.hpc_func import HPCFunc

load_dotenv('../../../.env')

slurm_jwt = os.getenv("SLURM_JWT")
api_key = os.getenv("AIHUB_API_KEY")

slurm_data = {
    "url": "https://slurm.snellius.surf.nl",
    "api_ver": "v0.0.43",
    "user_name": "nicolasr",
    "slurm_jwt": slurm_jwt,
}

def custom_sum(x, y):
    """Return the sum of two numbers.

    This function replaces the previous redefinition of the built‑in ``sum``
    to avoid shadowing the Python built‑in function.
    """
    return x + y

hpc_sum = HPCFunc(custom_sum,
                  slurm_data=slurm_data,
                  container_image='langchain_surf.sif')

print(hpc_sum(1, 2, slurm_resources={'jobname':'new_job'}))
