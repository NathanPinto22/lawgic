from datetime import datetime, timedelta
import subprocess
from flask import Flask, flash, get_flashed_messages, make_response, redirect, render_template, request, jsonify, session, url_for
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import requests
from utils.rag_engine import get_relevant_chunks, get_relevant_history_chunks, update_indexing, extract_text_from_pdf
from utils.chat_utils import generate_chat_id
import json
import bcrypt
import secrets
import os
import time
from transformers import pipeline
# Primary query processing pipeling
try:
    flan_legal = pipeline(
        "text2text-generation",
        model="nlearn/flan-legal-qa",
        tokenizer="nlearn/flan-legal-qa",
        max_new_tokens=200
    )
    print("QA model loaded.")
except Exception as e:
    print("Failed to load model:", e)
    flan_legal = None

# Query optimizer processing pipeling
try:
    query_optimizer = pipeline("text2text-generation", model="google/flan-t5-base")
except Exception as e:
    print("Failed to load model:", e)
    query_optimizer = None

# History compressor processing pipeling
try:
    compressor = pipeline("text2text-generation", model="google/flan-t5-base")
except Exception as e:
    print("Failed to load model:", e)
    query_optimizer = None


# try:
#     from openai import OpenAI
#     client = OpenAI(api_key="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")
#     use_openai = True
# except Exception:
#     use_openai = False
    
# hardcoded false coz im poor :')
# use_openai = False

# from transformers import pipeline
# local_llm = pipeline("text-generation", model="gpt2")

app = Flask(__name__)
app.secret_key = "sdfkasc54acaAsCAsc1Amsqpemqpcdk"
client = MongoClient("mongodb://localhost:27017")
db = client["lawgic"]
chats = db["chats"]
users = db["users"]
users.create_index("email", unique=True)
sessions = db["sessions"]   


def optimize_query(user_query):
    prompt = f"Shorten this query while maintaining the key words such as the action to be performed and the topic:\n\n{user_query}"
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "phi", "prompt": prompt, "stream": False}
    )

    if response.ok:
        return response.json()['response'].strip().title()
    else:
        return user_query
    
    

