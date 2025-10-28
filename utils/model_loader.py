import os
import sys
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
#from langchain_openai import ChatOpenAI

from utils.config_loader import load_config
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

log = CustomLogger().get_Logger(__name__)

class ModelLoader:
    """
    A Utility class to load Embedding Model and LLM
    """
    def __init__(self):

        load_dotenv()
        self._vaildate_env()
        self.config = load_config()
        log.info("Configuration loaded successfully", config_keys = list(self.config.keys()))

    def _vaildate_env(self):
        """
        Validate necessary environment variables.
        Ensure API keys exist
        """
        required_vars = ["GROQ_API_KEY","GOOGLE_API_KEY"]
        self.api_keys = {key: os.getenv(key) for key in required_vars}
        missing = [k for k, v in self.api_keys.items() if not v]
        if missing:
            log.error("Missing environment variables", missing_vars = missing)
            raise DocumentPortalException("Missing environment variables", sys)
        log.info("Environment variables validated", available_keys = [k for k in self.api_keys if self.api_keys[k] ])

    def load_embedding(self):
        """
        Method to load Embedding Model
        """
        try:
            log.info("Loading embedding model...")
            model_name = self.config["embedding_model"]["model_name"]
            return GoogleGenerativeAIEmbeddings(model=model_name)
        except Exception as e:
            log.error("Error loading embedding model",str(e))
            raise DocumentPortalException("Failed to load embedding model",sys)
        
    def load_llm(self):
        """
        Method to load LLM
        """
        llm_block = self.config["llm"]
        log.info("Loading LLM ")

        provider_key = os.getenv("LLM_PROVIDER",'groq')

        if provider_key not in llm_block:
            log.error('No provider key found', provider_key=provider_key)
            raise ValueError(f"Provider: {provider_key} not found in config")
        llm_config = llm_block[provider_key]
        provider = llm_config['provider']
        model_name = llm_config['model_name']
        #model_name = llm_config.get('model_name')
        temperature = llm_config.get('temperature', 0.2)
        max_output_tokens = llm_config.get('max_output_tokens', 2048)
        
        log.info("Loading LLM", provider=provider, model=model_name,temperature=temperature,max_tokens =max_output_tokens)

        if provider == 'google':
            return ChatGoogleGenerativeAI(
                model = model_name,
                api_key = self.api_keys["GOOGLE_API_KEY"],
                temperature = temperature,
                max_tokens = max_output_tokens

            )

        elif provider =='groq':
            return ChatGroq(
                model=model_name,
                api_key=self.api_keys["GROQ_API_KEY"],
                temperature=temperature,
                max_tokens=max_output_tokens
            )
        
        else:
            log.error("Unsupported LLM provider", provider = provider)
            raise ValueError(f"Unsupported LLM provider:{provider}")
        

if __name__ == "__main__":
    model_loader=ModelLoader()

    embedding = model_loader.load_embedding()
    print(f"Embedding model loaded :{embedding}")
    emb_result = embedding.embed_query("Hello, how are you?")
    print(f"Embedding result:{emb_result}")

    llm = model_loader.load_llm()
    print(f"LLM loaded:{llm}")
    llm_result = llm.invoke("Hello, how are you?")
    print(f"LLM result:{llm_result.content}")
