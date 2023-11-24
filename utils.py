from pydantic import BaseModel, Field
from typing import Tuple

from langchain import LLMChain
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.output_parsers import PydanticOutputParser
from langchain.agents import load_tools
from langchain.llms import OpenAI, Cohere, GPT4All, CTransformers
from langchain.chains import APIChain, RetrievalQA
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools.base import BaseTool
from langchain.utilities.graphql import GraphQLAPIWrapper
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.pydantic_v1 import BaseModel, Field
from langchain.chains.openai_functions import create_qa_with_structure_chain  # Importing the create_qa_with_structure_chain function from langchain.chains.openai_functions
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate  # Importing the ChatPromptTemplate and HumanMessagePromptTemplate classes from langchain.prompts.chat
from langchain.schema import SystemMessage, HumanMessage  # Importing the SystemMessage and HumanMessage classes from langchain.schema
from langchain.chains.combine_documents.stuff import StuffDocumentsChain  # Importing the StuffDocumentsChain class from langchain.chains.combine_documents.stuff


from IPython.display import display, update_display, HTML, Javascript, clear_output
import os
import json
import requests
import textwrap
import sqlite3
from typing import Any
from typing import Optional

def pretty_print(text: str, indent: str = ' ' * 4) -> None:
    """
    Pretty prints a string with actual line breaks.
    
    Args:
        text (str): The string to pretty print.
        indent (str): The indentation to add to each line break (default: '    ').
    """
    text = text.replace('\n', '\n' + textwrap.indent('', indent))
    print(text)

def convert_to_json(data):
    # Check if data is a string
    if isinstance(data, str):
        # Attempt to parse JSON from the string
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            # Handle JSON decode error
            print("Error: invalid JSON")
    return data

def run_and_display_agent_response(agent_img, agent_chain, input_str, flip=False):
    try:
        response = agent_chain.run(input=input_str)
    except OutputParserException as e:
        # Extract the response from the exception message
        response = str(e).split(": ")[-1].strip("`")
    display_agent_response(agent_img, response, flip)

def display_agent_response(agent_img, output_str, flip=False):

    css_flip = 'transform: scaleX(-1);' if flip else ''

    display(HTML(f"""
    <table style='width: 100%;'><tr>
    <td style='width: 100px; vertical-align: top;'><img style='{css_flip}border-radius: 15px;' src="./media/{agent_img}_head.png"></td>
    <td style='width: auto'></pre>
    </div>
    </td>
    </tr></table>
    <table style='width: 100%;'><tr>
    <td style='width: auto; vertical-align: middle;'><div style='width: auto; height: auto; background-color: black; border: 1px solid; border-radius: 15px; padding: 5px;'>
        <pre style='text-align: left; color: green; font-size: 1.2em;padding-top: -10px; font-weight: bold; font-family: Terminal, monospace;'>{output_str}</pre>
    </div>
    </td>
    </tr></table>
    """))

def get_agent_chain(llm, prefix, tools):
    suffix = """Begin!"
{chat_history}
Question: {input}
{agent_scratchpad}"""
  
    prompt = ZeroShotAgent.create_prompt(
        tools,
        prefix=prefix + """

These are the tools you have access to:""",
        suffix=suffix,
        input_variables=["input", "chat_history", "agent_scratchpad"],
    )

    memory = ConversationBufferMemory(memory_key="chat_history")

    llm_chain = LLMChain(llm=llm, prompt=prompt)

    agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)

    return AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, verbose=True, memory=memory,
        max_iterations=5, early_stopping_method="generate", handle_parsing_errors=True,
    )

def create_human_message_for_gpt4vision(instructions, *image_urls):
    return HumanMessage(
        content = [
            {'type': 'text', 'text': instructions},
            * [{'type': 'image_url', 'image_url': {'url': image_url, 'detail': 'auto'}} for image_url in image_urls],
        ]
    )

def display_html_for_streaming(agent_img, display_id):
    display(HTML(f"""
    <table style='width: 100%;'><tr>
    <td style='width: 100px; vertical-align: top;'><img style"border-radius: 15px;" src="./media/{agent_img}_head.png"></td>
    <td style='width: auto; vertical-align: middle;'><div style='width: auto; height: auto; background-color: black; border: 1px solid; border-radius: 15px; padding: 5px;'>
        <p id="{display_id}" style='text-align: left; color: green; font-size: 1.2em;padding-top: -10px; font-weight: bold; font-family: Terminal, monospace;'></p>
    </div>
    </td>
    </tr></table>
    """), display_id=display_id)

def stream_chat_content(chat, msg, display_id):
    for chunk in chat.stream([msg]):
        current_content = chunk.content

        js_code = f"""
        var current_html = document.getElementById('{display_id}').innerHTML;
        var new_html = current_html + '{current_content}';
        document.getElementById('{display_id}').innerHTML = new_html;
        """
        display(Javascript(js_code))
        clear_output(wait=True)

docsearch = None
def get_retrieval_qa_pydantic_from_document(llm, system_prompt, file, schema):
    loader = TextLoader(f"./{file}", encoding="utf-8")  # Creating a TextLoader object with the path to the text file and its encoding
    documents = loader.load()  # Loading the documents from the text file
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)  # Creating a CharacterTextSplitter object with a chunk size of 1000 and no overlap
    texts = text_splitter.split_documents(documents)  # Splitting the documents into chunks
    embeddings = OpenAIEmbeddings()  # Creating an OpenAIEmbeddings object
    global docsearch
    if docsearch is not None:
        docsearch.delete_collection()

    docsearch = Chroma.from_documents(texts, embeddings)  # Creating a Chroma object from the chunks and their embeddings, and purging the database first
    # 📃 prompt template
    doc_prompt = PromptTemplate(  # Creating a PromptTemplate object
        template="Content: {page_content}\nSource: {source}",  # The template for the prompt
        input_variables=["page_content", "source"],  # The input variables for the prompt
    )

    prompt_messages = [  # The messages for the prompt
        SystemMessage(
            content=(
                system_prompt
            )
        ),
        HumanMessage(content="Answer question using the following context"),
        HumanMessagePromptTemplate.from_template("{context}"),
        HumanMessagePromptTemplate.from_template("Question: {question}"),
        HumanMessage(
            content="Tips: Make sure to answer in the correct format. Return all of the countries mentioned in the sources in uppercase characters."
        ),
    ]

    chain_prompt = ChatPromptTemplate(messages=prompt_messages)  # Creating a ChatPromptTemplate object with the prompt messages

    qa_chain_pydantic = create_qa_with_structure_chain(  # Creating a QA chain with a structure
        llm, schema, output_parser="pydantic", prompt=chain_prompt
    )
    final_qa_chain_pydantic = StuffDocumentsChain(  # Creating a final QA chain
        llm_chain=qa_chain_pydantic,
        document_variable_name="context",
        document_prompt=doc_prompt,
    )
    retrieval_qa_pydantic = RetrievalQA(  # Creating a RetrievalQA object
        retriever=docsearch.as_retriever(), combine_documents_chain=final_qa_chain_pydantic
    )

    return retrieval_qa_pydantic