def summarize_context(context, llama3=None):
    
    print(context)
    if not llama3:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer(context, max_length=300, min_length=30, do_sample=False)
        print(summary)
        if summary:
            return summary
        else:
            return context
    else:
        template = """
        Summarize the following legal text in a clean systematic format.
        Ensure all critical information is retained
        Text: {text}
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        chain = prompt | llama3
        result = chain.invoke({"text":context})
        print(result.strip())
        if result.strip():
            return result.strip()
        else:
            return context

def generate_chat_title(user_query):
    prompt = f"Give a short title (3 to 7 words) summarizing this message:\n\n{user_query}"
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "phi", "prompt": prompt, "stream": False}
    )

    if response.ok:
        return response.json()['response'].strip().title()
    else:
        return "Untitled Chat"
   
def getChatList(user_id):
    return [(doc["_id"], doc["title"]) for doc in chats.find({"user_id": user_id}, {"_id":1, "title":1})]

def getUserFromSessionId(session_id):
    s = sessions.find_one({"_id":session_id})
    if s:
        print("session found")  
        return s["user"]
    else:
        print("session not found")
        return None

def createSession(resp, user):
    print("P2")
    session_id = secrets.token_urlsafe(32)
    print("P3")
    sessions.insert_one({"_id":session_id, "user":user["_id"], "created":datetime.utcnow(), "expires":datetime.utcnow() + timedelta(days=30)})
    print("P4")
    resp.set_cookie("session_id", session_id, httponly=True, secure=True)
    
def discardSession(session):
    try:
        sessions.delete_one({"_id":session["_id"]})
    except Exception as e:
        print("Error deleting a session: ", e)

def remote_llama3_infer(prompt):
    try:
        res = requests.post("https://<your-ngrok-or-api-url>/generate", json={"prompt": prompt})
        return res.json().get("response", "").strip()
    except Exception as e:
        print("Error calling remote model:", e)
        return "Error generating response."
        
CONTEXT_FILE = "context_history.json"

def html_format(text):
    formatted_text = ""
    bracketOpen = False
    for line in text.splitlines():
        if line == "":
            formatted_text += "<br><br>"
        else:
            for i in range(len(line)-1):
                if line[i]+line[i+1] == "**":
                    if bracketOpen:
                        formatted_text+="</b>"
                        bracketOpen = False
                    else:
                        formatted_text+="<b>"
                        bracketOpen = True
                else:
                    formatted_text+=line[i]
                if i+1 == len(line)-1 and not formatted_text[-4:0:] == "<br>":
                    formatted_text += "<br>"
    return formatted_text
                
        

def load_context(chatID):
    chat = chats.find_one({"_id" : chatID})
    try:
        return chat["history"]
    except Exception as e:
        print('chat["history"]: ', e)
        return ""

def save_context(chatID, query, result):
    chat = chats.find_one({"_id" : chatID})
    history = chat["history"]
    update = "\nUser: " + query + "\nAI: " + result
    history += update
    result = chats.update_one(
        {"_id" : chatID},
        {"$set" : { "history" : history }}
    )    
    return result.modified_count > 0


# Chat query processing
@app.route("/chat", methods=["POST"])
async def chatProcessing():
    chatID = None
    print("Query processing")
    try:
        session_id = request.cookies.get("session_id")
        query = request.form.get("query-text")
        chatID = request.form.get("chat-id")
        file = request.files.get("file")
        user_id = getUserFromSessionId(session_id)
        if not chatID:
            chat_title = generate_chat_title(query)
            while True:
                chatID = generate_chat_id()
                try:
                    chats.insert_one({
                        "_id" : chatID,
                        "user_id":user_id,
                        "title":chat_title,
                        "history": ""
                    })
                    break
                except DuplicateKeyError as e:
                    print("Chat exists, trying again...")
                    continue
        
        template = """
        You are a professional legal assistant helping users understand Indian laws, especially those applicable in Goa. Be formal, precise, and avoid giving advice beyond the scope of legal explanation. If you're unsure or the query is ambiguous, clearly state that legal advice should be obtained from a qualified lawyer. Use the context provided to frame your response. DO NOT hallucinate facts or cite laws unless they are explicitly present in the context.
        This is the conversation history: {context}
        
        Question: {question}

        Answer: 
        """

        optimized_query = optimize_query(query)
        print("Query: ", optimized_query)
        
        if file:
            contents = file.read()
            pdf_text = extract_text_from_pdf(contents)
            context_chunks = get_relevant_chunks(query, pdf_text)
        else:
            context_chunks = get_relevant_chunks(query)
        print(context_chunks)
        
        # Ollama llama3 model object
        llama3 = OllamaLLM(model="llama3")
        
        
        
        history = load_context(chatID)
        faiss_context = "\n--\n".join(context_chunks)
        
        # llama3 summarization
        print("Summarizing history...")
        context = summarize_context(history, llama3)
        print("Summarizing context...")
        context += "\n/////\n" + summarize_context(faiss_context, llama3)
        
        prompt = f"Summarize this legal conversation, keeping chronological order and main facts:\n\n{history}"
        context = summarize_context(history)
        
        faiss_context = summarize_context(faiss_context)
        context += "\n/////\n" + faiss_context
        
        # llama3(local) method
        # llama3_query = ChatPromptTemplate.from_template(template)
        # chain = llama3_query | llama3
        # result = chain.invoke({"context":context, "question":query})

        # llama3(remote) method
        final_prompt = template.format(context=context, question=query)
        result = remote_llama3_infer(final_prompt)


        # fine-tuned flan-t5-small method
        # prompt = template.format(context=context, question=optimized_query)
        # print(prompt)
        # result = flan_legal(prompt)[0]["generated_text"]
                
        result = html_format(result)
        
        if save_context(chatID, query, result):
            print("Chat history updated for chat", chatID)
        else:
            print("Failed to update chat history for chat", chatID)
        
        
        
        return json.dumps({"chatID":chatID, "reply":result})
    
    except Exception as e:
        print("exception caught")
        print(e)
        return json.dumps({"chatID":chatID, "reply":"There was an error processing your request!"})
    

@app.route('/manage-chats')

def manage_chats_page():
    session_id = request.cookies.get("session_id")
    return render_template("manage-chats.html", chatList = getChatList(getUserFromSessionId(session_id)))

@app.route('/sign-up')
def signup_page():
    msg = get_flashed_messages()
    return render_template("sign-up.html", message = msg)

@app.route('/login')
def login_page():
    msg = get_flashed_messages()
    return render_template("login.html", message = msg)

@app.route("/sign-up-acc", methods=["POST"])
def signup():
    try:
        email = request.form.get("email")
        pswd = request.form.get("password")
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        phno = request.form.get("phone")
        
        pswd = bcrypt.hashpw(pswd.encode('utf-8'), bcrypt.gensalt())
        
        user = users.find_one({"email":email})
        
        if not users.find_one({"email":email}):
            user_id = users.insert_one({
                "email":email,
                "pswd":pswd,
                "fname":fname,
                "lname":lname,
                "phno":phno
            }).inserted_id
            
            user = users.find_one({"_id":user_id})
            resp = make_response(redirect("/"))
            createSession(resp, user)
            return resp
        else:
            flash("Email already registered")
            resp = make_response(redirect("/sign-up"))
            return resp
        
    except Exception as e:
        print("Error:", e)
        resp = make_response(redirect("/sign-up"))
        return resp
            
@app.route('/login-acc', methods=["POST"])
def login():
    try:
        email = request.form.get("email")
        pswd = request.form.get("password")
        pswd = pswd.encode('utf-8')
        
        user = users.find_one({"email":email})
        user_pswd = user["pswd"]
        print(bcrypt.checkpw(pswd, user_pswd))
        if(bcrypt.checkpw(pswd, user_pswd)):
            print("User authenticated")
            resp = make_response(redirect("/"))
            print("P1")
            createSession(resp, user)
            return resp
        else:
            print("Email/password mismatch!")
            flash("Email/password mismatch!")
            resp = make_response(redirect("/login"))
            return resp
    except Exception as e:
        print("User not found. Invalid email")
        flash("User not found. Invalid email")
        print("Error", e)
        resp = make_response(redirect("/login"))
        return resp

@app.route('/session-valid', methods=["POST"])
def session_valid():
    print("checking session validity")
    session_id = request.cookies.get("session_id")
    print(request.cookies)

    if not session_id:
        return json.dumps({"valid": False, "reason": "Missing session_id"}), 401

    session = sessions.find_one({"_id": session_id})

    if not session:
        return json.dumps({"valid": False, "reason": "Session not found"}), 401

    if session["expires"] < datetime.utcnow():
        discardSession(session)
        return json.dumps({"valid": False, "reason": "Session expired"}), 401
    print("session found")
    return json.dumps({"valid": True, "user": str(session["user"])}), 200

# @app.route('/sign-out')
# def sign_out():
#     session_id = request.cookies.get("session_id")
#     sessions.delete_one({"_id":session_id})
#     return make_response(redirect('/index'))

@app.route('/delete-chat/<chatID>')
def deleteChat(chatID):
    session_id = request.cookies.get("session_id")
    result = chats.delete_one({"_id":chatID})
    return redirect(url_for("manage-chats"))

@app.route('/sign-out')
def sign_out():
    session_id = request.cookies.get("session_id")
    sessions.delete_one({"_id":session_id})
    return redirect(url_for('index'))

# Landing / existing chat
@app.route('/')
@app.route('/<chatID>')
def index(chatID=""):

    session_id = request.cookies.get("session_id")

    if not chatID:
        return render_template('index.html', chatList = getChatList(getUserFromSessionId(session_id)))
    
    chat = chats.find_one({"_id":chatID})
    if not chat:
        return "Chat not found"
    chat_title = chat["title"]
    history = chat["history"]
    userHistory = []
    aiHistory = []
    for exchange in history.split("User: "):
        if exchange.strip() != "":
            userHistory.append(exchange.split("AI: ")[0])
            aiHistory.append(exchange.split("AI: ")[1])
        
    zipped = zip(userHistory, aiHistory)
    return render_template('index.html', pairs = zipped, chatList = getChatList(getUserFromSessionId(session_id)), chat_title=chat_title)

if __name__ == "__main__":
    app.run(debug=True)