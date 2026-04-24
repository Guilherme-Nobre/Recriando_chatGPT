from pydantic import BaseModel

class PromptRequest(BaseModel):
    chat_id: str
    prompt: str
    max_new_tokens: int = 512