import os
import re
import time
from pathlib import Path
from typing import List, Dict

import pandas as pd
from doris_vector_search import DorisVectorClient, AuthOptions, IndexOptions

from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag_lib import get_embedding_model
from conf import settings


DOC_ROOT = Path(settings.docs.get('doc_root'))


CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def collect_markdown_files(root: Path) -> List[Path]:
    files = list(root.rglob("*.md")) + list(root.rglob("*.mdx"))
    return sorted(set(files))


def read_markdown(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def extract_title_from_markdown(text: str, default: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("## "):
            return line[3:].strip()
    return default


def clean_text(text: str) -> str:
    # remove docusaurus frontmatter
    text = re.sub(r"^---.*?---\s*", "", text, flags=re.S | re.M)
    lines = [ln.rstrip() for ln in text.splitlines()]
    return "\n".join(lines).strip()


def build_documents() -> List[Dict]:
    files = collect_markdown_files(DOC_ROOT)
    print(f"Found {len(files)} markdown files under {DOC_ROOT}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len
    )

    docs: List[Dict] = []
    cur_id = 1

    for fp in files:
        raw = read_markdown(fp)
        cleaned = clean_text(raw)
        if not cleaned:
            continue

        title = extract_title_from_markdown(cleaned, default=fp.stem)
        chunks = text_splitter.split_text(cleaned)

        rel_path = str(fp.relative_to(DOC_ROOT))
        for chunk in chunks:
            docs.append(
                {
                    "id": cur_id,
                    "path": rel_path,
                    "title": title,
                    "content": chunk,
                }
            )
            cur_id += 1

    print(f"Built {len(docs)} text chunks")
    return docs


def embed_documents(docs: List[Dict]) -> pd.DataFrame:
    if not docs:
        raise ValueError("No documents to embed")

    embeddings = get_embedding_model()

    texts = [d["content"] for d in docs]
    print("Generating embeddings via Ollama (this may take a while)...")
    vectors = embeddings.embed_documents(texts)
    print(f"Got {len(vectors)} embeddings; dim={len(vectors[0]) if vectors else 0}")

    df = pd.DataFrame(
        [
            {
                "id": d["id"],
                "path": d["path"],
                "title": d["title"],
                "content": d["content"],
                "embedding": vec,
            }
            for d, vec in zip(docs, vectors)
        ]
    )
    return df


def write_to_doris(df: pd.DataFrame):
    """Write embeddings DataFrame into an existing Doris database.
    assume DB_NAME already exists in Doris.
    `CREATE DATABASE IF NOT EXISTS doris_rag_db;`
    """
    doris_conf = settings.doris
    auth = AuthOptions(
        host=doris_conf.get('host', 'localhost'),
        query_port=int(doris_conf.get('query_port', 9030)),
        http_port=int(doris_conf.get('http_port', 8030)),
        user=doris_conf.get('user', 'root'),
        password=doris_conf.get('password', ''),
    )
    db_name = doris_conf.get('db_name')
    table_name = doris_conf.get('table_name')

    client = DorisVectorClient(db_name, auth_options=auth)

    index_options = IndexOptions(index_type="hnsw", metric_type="inner_product")

    print("Creating/opening table and uploading data to Doris...")
    try:
        table = client.create_table(
            table_name,
            df,
            index_options=index_options,
        )
    except Exception as e:
        print(f"create_table failed, trying to open existing table: {e}")
        table = client.open_table(table_name)
        table.insert(df)

    print("Waiting for index build...")
    time.sleep(5)

    client.close()
    print("Finished writing data to Doris.")


def main():
    docs = build_documents()
    if not docs:
        print("No docs found; exit.")
        return

    df = embed_documents(docs)
    write_to_doris(df)


if __name__ == "__main__":
    main()
