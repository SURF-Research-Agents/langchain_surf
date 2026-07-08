from deepagents import create_deep_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_surf.chat_models.chat_willma import ChatWillma

class DeepAgentChain:

    def __init__(self, 
                 model, 
                 api_key, 
                 temperature=0.1, 
                 max_tokens=1000, 
                 timeout=30,
                 tools = None,
                 instructions = None):
        
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout 
        if tools is None:
            tools = []
        self.tools = tools 
        if instructions is None:
            instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""
        self.instructions = instructions

    def __call__(self):
        return self.build_chain()

    def build_chain(self):
        
        prompt = ChatPromptTemplate.from_template("Question: {input}")
        
        llm = ChatWillma(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            api_key=self.api_key,
        )
        agent = create_deep_agent(
            model=llm,
            tools=[self.tools],
            system_prompt=self.instructions,
        )
        return prompt | agent