from rag_lib import get_llm, retrieve_context, query_augment
from i18n import get_message


def main():
    llm = get_llm()
    history = []
    while True:
        q = input(get_message("cli_input_prompt")).strip()
        if not q:
            break
        
        augmented_q = query_augment(q, history)
        print(get_message("cli_augmented_query", augmented_q))
        
        df = retrieve_context(augmented_q, top_k=5)
        ctx = "\n\n".join(
            f"[{r['path']} - {r['title']}]\n{r['content']}" for _, r in df.iterrows()
        )
        prompt = get_message("cli_retrieved_docs", ctx, q)
        ans = llm.invoke(prompt)
        ans_content = ans.content if hasattr(ans, "content") else str(ans)
        print(get_message("cli_answer_label"), "\n", ans_content)
        
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": ans_content})


if __name__ == "__main__":
    main()
