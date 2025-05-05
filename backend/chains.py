from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import (SystemMessagePromptTemplate, 
                                    HumanMessagePromptTemplate,
                                    MessagesPlaceholder,
                                    ChatPromptTemplate)

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.tools import TavilySearchResults

from backend.faiss_people import people_vectorstore
from dotenv import load_dotenv

load_dotenv()

model = "llama3.2:latest"
base_url = "http://localhost:11434"

llm = ChatOllama(base_url=base_url, model=model)

### Parse chain (for resume parsing) ###

parse_prompt = """Extract structured resume data in JSON:
    Name, Contact, Education, Skills, Work Experience.

    Provide the output in JSON format Strictly.
    DON'T include any other information.
    
    Resume:
    {resume}
    """

parse_prompt = ChatPromptTemplate.from_template(parse_prompt)
parse_chain = parse_prompt | llm | JsonOutputParser()

### Conversation chain (for resume Q&A) ###

conversation_system_prompt = SystemMessagePromptTemplate.from_template(
    """You are a helpful assistant reviewing a user's resume.
    This is the parsed resume content:

    {resume}

    Use this information to answer questions or provide advice related to the resume."""
    )

conversation_human_prompt = HumanMessagePromptTemplate.from_template("{input}")

conversation_messages = [conversation_system_prompt, MessagesPlaceholder(variable_name='history'), conversation_human_prompt]
conversation_prompt = ChatPromptTemplate(messages=conversation_messages)
conversation_chain = conversation_prompt | llm | StrOutputParser()

### Summary chain (prepare for recommendation) ###

summary_prompt = """You are a helpful assistant summarizing a user's resume.
    This is the parsed resume content:

    {resume}

    Provide the summary in 2-3 sentences including key education, skills, and experience, """

summary_prompt = ChatPromptTemplate.from_template(summary_prompt)
summary_chain = summary_prompt | llm | StrOutputParser()

### People retriever ###

people_retriever = people_vectorstore.as_retriever(search_kwargs={"k": 3}) # optionally set up threshold

### People recommendation chain ###

people_prompt = """You are a career assistant.
    Use the following searched data from other users to recommend me connections based on shared experience and skills.
    Response should ONLY include people from searched data.

    My Resume Summary:
    {summary}

    Searched data:
    {context}
    """

people_prompt = ChatPromptTemplate.from_template(people_prompt)
people_chain = people_prompt | llm | StrOutputParser()

### Combined people rag chain ###

recommend_people_chain = (
        summary_chain
        | (lambda summary: {"summary": summary, 
                            "context": "\n\n".join([
                                f"User: {doc.metadata.get('user_id', 'Unknown')}\nInformation: {doc.page_content}"
                                for doc in people_retriever.invoke(summary)
                            ])})
        | people_chain
    )

### Judgement chain ###

rout_prompt = """Given the user input question below, judge on using `rag` or `simple` chain.
            If the user is asking about recommending people, output `rag`, 
            else if the user is asking about the latest news regarding hiring, output `agent`,
            otherwise, output `simple`.
            Do not respond with more than one word.

            Question: {input}
            Classification:
        """

rout_prompt = ChatPromptTemplate.from_template(rout_prompt)
rout_chain = rout_prompt | llm | StrOutputParser()

### Search Chain ###

search = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
    )

def flatten_docs(docs):
    return "\n\n".join([f"{doc['url']}\n{doc['content']}" for doc in docs])

search_prompt = """Given the user question and context, generate a well-structured response.

                Question: {input}

                Context: {context}"""
search_prompt = ChatPromptTemplate.from_template(search_prompt)
search_chain = {
    "input": lambda x: x["input"], 
    "context": lambda x: flatten_docs(search.invoke(x["input"]))
    } | search_prompt | llm | StrOutputParser()