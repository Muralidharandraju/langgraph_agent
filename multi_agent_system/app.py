from fastapi import FastAPI
from pydantic import BaseModel
from workflow.agent_workflow import DoctorAppointmentAgent
import os
from langchain_core.messages import HumanMessage

# os.environ.pop("SSL_CERT_FILE", None)

class UserQuery(BaseModel):
    query: str
    id_number:int

app = FastAPI()
agent = DoctorAppointmentAgent()
workflow = agent.workflow( )

@app.post("/chat")

async def chat(user_query: UserQuery):
    
    
    response = workflow.invoke({"messages": [HumanMessage(content=user_query.query)],
                                "id_number":user_query.id_number})
    
    return response
    

#health check for app
@app.get("/health")
def health_status():
    '''
    :return: to know the API status, if API is running then you will have status code 200
    '''
    return {'status_code':200,'message':'Api is active'}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


