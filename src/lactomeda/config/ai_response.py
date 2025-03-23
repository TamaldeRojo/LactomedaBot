from pydantic import BaseModel


class AIResponse(BaseModel):
    command: str
    command_args: list[str]
    response: str