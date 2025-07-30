from datetime import datetime
import subprocess
from flask import Flask, flash, get_flashed_messages, make_response, redirect, render_template, request, jsonify, session
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from utils.rag_engine import get_relevant_chunks, get_relevant_history_chunks, update_indexing, extract_text_from_pdf
from utils.chat_utils import generate_chat_id
import json
import bcrypt
import secrets
import os

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

def getChatList(user_id):
    return [doc["_id"] for doc in chats.find({"user_id": user_id}, {"_id":1})]

def createSession(resp, user):
    session_id = secrets.token_urlsafe(32)
    sessions.insert_one({"_id":session_id, "user":user["_id"], "created":datetime.utcnow(), "expires":datetime.utcnow()+datetime.timedelta(days=30)})
    resp.set_cookie("session_id", session_id, httponly=True, secure=True)

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
    print("Query processing")
    try:
        query = request.form.get("query-text")
        chatID = request.form.get("chat-id")
        file = request.files.get("file")

        if not chatID:
            while True:
                chatID = generate_chat_id()
                try:
                    chats.insert_one({
                        "_id" : chatID,
                        "history": ""
                    })
                    break
                except DuplicateKeyError as e:
                    print("Chat exists, trying again...")
                    continue
        
        template = """
        You are a professional legal assistant helping users understand Indian laws, especially those applicable in Goa.
        Be formal, precise, and avoid giving advice beyond the scope of legal explanation.
        
        If you're unsure or the query is ambiguous, clearly state that legal advice should be obtained from a qualified lawyer.

        Use the context provided to frame your response. DO NOT hallucinate facts or cite laws unless they are explicitly present in the context.

        Use '**' to enclose bold text in this form **BOLD TEXT**

        This is the conversation history: {context}

        Question: {question}

        Answer: 
        """

        if file:
            contents = file.read()
            pdf_text = extract_text_from_pdf(contents)
            context_chunks = get_relevant_chunks(query, pdf_text)
        else:
            context_chunks = get_relevant_chunks(query)
        
        model = OllamaLLM(model="llama3")

        prompt = ChatPromptTemplate.from_template(template)
        
        chain = prompt | model
        
        context = load_context(chatID)
        context += "\n/////\n" + "\nBACKEND STORED CONTEXT\n" + "\n--\n".join(context_chunks)
        
        result = chain.invoke({"context":context, "question":query})
                
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
    return render_template("manage-chats.html", chatList = getChatList())

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
        
        pswd = bcrypt.hashpw(pswd, bcrypt.gensalt())
        
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
        else:
            flash("Email already registered")
            resp = make_response(redirect("/sign-up"))
        
    except Exception as e:
        flash("User not found. Invalid email")
        resp = make_response(redirect("/login"))
            
@app.route('/login-acc', methods=["POST"])
def login():
    try:
        email = request.form.get("email")
        pswd = request.form.get("password")
        pswd = bcrypt.hashpw(pswd, bcrypt.gensalt())
        
        user = users.find_one({"email":email})
        user_pswd = user["pswd"]
        
        if(bcrypt.checkpw(pswd, user_pswd)):
            resp = make_response(redirect("/"))
            createSession(resp)
        else:
            flash("Email/password mismatch!")
            resp = make_response(redirect("/login"))
    except Exception as e:
        if e.type == "TypeError":
            flash("User not found. Invalid email")
            resp = make_response(redirect("/login"))


# Landing / existing chat
@app.route('/')
@app.route('/<chatID>')
def index(chatID=""):

    session_id = request.cookies.get("session_id")
    session = sessions.find_one({"_id":session_id})
    if session:
        user_id = session["user_id"]
    else:
        user_id = ""

    if not chatID:
        return render_template('index.html', chatList = getChatList(user_id))
    
    chat = chats.find_one({"_id":chatID})
    if not chat:
        return "Chat not found"
    history = chat["history"]
    userHistory = []
    aiHistory = []
    for exchange in history.split("User: "):
        if exchange.strip() != "":
            userHistory.append(exchange.split("AI: ")[0])
            aiHistory.append(exchange.split("AI: ")[1])
        
    zipped = zip(userHistory, aiHistory)
    return render_template('index.html', pairs = zipped, chatList = getChatList(user_id))

if __name__ == "__main__":
    app.run(debug=True)