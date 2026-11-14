from fastapi import APIRouter,Query
from datetime import date,datetime,timedelta
from typing import Optional,Literal
import math


from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.ticket import Ticket, TicketPriority, TicketStatus,TicketCategory
from app.schemas.ticket import TicketCreate, TicketResponse,TicketUpdate,TicketAssign,TicketManagementUpdate,TicketPaginationResponse
from app.utils.dependencies import get_current_user,get_current_admin
from app.models.user import User



def get_admin_or_agent(
    current_user=Depends(get_current_user)
):
    if current_user.role.name not in ["Admin", "Support Agent"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return current_user


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)





@router.post("/create", response_model=TicketResponse)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    new_ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
        created_by=current_user.id
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket






@router.get("/my-tickets", response_model=list[TicketResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    tickets = db.query(Ticket).filter(
        Ticket.created_by == current_user.id
    ).all()

    return tickets



@router.get("/all",response_model=list[TicketResponse],dependencies=[Depends(get_admin_or_agent)])
def get_all_tickets( db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    return tickets






@router.get("/details/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.created_by == current_user.id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket





@router.put("/update/{ticket_id}",response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.created_by == current_user.id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket_data.title is not None:
        ticket.title = ticket_data.title

    if ticket_data.description is not None:
        ticket.description = ticket_data.description

    if ticket_data.category is not None:
        ticket.category = ticket_data.category

    db.commit()
    db.refresh(ticket)

    return ticket




@router.put("/{ticket_id}/assign", response_model=TicketResponse,dependencies=[Depends(get_current_admin)])
def assign_ticket(
    ticket_id: int,
    assign_data: TicketAssign,
    db: Session = Depends(get_db)
):
    # Check whether ticket exists
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # Check whether the agent exists
    agent = db.query(User).filter(
        User.id == assign_data.agent_id,
        User.is_active == True
    ).first()

    if not agent or agent.role.name != "Support Agent":
        raise HTTPException(
            status_code=404,
            detail="Active Support Agent not found"
        )

    # Assign ticket
    ticket.assigned_agent = agent.id

    db.commit()
    db.refresh(ticket)

    return ticket






@router.put(
    "/{ticket_id}/manage",
    response_model=TicketResponse,
    dependencies=[Depends(get_admin_or_agent)]
)
def manage_ticket(
    ticket_id: int,
    update_data: TicketManagementUpdate,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if update_data.priority is not None:
        ticket.priority = update_data.priority

    if update_data.status is not None:
        ticket.status = update_data.status

    db.commit()
    db.refresh(ticket)

    return ticket





@router.get(
    "/search",
    response_model=list[TicketResponse],
    dependencies=[Depends(get_admin_or_agent)]
)
def search_tickets(
    search: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    query = db.query(Ticket)

    # Search by ticket title
    query = query.filter(
        Ticket.title.ilike(f"%{search}%")
        if not search.isdigit()
        else (
            (Ticket.title.ilike(f"%{search}%")) |
            (Ticket.id == int(search))
        )
    )

    tickets = query.all()

    return tickets




@router.get(
    "/filter",
    response_model=TicketPaginationResponse,
    dependencies=[Depends(get_admin_or_agent)]
)
def filter_tickets(
    category: Optional[TicketCategory] = None,
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    user_email: Optional[str] = None,
    agent_id: Optional[int] = None,
    created_from: Optional[date] = None,
    created_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: Literal["created_at", "updated_at", "title", "priority", "status", "id"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db)
):
    query = db.query(Ticket)

    if category is not None:
        query = query.filter(Ticket.category == category)

    if status is not None:
        query = query.filter(Ticket.status == status)

    if priority is not None:
        query = query.filter(Ticket.priority == priority)

    if user_email is not None:
        query = query.join(User, Ticket.created_by == User.id).filter(
        User.email.ilike(f"%{user_email}%")
    )

    if agent_id is not None:
        query = query.filter(Ticket.assigned_agent == agent_id)


    if created_from is not None:
        query = query.filter(
        Ticket.created_at >= datetime.combine(created_from, datetime.min.time())
    )

    if created_to is not None:
        query = query.filter(
        Ticket.created_at < datetime.combine(
            created_to + timedelta(days=1),
            datetime.min.time()
        )
    )


    sort_column = getattr(Ticket, sort_by)

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    tickets = query.offset(skip).limit(limit).all()

    total_tickets = query.count()
    total_pages = math.ceil(total_tickets / limit)
    current_page = (skip // limit) + 1

    return {
    "total_tickets": total_tickets,
    "total_pages": total_pages,
    "current_page": current_page,
    "limit": limit,
    "tickets": tickets
}