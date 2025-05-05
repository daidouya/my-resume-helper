from backend.chains import (conversation_chain, 
                            recommend_people_chain, 
                            rout_chain,
                            search_chain)
from backend.helper import get_message_history

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda

def router(info: dict):
    if 'rag' in info['choice'].lower():
        return recommend_people_chain
    elif 'agent' in info['choice'].lower():
        return search_chain
    else:
        return conversation_chain

full_chain = {
    "choice": rout_chain, 
    'input': lambda x: x['input'], 
    "resume": lambda x: x['resume'],
    "history": lambda x: x['history']
    } | RunnableLambda(router)

chain_with_memory = RunnableWithMessageHistory(
        full_chain,
        get_message_history,
        input_messages_key="input",     # key from frontend
        history_messages_key="history"
    )
