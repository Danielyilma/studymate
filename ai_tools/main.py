from langchain.docstore.document import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from ai_tools.mixins import BaseClient
from ai_tools.template import (
    prompt, refine_prompt_template,
    mcq_prompt_template, study_card_prompt_template
)

class AI(BaseClient):
    tasks = {
        "summerize",
        "mutiple-choice",
        "study-card"
    }

    def __init__(self):
        super().__init__()
        self.session_vector_stores = {}
        self.user_memories = {}

    def run(self, path, task="summerize"):
        '''
        path:
            path to the file to be used
        
        task:
            the task to be performed
            options -   
                        "summerize", default
                        "mutiple-choice",
                        "study-card"
        '''

        text = self.extract(path)
        t = "".join([tex.page_content for tex in text])
        docs = [Document(page_content=t)]
        result = None
        
        if task == "study-card":
            result = self.generate_study_card(docs, self.llm)
            result = self.parse_json_like_content(result)
        elif task == "mutiple-choice":
            result = self.generate_mcq_from_text(docs, self.llm)
            result = self.parse_json_like_content(result)
        else:
            result = self.summerize_text(docs, self.llm)

        return result

    def summerize_text(self, split_docs, llm):
        question_prompt = PromptTemplate(
            template=prompt, input_variables=["text"]
        )

        refine_prompt = PromptTemplate(
            template=refine_prompt_template, input_variables=["text"]
            )

        chain = load_summarize_chain(
            llm=llm,
            chain_type="refine",
            question_prompt=question_prompt,
            refine_prompt=refine_prompt,
            return_intermediate_steps=True,
            input_key="input_documents",
            output_key="output_text",
        )
        result = chain({"input_documents": split_docs}, return_only_outputs=True)
        return result["output_text"]
    
    def generate_mcq_from_text(self, split_docs, llm):
        mcq_prompt = PromptTemplate(
            template=mcq_prompt_template, input_variables=["text"]
        )

        chain = LLMChain(prompt=mcq_prompt, llm=llm)

        result = chain.run({"text": split_docs})

        return str(result)

    def generate_study_card(self, split_docs, llm):
        study_card_prompt = PromptTemplate(
            template=study_card_prompt_template, input_variables=["text"]
        )

        chain = LLMChain(prompt=study_card_prompt, llm=llm)

        result = chain.run({"text": split_docs})

        return str(result)
    





































# def extract(file_path):
#     loader = PyPDFLoader(file_path)
#     documents = loader.load()
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=600, chunk_overlap=200
#     )
#     texts = text_splitter.split_documents(documents)
#     return texts

# def store_embeddings(docs, embeddings, sotre_name, path):
#     vectorStore = FAISS.from_documents(docs, embeddings)

#     with open(f"{path}/faiss_{sotre_name}.pkl", "wb") as f:
#         pickle.dump(vectorStore, f)

# def load_embeddings(sotre_name, path):

#     with open(f"{path}/faiss_{sotre_name}.pkl", "rb") as f:
#         vectorStore = pickle.load()
    
#     return vectorStore

# def summerize_text(split_docs, llm):
#     question_prompt = PromptTemplate(
#         template=prompt, input_variables=["text"]
#     )

#     refine_prompt = PromptTemplate(
#         template=refine_prompt_template, input_variables=["text"]
#         )

#     chain = load_summarize_chain(
#         llm=llm,
#         chain_type="refine",
#         question_prompt=question_prompt,
#         refine_prompt=refine_prompt,
#         return_intermediate_steps=True,
#         input_key="input_documents",
#         output_key="output_text",
#     )
#     result = chain({"input_documents": split_docs}, return_only_outputs=True)
#     return result["output_text"]


# def generate_mcq_from_text(split_docs, llm):
#     mcq_prompt = PromptTemplate(
#         template=mcq_prompt_template, input_variables=["text"]
#     )

#     chain = LLMChain(prompt=mcq_prompt, llm=llm)

#     result = chain.run({"text": split_docs})

#     return str(result)[7:-3]

# def generate_study_card(split_docs, llm):
#     study_card_prompt = PromptTemplate(
#         template=study_card_prompt_template, input_variables=["text"]
#     )

#     chain = LLMChain(prompt=study_card_prompt, llm=llm)

#     result = chain.run({"text": split_docs})

#     return str(result)

# load_dotenv()
# api_key = os.environ.get('GEMNI_API_KEY')
# llm = GoogleGenerativeAI(model='gemini-1.5-pro-latest', google_api_key=api_key, verbose=True)

# text = extract("uploads/2_Chapter_2.pdf")
# t = "".join([tex.page_content for tex in text])
# docs = [Document(page_content=t)]


# print("\n\n\n\n")
# print(json.loads(generate_study_card(docs, llm)))

# print(summerize_text("uploads/2_Chapter_2.pdf"))