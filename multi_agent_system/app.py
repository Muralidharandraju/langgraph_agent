from fastapi import FastAPI
from pydantic import BaseModel
from agent_workflow import DoctorAppointmentAgent
import os
from langchain_core.messages import HumanMessage

os.environ.pop("SSL_CERT_FILE", None)

class UserQuery(BaseModel):
    query: str
    id_number:int

app = FastAPI()
agent = DoctorAppointmentAgent()
workflow = agent.workflow( )

@app.post("/chat")
async def chat(user_query: UserQuery):
    
    
    response = workflow.invoke({"messages": [HumanMessage(content=user_query.query)],
                                "id_number":user_query.id_number},
                                {"recursion_limit": 20})
    
    return response
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


