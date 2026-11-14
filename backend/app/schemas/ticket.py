from pydantic import BaseModel, Field
from typing import Optional

from app.models.ticket import TicketCategory, TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10)
    category: TicketCategory
    


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    created_by: int
    assigned_agent: Optional[int]

    class Config:
        from_attributes = True





class TicketUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=200)
    description: Optional[str] = Field(default=None, min_length=10)
    category: Optional[TicketCategory] = None




class TicketAssign(BaseModel):
    agent_id: int = Field(gt=0)



class TicketManagementUpdate(BaseModel):
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None





class TicketPaginationResponse(BaseModel):
    total_tickets: int
    total_pages: int
    current_page: int
    limit: int
    tickets: list[TicketResponse]