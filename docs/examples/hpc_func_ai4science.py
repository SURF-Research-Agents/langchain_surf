from ai4science_client import Ai4ScienceClient, job

_BASE_URL = "https://ai4science.dev.sdp.surf.nl"
_USER = ""
_TOKEN = ""

client = Ai4ScienceClient(base_url=_BASE_URL, user=_USER, token=_TOKEN)

def custom_sum(x, y):
    """Return the sum of two numbers.

    This function replaces the previous redefinition of the built‑in ``sum``
    to avoid shadowing the Python built‑in function.
    """
    return x + y

print(client.run(custom_sum, 1, 2, stream=True))


@job(base_url=_BASE_URL, user=_USER, token=_TOKEN, stream=True)
def custom_sum_decorated(x, y):
    """Return the sum of two numbers.

    This function replaces the previous redefinition of the built‑in ``sum``
    to avoid shadowing the Python built‑in function.
    """
    return x + y

print(custom_sum_decorated(1, 2))
