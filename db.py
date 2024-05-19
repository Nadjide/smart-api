import sqlite3

conn = sqlite3.connect('database.db')

c = conn.cursor()

c.execute('''
    CREATE TABLE User (
        Email TEXT PRIMARY KEY,
        password TEXT
    )
''')

c.execute('''
    CREATE TABLE Candidats (
        Email TEXT PRIMARY KEY,
        Nom TEXT,
        Prénom TEXT,
        Date_de_naissance TEXT,
        Téléphone TEXT
    )
''')

c.execute('''
    CREATE TABLE Questionnaires (
        ID_Questionnaire INTEGER PRIMARY KEY,
        Titre TEXT,
        Questions TEXT
    )
''')

c.execute('''
    CREATE TABLE Réponses_Questionnaires (
        ID_Réponse INTEGER PRIMARY KEY,
        ID_Questionnaire INTEGER,
        Email TEXT,
        Réponses TEXT,
        Score INTEGER,
        FOREIGN KEY(ID_Questionnaire) REFERENCES Questionnaires(ID_Questionnaire),
        FOREIGN KEY(Email) REFERENCES Candidats(Email)
    )
''')

c.execute('''
    CREATE TABLE Statistiques (
        ID_Statistique INTEGER PRIMARY KEY,
        Email TEXT,
        Catégorie TEXT,
        Valeur REAL,
        Date_Mesure TEXT,
        FOREIGN KEY(Email) REFERENCES Candidats(Email)
    )
''')

conn.commit()

conn.close()