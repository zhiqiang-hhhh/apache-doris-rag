from conf import settings

MESSAGES = {
    "zh": {
        "source_label": "来源",
        "cli_input_prompt": "请输入您的问题（直接回车退出）：",
        "cli_augmented_query": "优化后的查询: {}",
        "cli_answer_label": "回答:",
        "cli_retrieved_docs": "以下是检索到的 Doris 文档片段：\n\n{}\n\n请根据上述内容回答：{}",
        "augment_prompt_history": (
            "你是一个专业的搜索助手。请根据对话历史，将用户的最新问题重写为一个独立、清晰的搜索查询。\n"
            "如果问题中包含代词（如“它”、“这个”），请根据历史替换为具体的名词。\n"
            "如果问题已经很清晰，则保持原样。\n"
            "只返回重写后的查询，不要有任何解释。\n\n"
            "对话历史：\n{}\n\n"
            "用户问题：{}"
        ),
        "augment_prompt_no_history": (
            "你是一个专业的搜索助手。请优化以下用户问题，使其更适合在 Apache Doris 文档库中进行向量检索。\n"
            "可以补充相关的关键词，但不要改变原意。\n"
            "只返回优化后的查询，不要有任何解释。\n\n"
            "用户问题：{}"
        ),
        "service_original_augmented": "原始问题: {} -> 优化后: {}",
        "chat_prompt_template": (
            "你是一个专业的 Apache Doris 中文文档助手，请根据给定的“检索上下文”来回答用户问题。\n\n"
            "【对话历史】\n{history}\n\n"
            "【检索上下文】\n{context}\n\n"
            "【要求】\n"
            "- 优先使用检索到的内容回答。\n"
            "- 如果文档中没有相关信息，请明确说明“基于当前文档未找到相关说明”，不要胡编。\n"
            "- 回答使用简体中文，尽可能简洁，但在技术细节上要准确。\n\n"
            "【用户问题】\n{question}"
        ),
        "html_lang": "zh-CN",
        "ui_placeholder": "请输入你的问题，比如：Doris 如何配置向量索引？",
        "ui_send": "发送",
        "ui_thinking": "思考中...",
        "ui_error_prefix": "服务错误: ",
        "ui_request_failed": "请求失败，请检查后端服务是否启动。",
        "ui_source_ref": "引用文档: ",
    },
    "en": {
        "source_label": "Source",
        "cli_input_prompt": "Your question (input empty to quit): ",
        "cli_augmented_query": "Augmented Query: {}",
        "cli_answer_label": "Answer:",
        "cli_retrieved_docs": "Here are the retrieved Doris document snippets:\n\n{}\n\nPlease answer based on the above content: {}",
        "augment_prompt_history": (
            "You are a professional search assistant. Please rewrite the user's latest question into an independent, clear search query based on the conversation history.\n"
            "If the question contains pronouns (e.g., 'it', 'this'), please replace them with specific nouns based on the history.\n"
            "If the question is already clear, keep it as is.\n"
            "Return only the rewritten query, without any explanation.\n\n"
            "Conversation History:\n{}\n\n"
            "User Question: {}"
        ),
        "augment_prompt_no_history": (
            "You are a professional search assistant. Please optimize the following user question to make it more suitable for vector retrieval in the Apache Doris documentation.\n"
            "You can add relevant keywords, but do not change the original meaning.\n"
            "Return only the optimized query, without any explanation.\n\n"
            "User Question: {}"
        ),
        "service_original_augmented": "Original: {} -> Augmented: {}",
        "chat_prompt_template": (
            "You are a professional Apache Doris documentation assistant. Please answer the user's question based on the provided 'Retrieved Context'.\n\n"
            "【Conversation History】\n{history}\n\n"
            "【Retrieved Context】\n{context}\n\n"
            "【Requirements】\n"
            "- Prioritize using the retrieved content to answer.\n"
            "- If there is no relevant information in the documents, please explicitly state 'No relevant information found based on current documents', do not make things up.\n"
            "- Answer in English, be concise, but accurate in technical details.\n\n"
            "【User Question】\n{question}"
        ),
        "html_lang": "en",
        "ui_placeholder": "Enter your question, e.g., How to configure vector index in Doris?",
        "ui_send": "Send",
        "ui_thinking": "Thinking...",
        "ui_error_prefix": "Service Error: ",
        "ui_request_failed": "Request failed, please check if the backend service is running.",
        "ui_source_ref": "References: ",
    }
}

def get_message(key, *args):
    lang = settings.app.get('language', 'zh')
    msg = MESSAGES.get(lang, MESSAGES['zh']).get(key, "")
    if args:
        return msg.format(*args)
    return msg
