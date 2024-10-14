import json
import logging
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

import requests
import pickle
import base64

from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_openai.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Yellowbrick

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

OPEN_API_KEY=os.environ.get("OPEN_API_KEY")
YB_CONNECTION_STRING = os.environ.get("YB_CONNECTION_STRING")
SLACK_API_KEY = os.environ.get("SLACK_API_KEY")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

SYSTEM_TEMPLATE = """Use the following pieces of context to answer the users question.  Assume the questions are about the Yellowbrick Datawarehouse.
    If you don't know the answer, preface the answer with "I believe" or "I think" to indicate uncertainty.  
    If the question requires you to answer in code (like SQL) be very precise with your answers and do not guess.
    ----------------
    {summaries}"""


embedding_table = "doc_vectors"

def post_message(channel_id, text, thread_ts=None):

    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "channel": channel_id,
        "text": text,
    }

    if thread_ts:
        payload["thread_ts"] = thread_ts

    response = requests.post(url, headers=headers, json=payload)
    return response


def post_to_slack(Question, Answer):

    initial_response = post_message(SLACK_CHANNEL_ID, Question)
    if initial_response.status_code == 200 and initial_response.json()["ok"]:
        thread_ts = initial_response.json()["message"]["ts"]
        reply_response = post_message(SLACK_CHANNEL_ID, Answer, thread_ts)
        if reply_response.status_code == 200 and reply_response.json()["ok"]:
            return


def queryGPT(qString, previousText, nologging=False):
    if previousText == "":
        prevMessages = ChatMessageHistory()
    else:
        prevMessages = pickle.loads(base64.b64decode(previousText))
    messages = [SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE)] + \
               prevMessages.messages + \
               [HumanMessagePromptTemplate.from_template("{question}")]

    prompt = ChatPromptTemplate.from_messages(messages)

    vector_store = Yellowbrick(OpenAIEmbeddings(openai_api_key=OPEN_API_KEY),
                               YB_CONNECTION_STRING,
                               embedding_table
                               )

    chain_type_kwargs = {"prompt": prompt}
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.0, max_tokens=1024, openai_api_key=OPEN_API_KEY)
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={'k': 5}),
        return_source_documents=True,
        chain_type_kwargs=chain_type_kwargs
    )

    result = chain.invoke(qString)
    output_text = result['answer']
    if not nologging: post_to_slack(qString, output_text)

    prevMessages.add_user_message(qString)
    prevMessages.add_ai_message(output_text)

    return jsonify(
        {'chatResponse': output_text, 'previousText': base64.b64encode(pickle.dumps(prevMessages)).decode('utf-8')})

logging.basicConfig( level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
app = Flask(__name__)
CORS(app)

@app.route( '/health',methods=['GET'])
def health():
    return "Ok"

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    app.logger.info('request: %s ', data)

    qString = data.get('q')
    previousText = data.get('previousText')
    noLogging = data.get('nologging')
    resp = queryGPT(qString, previousText, noLogging)
    app.logger.info("response: %s ",resp.json)
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
