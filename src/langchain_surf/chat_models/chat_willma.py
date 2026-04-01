from langchain_openai import ChatOpenAI

class ChatWillma(ChatOpenAI):
    def __init__(self, **kwargs):
        if 'base_url' not in kwargs:
            kwargs['base_url'] = 'https://willma.surf.nl/api/v0'
        else:
            raise ValueError("base_url is not allowed to be set for Willma, it is fixed to 'https://willma.surf.surf/v1'")
        super().__init__(**kwargs)