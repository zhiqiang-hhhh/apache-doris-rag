import os
import pandas as pd
from doris_vector_search import DorisVectorClient, AuthOptions
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from conf import settings
from i18n import get_message

def get_embedding_model():
    emb_conf = settings.embedding
    emb_type = emb_conf.get('type', 'ollama').lower()
    
    if emb_type == 'ollama':
        return OllamaEmbeddings(
            model=emb_conf.get('model', 'bge-m3:latest'),
            base_url=emb_conf.get('base_url', 'http://localhost:11434')
        )
    elif emb_type == 'openai':
        return OpenAIEmbeddings(
            model=emb_conf.get('model'),
            api_key=emb_conf.get('api_key'),
            base_url=emb_conf.get('base_url')
        )
    else:
        raise ValueError(f"Unsupported embedding type: {emb_type}")

def get_llm():
    llm_conf = settings.llm
    llm_type = llm_conf.get('type', 'openai').lower()
    
    if llm_type == 'openai':
        return ChatOpenAI(
            model=llm_conf.get('model'),
            api_key=llm_conf.get('api_key'),
            base_url=llm_conf.get('base_url'),
            temperature=float(llm_conf.get('temperature', 0.2))
        )
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")

def retrieve_context(query: str, top_k: int = 5) -> pd.DataFrame:
    embeddings = get_embedding_model()
    query_vec = embeddings.embed_query(query)

    doris_conf = settings.doris
    auth = AuthOptions(
        host=doris_conf.get('host', 'localhost'),
        query_port=int(doris_conf.get('query_port', 9030)),
        http_port=int(doris_conf.get('http_port', 8030)),
        user=doris_conf.get('user', 'root'),
        password=doris_conf.get('password', ''),
    )
    
    client = DorisVectorClient(doris_conf.get('db_name'), auth_options=auth)
    table = client.open_table(doris_conf.get('table_name'))
    try:
        df = (
            table.search(query_vec, vector_column="embedding")
            .limit(top_k)
            .select(["_key", "filename", "text", "location"])
            .to_pandas()
        )
    finally:
        client.close()
    return df

def query_augment(query: str, history: list = None) -> str:
    """
    Augment the user query using LLM.
    If history is provided, it helps in coreference resolution.
    Otherwise, it refines the query for better retrieval.
    """
    llm = get_llm()
    
    if history and len(history) > 0:
        # Format history for the prompt
        history_str = ""
        for turn in history[-5:]: # Take last 5 turns
            role = turn.get("role", "user")
            content = turn.get("content", "")
            history_str += f"{role}: {content}\n"
            
        prompt = get_message("augment_prompt_history", history_str, query)
    else:
        prompt = get_message("augment_prompt_no_history", query)

    resp = llm.invoke(prompt)
    return resp.content.strip() if hasattr(resp, "content") else str(resp).strip()
