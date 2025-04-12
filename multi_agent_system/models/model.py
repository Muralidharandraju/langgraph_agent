
import re
from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict,Annotated
from typing import Literal,List,Any
from langgraph.graph.message import add_messages



class DateTimeModel(BaseModel):
    date: str = Field(description=" date format for reservation of appointment", pattern=r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$')

    @field_validator("date")
    def check_format_date(cls, date_time_value):
        if not re.match(r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}$', date_time_value):  # Ensures 'DD-MM-YYYY HH:MM' format
            raise ValueError("The date should be in format 'DD-MM-YYYY HH:MM'")
        return date_time_value
    


class DateModel(BaseModel):
    date: str = Field(description="Properly formatted date", pattern=r'^\d{2}-\d{2}-\d{4}$')

    @field_validator("date")
    def check_format_date(cls, date_value):
        if not re.match(r'^\d{2}-\d{2}-\d{4}$', date_value):  # Ensures DD-MM-YYYY format
            raise ValueError("The date must be in the format 'DD-MM-YYYY'")
        return date_value
    


class IdentificationNumberModel(BaseModel):
    id: int = Field(description="Identification number (7 or 8 digits long)")
    @field_validator("id")
    def check_format_id(cls, id_number):
        if not re.match(r'^\d{7,8}$', str(id_number)):  # Convert to string before matching
            raise ValueError("The ID number should be a 7 or 8-digit number")
        return id_number



class Router(TypedDict):
    next:Literal["information_node","booking_node","FINISH"]
    reasoning:str


class AgentState(TypedDict):
    messages: Annotated[list[Any],add_messages]
    id_number:int
    next:str
    query:str
    current_reasoning:str




