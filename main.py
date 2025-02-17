# app/main.py
import warnings, logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi_proxiedheadersmiddleware import ProxiedHeadersMiddleware
from app.routers import user_router
from app.routers import chat_router
from app.database.config import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.utils.services import initialize_app_state, start_file_watcher
from contextlib import asynccontextmanager


#-----------------------------------------------------------------------------------------------------------#
#                                                                                                           #
#                                                                                                           #
#                                                                                                           #
#                                                                                                           #
#-----------------------------------------------------------------------------------------------------------#

# Set global logging level to INFO (or any desired level)
logging.basicConfig(level=logging.INFO)
# Suppress specific module logs
logging.getLogger("faiss.loader").setLevel(logging.WARNING)  # Suppress faiss logs
logging.getLogger("httpx").setLevel(logging.WARNING)         # Suppress httpx logs

# Surpress all warnings
warnings.filterwarnings('ignore')
#Base.metadata.drop_all(bind=engine)
# Create all database tables
from app.models.models import User, ChatHistory, pgDocument  # should always be imported if u want to create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    #start_file_watcher(app)
    print("running: ")
    initialize_app_state(app)
    yield
    # Add shutdown logic here if needed
    #cleanup_app_state(app)


app = FastAPI(
    title="Chatbot API",
    description="API for managing users and chats in the chatbot application.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS settings (adjust origins as needed)
origins = [
    #"http://localhost:4200", # Local development
    "https://bnkichat.steep.loc" # Production server

]
# Trusted hosts for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        #"http://localhost:4200", 
        "bnkichat.steep.loc", 
        "*.steep.loc",
        "127.0.0.1", 
        ]
)
# Middleware to handle proxies and X-Forwarded headers
app.add_middleware(ProxiedHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Origins that are allowed to communicate with the API
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Include routers
app.include_router(user_router.router)
app.include_router(chat_router.router)

# websocket endpoint for real-time chat
@app.websocket("ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            response = f"Session {session_id}: {data}"
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")


# Middleware to handle X-Forwarded-* headers (if needed)
@app.middleware("http")
async def handle_proxy_headers(request: Request, call_next):
    # Update request with proxy information if X-Forwarded headers exist
    forwarded_host = request.headers.get("x-forwarded-host")
    forwarded_proto = request.headers.get("x-forwarded-proto")

    if forwarded_host:
        request.scope["server"] = (forwarded_host, request.url.port)
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto

    return await call_next(request)


# Root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Welcome to Chatbot API"}

