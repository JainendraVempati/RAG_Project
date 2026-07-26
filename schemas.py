from pydantic import BaseModel

class Question(BaseModel):

    filename: str   # tells us WHICH document's FAISS index to load

    question: str   # the actual question being asked

    mode: str        # "document" / "web" / "both"