from pydantic import BaseModel

class GenerateRequest(BaseModel):
    prefix: str
    max_length: int = 100
