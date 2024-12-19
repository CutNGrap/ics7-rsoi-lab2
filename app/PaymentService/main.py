from fastapi import *
from fastapi.responses import *
from fastapi.exceptions import RequestValidationError
from sqlmodel import *
from database import Person, PersonScheme
from typing import Annotated
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import uvicorn
from multiprocessing import Process
import os

app = FastAPI()

# "postgresql://program:test@localhost:5432/persons"
# database_url = os.environ["DATABASE_URL"]
database_url = "postgresql://program:test@localhost:5432/persons"
print(database_url)
engine = create_engine(database_url)



def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.get('/api/v1/persons')
def get_persons(session: SessionDep) -> list[Person]:
    return session.exec(select(Person)).all()


@app.get('/api/v1/persons/{person_id}')
def get_person(person_id: int, session: SessionDep) -> Person:
    person = session.get(Person, person_id)
    if not person:
        return JSONResponse(content={"message": "Person not found"}, status_code=404)
    return person


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request : Request, exc):
    return JSONResponse({"message": "what", "errors": exc.errors()[0]}, status_code=400)


@app.post('/api/v1/persons')
def create_person(person: PersonScheme, session: SessionDep):
    person_data = jsonable_encoder(person)
    db_person = Person(**person_data)
    session.add(db_person)
    session.commit()
    session.refresh(db_person)
    return Response(status_code=201, headers={"Location": f"/api/v1/persons/{db_person.id}"})


@app.delete('/api/v1/persons/{person_id}')
def delete_person(person_id: int, session: SessionDep):
    person = session.get(Person, person_id)
    if not person:
        return Response(status_code=204)
    session.delete(person)
    session.commit()
    return Response(status_code=204)


@app.patch('/api/v1/persons/{person_id}')
def update_person(person_id: int, person: PersonScheme, session: SessionDep):
    person.id = person_id
    person_data = jsonable_encoder(person)
    db_person = session.get(Person, person_id)
    if not db_person:
        return JSONResponse(content={"message": "Person not found"}, status_code=404)
    db_person_new = Person(**person_data)
    print("new", db_person_new)
    data = db_person_new.model_dump(exclude_none=True)
    print(data)
    db_person.sqlmodel_update(data)
    session.add(db_person)
    session.commit()
    session.refresh(db_person)
    return db_person

def daemon():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    pr = Process(target=daemon)
    pr.daemon = True
    pr.start()
    pr.join()