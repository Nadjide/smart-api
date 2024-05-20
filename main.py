from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import errors
from bson import ObjectId
from models import Admin, Candidat, CandidatResponse, Questionnaire, CandidatAnswer, SavedQuestion
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import bcrypt
from datetime import datetime
from typing import List
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://nadjide:VgSlIjkXOxF1sXia@prod-cluster.cnbxwti.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true")

async def connect_to_mongo():
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.mongodb = app.mongodb_client.SmartHire

def disconnect_from_mongo():
    if app.mongodb_client:
        app.mongodb_client.close()

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", disconnect_from_mongo)

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

@app.get('/')
def read_root():
    return {"message": "Bienvenue sur notre site"}

@app.get('/api')
def principal():
    return {"message": "Bienvenue sur notre api"}

def document_to_dict(document):
    return {**document, "_id": str(document["_id"])}

@app.get("/candidats/")
async def read_candidats():
    candidats = []
    async for candidat in app.mongodb.Candidats.find():
        candidats.append(document_to_dict(candidat))
    return candidats

@app.post("/candidats/")
async def create_candidat(candidat: Candidat):
    existing_user = await app.mongodb.Candidats.find_one({"Email": candidat.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Un candidat avec cet email existe déjà")
    
    candidat_dict = candidat.model_dump()
    result = await app.mongodb.Candidats.insert_one(candidat_dict)
    print(candidat.email)
    return {"_id": str(result.inserted_id), "email": candidat.email}, 200

@app.post("/admin/connexion/")
async def admin_connexion(admin: Admin):
    existing_admin = await app.mongodb["Admin"].find_one({"email": admin.email})
    if not existing_admin or admin.password != existing_admin["password"]:
        raise HTTPException(status_code=400, detail="Identifiants incorrects")
    return {"message": "Connexion réussie", "email": existing_admin["email"]}, 200

@app.post("/questionnaires/")
async def create_questionnaire(questionnaire: Questionnaire):
    existing = await app.mongodb.Questionnaires.find_one({"category": questionnaire.category})
    if existing:
        raise HTTPException(status_code=400, detail="Un questionnaire de cette catégorie existe déjà.")
    
    result = await app.mongodb.Questionnaires.insert_one(questionnaire.model_dump(by_alias=True))
    
    for question in questionnaire.questions:
        existing_question = await app.mongodb.Liste_Question.find_one({"theme": question.theme, "content": question.content})
        if not existing_question:
            saved_question = {"theme": question.theme, "content": question.content}
            await app.mongodb.Liste_Question.insert_one(saved_question)
    
    return {"id": str(result.inserted_id), "category": questionnaire.category}

@app.get("/questions/")
async def get_saved_questions():
    questions = []
    async for question in app.mongodb.Liste_Question.find():
        questions.append(document_to_dict(question))
    return questions

@app.get("/questionnaires/{category}", response_model=Questionnaire)
async def get_questionnaire_by_category(category: str):
    questionnaire = await app.mongodb.Questionnaires.find_one({"category": category})
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Ce questionnaire n'existe pas.")
    return questionnaire

@app.get("/questionnaires/")
async def get_questionnaires():
    questionnaires = []
    async for questionnaire in app.mongodb.Questionnaires.find():
        questionnaires.append(document_to_dict(questionnaire))
    return questionnaires

@app.delete("/questionnaires/{category}")
async def delete_questionnaire(category: str):
    result = await app.mongodb.Questionnaires.delete_one({"category": category})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ce questionnaire n'existe pas.")

@app.put("/questionnaires/{category}")
async def update_questionnaire(category: str, questionnaire: Questionnaire):
    try:
        existing = await app.mongodb.Questionnaires.find_one({"category": category})
        if not existing:
            raise HTTPException(status_code=404, detail="Ce questionnaire n'existe pas.")
        
        result = await app.mongodb.Questionnaires.update_one(
            {"category": category},
            {"$set": questionnaire.dict(by_alias=True)}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update the questionnaire.")
        
        return {"message": "Questionnaire updated successfully"}
    
    except Exception as e:
        print(f"Error updating questionnaire: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while updating the questionnaire.")
    
@app.post("/responses/")
async def save_responses(response: CandidatResponse):
    existing_response = await app.mongodb.Responses.find_one({
        "email": response.email,
        "questionnaire_category": response.questionnaire_category
    })
    if existing_response:
        raise HTTPException(status_code=400, detail="Réponses déjà enregistrées pour ce questionnaire.")
    
    response_dict = response.model_dump()
    result = await app.mongodb.Responses.insert_one(response_dict)
    return {"_id": str(result.inserted_id), "email": response.email, "questionnaire_category": response.questionnaire_category}, 200

@app.get("/responses/")
async def get_responses():
    responses = []
    async for response in app.mongodb.Responses.find():
        responses.append(document_to_dict(response))
    return responses

@app.get("/responses/{email}")
async def get_responses_by_email(email: str):
    responses = []
    async for response in app.mongodb.Responses.find({"email": email}):
        responses.append(document_to_dict(response))
    return responses