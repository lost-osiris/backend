from pydantic import BaseModel


class IssueComment(BaseModel):
    comment: str
