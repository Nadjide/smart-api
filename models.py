from typing import List
from pydantic import BaseModel, EmailStr, validator

class Admin(BaseModel):
    email: EmailStr
    password: str

class Candidat(BaseModel):
    email: EmailStr
    nom: str
    prénom: str
    date_de_naissance: str
    téléphone: str

    @validator('date_de_naissance')
    def parse_date(cls, v):
        return v

class Answer(BaseModel):
    text: str
    score: int

class Question(BaseModel):
    theme: str
    content: str
    answers: List[Answer]

class Questionnaire(BaseModel):
    category: str
    questions: List[Question]

class SavedQuestion(BaseModel):
    theme: str
    content: str

class CandidatAnswer(BaseModel):
    question_index: int
    answer_index: int
    question_text: str
    theme : str
    answer_text: str
    score: int

class CandidatResponse(BaseModel):
    email: EmailStr
    questionnaire_category: str
    answers: List[CandidatAnswer]