from typing import Literal,List,Dict
from langchain_core.tools import tool
from langgraph.types import Command
from typing_extensions import TypedDict,Annotated
from langchain_core.prompts.chat import ChatPromptTemplate
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from prompt_library.prompt import system_prompt
from utils.llm import LLMModel
from agent_tools.tools import check_availability_by_doctor, check_availability_by_specialization, \
    set_appointment, cancel_appointment, reschedule_appointment
from models.model import Router, AgentState
import logging
import json

#reading json for user specific variables
with open("./config.json", 'r') as f:
    config = json.load(f)

log_file_save_path = config['log_file_save_path']

logging.basicConfig(filename=log_file_save_path+'log_information.txt',level=logging.INFO)
logging.warning("AGENT WORKFLOW LOGGING INITIALIZED ") 
logger = logging.getLogger(__name__)

            
class DoctorAppointmentAgent:
    def __init__(self):
        llm_model = LLMModel()
        self.llm_model= llm_model.get_llm()
        
    
    def supervisor_node(self, state: AgentState) -> Command[Literal['information_node', 'booking_node', '__end__']]:
        
        logger.info(f"Entering supervisor node. Current state: {state}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"user's identification number is {state['id_number']}"},
        ] + state["messages"]
        
        
        query = ''
        if len(state['messages']) == 1:
            query = state['messages'][0].content
        
        
        response = self.llm_model.with_structured_output(Router).invoke(messages)
        
        goto = response["next"]
        
        logging.info(f"information on next step: {goto}")
        
        logging.info(f"response from LLM: {response}")
            
        if goto == "FINISH":
            goto = END
            
        
        if query:
            return Command(goto=goto, update={'next': goto, 
                                            'query': query, 
                                            'current_reasoning': response["reasoning"],
                                            'messages': [HumanMessage(content=f"user's identification number is {state['id_number']}")]
                            })
        return Command(goto=goto, update={'next': goto, 
                                        'current_reasoning': response["reasoning"]}
                    )


    def information_node(self, state:AgentState) -> Command[Literal['supervisor']]:
        logger.info(f"Information node state: {state}") # Use f-string

        try:
            info_system_prompt_content = (
                "You are a specialized agent to provide information related to availability of doctors or any FAQs "
                "related to the hospital based on the query. You have access to tools.\n"
                "Make sure to ask the user politely if you need any further information to execute the tool.\n"
                "doctor are available if the "
            )

            # Use the corrected variable name
            info_system_prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            info_system_prompt_content # Use the content string here
                        ),
                        (
                            "placeholder",
                            "{messages}"
                        ),
                    ]
                )

            
            information_agent = create_react_agent(
                model=self.llm_model, 
                tools=[check_availability_by_doctor, check_availability_by_specialization],
                prompt=info_system_prompt 
            )


            result = information_agent.invoke(state)

            # new_messages = result.get("messages", [])
            # last_message = new_messages[-1] if new_messages else AIMessage(content="No response from information agent.", name="information_node")

            # Ensureing the message has the correct name attribute if needed in downstream
            # if not getattr(last_message, 'name', None):
            #         last_message.name = "information_node"

            return Command(
                update={
                "messages": state["messages"] + [
                    AIMessage(content=result["messages"][-1].content, name="information_node")
                ]},goto="supervisor",
            )
        except Exception as e:
             print(str(e))

    def booking_node(self, state:AgentState) -> Command[Literal['supervisor']]:
        logger.info(f"Booking node state: {state}")


        booking_system_prompt_content = (
            "You are a specialized agent to set, cancel, or reschedule appointments based on the query. "
            "You have access to tools.\n"
            "Make sure to ask the user politely if you need any further information to execute the tool.\n"
        )

        # Use the corrected variable name
        booking_system_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        booking_system_prompt_content 
                    ),
                    (
                        "placeholder",
                        "{messages}"
                    ),
                ]
            )

        
        booking_agent = create_react_agent(
            model=self.llm_model, 
            tools=[set_appointment, cancel_appointment, reschedule_appointment],
            prompt=booking_system_prompt 
        )

        agent_input = {"messages": state["messages"]}
        results = booking_agent.invoke(agent_input)

        
        new_messages = results.get("messages", [])
        last_message = new_messages[-1] if new_messages else AIMessage(content="No response from booking agent.", name="booking_node")

        # Ensureing the message has the correct name attribute if needed in downstream
        if not getattr(last_message, 'name', None):
                last_message.name = "booking_node"

        return Command(
            update={
                "messages": [last_message]
            },
            goto="supervisor"
        )


    def workflow(self):
        try:
            self.graph = StateGraph(AgentState)
            self.graph.add_node("supervisor", self.supervisor_node)
            self.graph.add_node("information_node", self.information_node)
            self.graph.add_node("booking_node", self.booking_node)
            self.graph.set_entry_point("supervisor")

            
            self.graph.add_conditional_edges(
                "supervisor",
                lambda state: state['next'], 
                {
                    "information_node": "information_node",
                    "booking_node": "booking_node",
                    END: END
                    }
            )

            
            self.graph.add_edge("information_node", "supervisor")
            self.graph.add_edge("booking_node", "supervisor")


            
            self.app = self.graph.compile()
            logging.info("Graph compiled successfully and app is ready.")
            return self.app

        except Exception as e:
            
            logging.exception("Exception occurred while building or compiling the graph:")
            
            raise e


