from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google import genai
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# SQLite
engine = create_engine('sqlite:///rag_database.db', connect_args={"check_same_thread": False})
Base = declarative_base()

class ChatLog(Base):
    __tablename__ = 'chat_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String)
    message = Column(String)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup Gemini's genai client with API key
client = genai.Client(api_key="YOUR_API_KEY_TO_BE_PUT_HERE") 

# Faiss setup
print("Loading Embedding Model... (This takes a few seconds on boot)")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

knowledge_base = [
    "The developer is a pre-final year Electrical Engineering undergraduate at IIT Bhubaneswar, graduating in 2028.",
    "The developer focuses on electrical engineering concepts, microprocessors, network theory, and advanced mathematical transforms.",
    "The developer maintains an active profile on Codeforces under the handle PLASMICBOLT for competitive programming.",
    "The developer is a member of the Robotics and Integrated Systems Club (RISC) and was on the organizing team for the Robo Race at Pravaah 2025.",
    "Outside of engineering, the developer participates in basketball, dance practice, and explores virtual machine environments like Ubuntu."
]

# Converting text to embeddings and loading them into FAISS
print("Indexing Knowledge Base into FAISS...")
embeddings = embedder.encode(knowledge_base)
dimension = embeddings.shape[1]
vector_index = faiss.IndexFlatL2(dimension)
vector_index.add(embeddings)

# tunnel setup
app = FastAPI()

html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise RAG Engine</title>
    <style>
        body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #343541; color: #ececf1; display: flex; flex-direction: column; height: 100vh; }
        .header { background-color: #202123; padding: 15px 20px; text-align: center; border-bottom: 1px solid #4d4d4f; font-weight: 600; letter-spacing: 1px; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .message { padding: 15px; border-radius: 8px; max-width: 80%; line-height: 1.5; }
        .user-message { background-color: #444654; align-self: flex-end; border-bottom-right-radius: 0; }
        .ai-message { background-color: #10a37f; align-self: flex-start; border-bottom-left-radius: 0; color: white; }
        .input-container { padding: 20px; background-color: #343541; border-top: 1px solid #4d4d4f; display: flex; justify-content: center; }
        form { display: flex; width: 100%; max-width: 800px; background-color: #40414f; border-radius: 8px; padding: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
        input { flex: 1; background: transparent; border: none; padding: 12px 15px; color: white; font-size: 16px; outline: none; }
        button { background-color: #10a37f; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: background 0.2s; }
        button:hover { background-color: #0b8c6a; }
    </style>
</head>
<body>
    <div class="header">SYSTEM ARCHITECTURE RAG</div>
    <div class="chat-container" id="messages"></div>
    <div class="input-container">
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off" placeholder="Ask the database..." required/>
            <button type="submit">Send</button>
        </form>
    </div>
    <script>
        var ws = new WebSocket("ws://localhost:8000/ws");
        const messagesDiv = document.getElementById('messages');

        ws.onmessage = function(event) {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message ai-message';
            msgDiv.innerHTML = "<b>System:</b><br>" + event.data;
            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        };

        function sendMessage(event) {
            event.preventDefault();
            const input = document.getElementById("messageText");
            const text = input.value.trim();
            if(!text) return;

            const msgDiv = document.createElement('div');
            msgDiv.className = 'message user-message';
            msgDiv.textContent = text;
            messagesDiv.appendChild(msgDiv);
            
            ws.send(text);
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            user_question = await websocket.receive_text()
            db.add(ChatLog(sender="User", message=user_question))
            db.commit()

            # RAG Logic
            # Convert the user's question into an embedding
            question_vector = embedder.encode([user_question])
            
            # k=1 for best match
            distances, indices = vector_index.search(question_vector, k=1)
            best_match_index = indices[0][0]
            retrieved_context = knowledge_base[best_match_index]

            # Build the highly-restricted prompt
            prompt = f"""
            You are a system assistant. Answer the user's question using ONLY the context below.
            If the answer is not in the context, say "I don't know."
            
            Context: {retrieved_context}
            
            Question: {user_question}
            """

            # generate response
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            ai_answer = response.text

            # Log and Stream back
            db.add(ChatLog(sender="AI", message=ai_answer))
            db.commit()
            await websocket.send_text(ai_answer)

    except WebSocketDisconnect:
        print("Client disconnected.")
    finally:
        db.close()