import os
from dotenv import load_dotenv
from langchain_surf.tools.utils.hpc_func import hpc_func

load_dotenv('../../../.env')

slurm_jwt = os.getenv("SLURM_JWT")
api_key = os.getenv("AIHUB_API_KEY")

slurm_data = {
    "url": "https://slurm.snellius.surf.nl",
    "api_ver": "v0.0.43",
    "user_name": "nicolasr",
    "slurm_jwt": slurm_jwt,
}

@hpc_func(slurm_data)
def custom_sum(x, y):
    """Return the sum of two numbers.

    This function replaces the previous redefinition of the built‑in ``sum``
    to avoid shadowing the Python built‑in function.
    """
    return x + y

print(custom_sum(1, 2))
