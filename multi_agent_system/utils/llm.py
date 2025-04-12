from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import json

load_dotenv()


#reading json for user specific variables
with open("./config.json", 'r') as f:
    config = json.load(f)

class LLMModel:
    def __init__(self, model_name=config['model_name']):
        self.model_name = model_name
        self.llm = ChatOpenAI(model_name=model_name)

    def get_llm(self):
        return self.llm

