# app/main.py
import warnings
from fastapi import FastAPI
from app.routers import user_router
from app.routers import chat_router
from app.database.config import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from app.utils.services import initialize_app_state


#-----------------------------------------------------------------------------------------------------------#
#                                                                                                           #
#                                                                                                           #
#                                                                                                           #
#                                                                                                           #
#-----------------------------------------------------------------------------------------------------------#


# Surpress all warnings
warnings.filterwarnings('ignore')

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Chatbot API",
    description="API for managing users and chats in the chatbot application.",
    version="1.0.0",
)

# CORS settings (adjust origins as needed)
origins = [
    "http://localhost",
    #"http://localhost:4200",
    #"http://localhost:59976",
    # Add other origins as necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Origins that are allowed to communicate with the API
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

## Initialize services on startup
@app.on_event("startup")
async def startup_event():
    initialize_app_state(app)
# Include routers
app.include_router(user_router.router)
app.include_router(chat_router.router)
