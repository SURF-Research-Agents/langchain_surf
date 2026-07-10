## How to use langchain_surf

Connect LangChain with SURF services

The project setup is documented in [project_setup.md](project_setup.md). Feel free to remove this document (and/or the link to this document) if you don't need it.

## Installation

To install langchain_surf from GitHub repository, do:

```console
git clone git@github.com:SURF-Research-Agents/langchain_surf.git
cd langchain_surf
python -m pip install .
```

## Example

### Simple Chat bot

The library contains a simple chat interface with Willma. This largely a convenience class that wraps the `ChatOpenAI` class.

```python
import os
from langchain_surf import ChatWillma   
from dotenv import load_dotenv

load_dotenv('../../.env')  
api_key = os.getenv("AIHUB_API_KEY")
model = "default-text-large"


model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)

result = model.invoke("What is the capital of France?")
print(result)
```

### HPC Tools

The library contains a wrapper to define tools that are executed on HPC via slurm (e.g. snellius). An example can be found [here](./examples/tool.py). 
To use you need to:

1. create a directory on snellius at `~/test_rsa`. This is where the files of the job will be created and is hardcoded for now [here](https://github.com/SURF-Research-Agents/langchain_surf/blob/4652e52dfa547240a74fe967c50f5a13d7463164/src/langchain_surf/tools/utils/slurm_connector.py#L48)

2. create a virtual environemnt at `~/test_rsa/.venv`. This environment must contain all the dependencies needed to execute the tools. It should also use exactly the same python version as the one used in the local environment (e.g. your laptop) to run the [example](./examples/tool.py)

3. you need to set up the objecstore credential on snellius and your local machine. Follow the instruction [here](https://servicedesk.surf.nl/wiki/spaces/WIKI/pages/112591355/AWS+S3+client+awscli). As explained in this page you will need to create a `~/.aws/config` file and a `~/.aws/credentials` files. You should have received the keys and secret keys from our object store team.

4. Get a SLURM JWT from snellius. Log in on snellius and type `scontrol token` copy the token given as an answer

5. Put all your credentials in a .env file:
    -   AIHUB_API_KEY : Token from AI Hub
    -   SLURM_JWT : SLURM Token from snellius
    -   OS_KEY : Object store key
    -   OS_SECRET_KEY: Object store secret key

Once all of that is set up you can use execute this [file](./examples/tool.py). and it should launch a calculation on snellius and return the result back. The file is roughly as follow:


```python
import os
from typing import Optional
import json 
from langchain.agents import create_agent
from langchain_surf import ChatWillma   
from langchain_surf.tools.hpc_tools import tool
from dotenv import load_dotenv

# load the credentials
load_dotenv(dotenv_path="/path/to/.env")
api_key = os.getenv("AIHUB_API_KEY")
....

# create the slurm data
slurm_data = {
    "url": "https://slurm.snellius.surf.nl",
    "api_ver": "v0.0.43",
    "user_name": "nicolasr",
    "slurm_jwt": slurm_jwt,
}

# create the onject store data
os_data = {
    "url": "https://objectstore.surf.nl",
    "os_access_key": os_key,
    "os_secret_key": os_secret,
}

# put all the slurm + object store together
hpc_opt = {
    'slurm_data': slurm_data,
    'os_data': os_data
}

# create the model
model = ChatWillma(
    model="default-text-large",
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)

# HPC tool Wrapper
# This toll will be executed on Snellius
@tool(hpc=hpc_opt)
def calculate_expression(expression):
    """Evaluate the mathematical expression and return the result."""
    ....
    return 

# Crete the agent and give it the tool
agent = create_agent(model, 
                     tools=[calculate_expression],
                     system_prompt="You are a helpful assistant. Be concise and accurate.")

# invoke it and print the result
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's 3+4?"}]}
)
print(result)
```

## Contributing

If you want to contribute to the development of langchain_surf,
have a look at the [contribution guidelines](CONTRIBUTING.md).

## Credits

This package was created with [Copier](https://github.com/copier-org/copier) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).
