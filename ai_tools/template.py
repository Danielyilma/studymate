prompt = """
                  Please provide an expanded summary of the following text, ensuring that 
                  all key points, details, and significant aspects are included for a thorough understanding.
                  TEXT: {text}
                  SUMMARY:
                  """
refine_prompt_template = """
            Write a concise summary of the following text delimited by triple backquotes.
            Return your response in bullet points which covers the key points of the text.
            ```{text}```
            BULLET POINT SUMMARY:
            """

mcq_prompt_template = """
    Based on the following text, generate 15 multiple-choice questions (MCQs) along with the correct answers. 
    The questions should cover key concepts from the text and be in the following format:

    Please respond this JSON format and starting with `[`. Do not include any labels, titles, or prefixes 
    (e.g., 'json'). Only provide the JSON response.. The JSON response should look like this:

    [
        
        "questionText": "[The question text]",
        "answers": [
            "text": "[Option 1 text]", "isCorrect": true/false,
            "text": "[Option 2 text]", "isCorrect": true/false,
            "text": "[Option 3 text]", "isCorrect": true/false,
            "text": "[Option 4 text]", "isCorrect": true/false
        ]
        ,
    ]

    TEXT: {text}
    JSON_RESPONSE:
    """

study_card_prompt_template = """
    Based on the following text, generate 15 study cards. 
    Each study card should contain a concise question and a detailed answer summarizing key concepts from the text.
    
    Please respond in this JSON format and starting with `[`. Do not include any labels, titles, or prefixes 
    (e.g., 'json'). Only provide the JSON response. The JSON response should look like this:

    [
        
            "question": "[The question text]",
            "answer": "[The answer text]"
        ,
        
            "question": "[The next question text]",
            "answer": "[The next answer text]"
        
    ]

    TEXT: {text}
    JSON_RESPONSE:
    """

chat_template = """
    You are an AI assistant designed to help university students understand the content of the document they uploaded.
    Use the provided chat history and the document context to give clear, concise, and informative answers.

    After answering, encourage the student to ask any follow-up questions related to the conversation to help them better understand the material.

    Chat History:
    {chat_history}

    Document Content:
    {context}

    Question:
    {question}

    Answer:"""
