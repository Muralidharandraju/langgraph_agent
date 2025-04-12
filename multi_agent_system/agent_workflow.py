from typing import Literal,List,Dict
from langchain_core.tools import tool
from langgraph.types import Command
from typing_extensions import TypedDict,Annotated
from langchain_core.prompts.chat import ChatPromptTemplate
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from prompt_library.prompt import systemprompt
from utils.llm import LLMModel
from agent_tools.tools import check_availability_by_doctor, check_availability_by_specialization, \
    set_appointment, cancel_appointment, reschedule_appointment
from models.model import Router, AgentState
import logging



logging.basicConfig(level=logging.INFO)
logging.warning("AGENT WORKFLOW LOGGING INITIALIZED ") 
logger = logging.getLogger(__name__)



# class DoctorAppointmentAgent:
#     def __init__(self):
#         llm_model = LLMModel()
#         self.llm = llm_model.get_llm()
#     def supervisor_node(self, state:AgentState) -> Command[Literal['informtaion_node','booking_node','__end__']]:
#         logger.info("the supervisor node state of the agent is ",state)

#         messages = [
#             {"role":"system","content":systemprompt},
#             {"role":"user","content":f"user query {state['id_number']}"}
#         ] + state['messages']


#         query =''
#         if len(state['messages']) ==1:
#             query = state['messages'][0].content
        
#         logging.info("query from the agent ",query)

#         reponse = self.llm.with_structured_output(Router).invoke(messages)

#         go_to = reponse['next']
#         reasoning = reponse['reasoning']
        
#         logging.info("supervisor state llm response from ", go_to)
#         logging.info("supervisor state llm reasoning from the user query",reasoning)


#         if go_to == "FINISH":
#             go_to = END
        
#         if query:
#             return Command(goto=go_to,
#                            update={'next':go_to,
#                                    'query':query,
#                                    'current_reasoning':reasoning,
#                                    'messages':[HumanMessage(content=query),AIMessage(content=reasoning)]})
        
#         return Command(goto=go_to,
#                        update={'next':go_to,
#                                'query':query,
#                                'current_reasoning':reasoning,
#                                'messages':[AIMessage(content=reasoning)]})
    

#     def information_node(self, state:AgentState) -> Command[Literal['supervisor']]:
        
#         logging.info("the information node state of the agent is ",state)
        
#         systemprompt = "You are specialized agent to provide information related to availablity of doctors  or any FAQs \
#             related to hospital based on the query. You have access to the tool.\n Make sure to ask user politely\
#             if you need any further information to execute the tool.\n For your information, Always consider current year is 2024"


#         system_prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         system_prompt
#                     ),
#                     (
#                         "placeholder", 
#                         "{messages}"
#                     ),
#                 ]
#             )
        
#         information_agent = create_react_agent(model=self.llm_model,tools=[check_availability_by_doctor,check_availability_by_specialization] ,prompt=system_prompt)
        
#         result = information_agent.invoke(state)
        
#         return Command(
#             update={
#                 "messages": state["messages"] + [
#                     AIMessage(content=result["messages"][-1].content, name="information_node")
#                     #HumanMessage(content=result["messages"][-1].content, name="information_node")
#                 ]
#             },
#             goto="supervisor",
#         )


#     def booking_node(self, state:AgentState) -> Command[Literal['supervisor']]:
        
#         logging.info("the booking node state of the agent is ",state)

#         system_prompt = "You are specialized agent to set, cancel or reschedule appointment based on the query.\
#               You have access to the tool.\n Make sure to ask user politely if you need any further information\
#                   to execute the tool.\n For your information, Always consider current year is 2024."
        
#         system_prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         system_prompt
#                     ),
#                     (
#                         "placeholder", 
#                         "{messages}"
#                     ),
#                 ]
#             )
        
#         booking_agent = create_react_agent(model=self.llm_model,
#                                            tools=[set_appointment,cancel_appointment,reschedule_appointment],
#                                            prompt=system_prompt)
        
#         results = booking_agent.invoke(state)

#         return Command(
#             update={
#                 "messages": state["messages"] + [
#                     AIMessage(content=results["messages"][-1].content, name="booking_node")]
#             },
#             goto="supervisor"
#         )
        
        

#     def workflow(self):
#         try:
#             self.graph = StateGraph(AgentState)
#             self.graph.add_node("supervisor", self.supervisor_node)
#             self.graph.add_node("information_node", self.information_node)
#             self.graph.add_node("booking_node", self.booking_node)
            
#             self.graph.add_edge(START, "supervisor")
#             self.app = self.graph.compile()
#             logging.info("Graph app is up and running")
#             return self.app
            
#         except Exception as e:
#             logging.exception("exception to load the app",e)# agent_workflow.py
            
#             # ... (imports and other code) ...
            
class DoctorAppointmentAgent:
    def __init__(self):
        llm_model = LLMModel()
        self.llm_model= llm_model.get_llm()
        
    
    def supervisor_node(self, state:AgentState) -> Command[Literal['information_node','booking_node',END]]:
        logger.info(f"Supervisor node state: {state}") # Use f-string for better logging

        
        formatted_messages = [{"role": "system", "content": systemprompt}]
        formatted_messages.append({"role": "user", "content": f"User ID: {state['id_number']}"})
        formatted_messages.extend(state['messages'])

        query =''
        if state['messages'] and isinstance(state['messages'][0], HumanMessage):
            query = state['messages'][0].content
        elif state.get('query'): 
                query = state['query']

        logging.info(f"Query for supervisor: {query}") 

        #llm invoke
        response = self.llm_model.with_structured_output(Router).invoke(formatted_messages)

        go_to = response['next']
        reasoning = response['reasoning']

        logging.info(f"Supervisor decision: route to {go_to}") 
        logging.info(f"Supervisor reasoning: {reasoning}") 

        update_dict = {
            'next': go_to,
            'current_reasoning': reasoning,
            'messages': [AIMessage(content=reasoning)]
        }
        # Only adding the original query message if it's the very first turn
        if len(state['messages']) == 1 and isinstance(state['messages'][0], HumanMessage):
                update_dict['messages'].insert(0, state['messages'][0])
                update_dict['query'] = query 


        if go_to == "FINISH":
            return Command(goto=END) 

        actual_goto = END if go_to == "FINISH" else go_to

        return Command(goto=actual_goto, update=update_dict)


    def information_node(self, state:AgentState) -> Command[Literal['supervisor']]:
        logger.info(f"Information node state: {state}") # Use f-string

        
        info_system_prompt_content = (
            "You are a specialized agent to provide information related to availability of doctors or any FAQs "
            "related to the hospital based on the query. You have access to tools.\n"
            "Make sure to ask the user politely if you need any further information to execute the tool.\n"
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


        agent_input = {"messages": state["messages"]}
        result = information_agent.invoke(agent_input)

        new_messages = result.get("messages", [])
        last_message = new_messages[-1] if new_messages else AIMessage(content="No response from information agent.", name="information_node")

        # Ensureing the message has the correct name attribute if needed in downstream
        if not getattr(last_message, 'name', None):
                last_message.name = "information_node"

        return Command(
            update={
                "messages": [last_message]
            },
            goto="supervisor",
        )


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





