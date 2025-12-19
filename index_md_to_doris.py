from pathlib import Path

import cocoindex
from conf import settings
from doris_target import DorisTarget
from cocoindex.llm import LlmApiType
from cocoindex.auth_registry import add_transient_auth_entry


DOC_ROOT = Path(settings.docs.get("doc_root"))

# Doris connection from conf.ini
_dc = settings.doris
DORIS_FE_HOST = _dc.get("host", "localhost")
DORIS_FE_PORT = int(_dc.get("http_port", 8030))
DORIS_QUERY_PORT = int(_dc.get("query_port", 9030))
DORIS_DATABASE = _dc.get("db_name", "cocoindex_demo")
DORIS_TABLE = _dc.get("table_name", "document_embeddings")
DORIS_USER = _dc.get("user", "root")
DORIS_PASSWORD = _dc.get("password", "")

# Chunking from conf.ini
CHUNK_SIZE = int(settings.docs.get("chunk_size", "500"))
CHUNK_OVERLAP = int(settings.docs.get("chunk_overlap", "100"))

# Embedding settings from conf.ini
_emb = settings.embedding
EMB_TYPE = _emb.get("type", "openai").lower()
EMB_MODEL = _emb.get("model", "text-embedding-3-small")
EMB_BASE_URL = _emb.get("base_url", "https://api.openai.com/v1")
EMB_API_KEY = _emb.get("api_key", "")
EMB_DIM = int(_emb.get("embed_dim", "1536"))


@cocoindex.transform_flow()
def text_to_embedding(
    text: cocoindex.DataSlice[str],
) -> cocoindex.DataSlice[list[float]]:
    if EMB_TYPE == "openrouter":
        api_type = LlmApiType.OPEN_ROUTER
    elif EMB_TYPE == "openai":
        api_type = LlmApiType.OPENAI
    else:
        raise ValueError(
            f"Unsupported embedding.type for indexing: {EMB_TYPE}. Use 'openai' or 'openrouter'."
        )

    return text.transform(
        cocoindex.functions.EmbedText(
            api_type=api_type,
            model=EMB_MODEL,
            address=EMB_BASE_URL,
            output_dimension=EMB_DIM,
            api_key=add_transient_auth_entry(EMB_API_KEY),
        )
    )


@cocoindex.flow_def(name="MdToDoris")
def md_to_doris_flow(flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope) -> None:
    data_scope["docs"] = flow_builder.add_source(
        cocoindex.sources.LocalFile(
            path=str(DOC_ROOT),
            included_patterns=["**/*.md", "**/*.mdx"],
            excluded_patterns=["**/*.pdf", "**/*.png", "**/*.jpg", "**/*.jpeg"],
        )
    )

    out = data_scope.add_collector()

    with data_scope["docs"].row() as doc:
        doc["chunks"] = doc["content"].transform(
            cocoindex.functions.SplitRecursively(),
            language="markdown",
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        with doc["chunks"].row() as chunk:
            chunk["embedding"] = text_to_embedding(chunk["text"])
            out.collect(
                _key=cocoindex.GeneratedField.UUID,
                filename=doc["filename"],
                location=chunk["location"],
                text=chunk["text"],
                embedding=chunk["embedding"],
            )

    out.export(
        "md_embeddings",
        DorisTarget(
            fe_host=DORIS_FE_HOST,
            fe_http_port=DORIS_FE_PORT,
            query_port=DORIS_QUERY_PORT,
            database=DORIS_DATABASE,
            table=DORIS_TABLE,
            username=DORIS_USER,
            password=DORIS_PASSWORD,
            batch_size=5000,
        ),
        primary_key_fields=["_key"],
    )