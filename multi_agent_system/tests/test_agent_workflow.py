
import os,sys
sys.path.append("./.")
import pytest
from unittest.mock import patch, MagicMock
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from workflow.agent_workflow import DoctorAppointmentAgent,AgentState
from models.model import Router



@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock external dependencies like LLM and tools."""
    
    with patch('agent_workflow.LLMModel') as mock_llm_model_cls, \
         patch('agent_workflow.create_react_agent') as mock_create_agent, \
         patch('agent_workflow.check_availability_by_doctor') as mock_tool_check_dr, \
         patch('agent_workflow.check_availability_by_specialization') as mock_tool_check_spec, \
         patch('agent_workflow.set_appointment') as mock_tool_set_appt, \
         patch('agent_workflow.cancel_appointment') as mock_tool_cancel_appt, \
         patch('agent_workflow.reschedule_appointment') as mock_tool_resched_appt:

        # Configure the mock LLM instance returned by LLMModel().get_llm()
        mock_llm_instance = MagicMock()
        mock_llm_model_cls.return_value.get_llm.return_value = mock_llm_instance

        # Configure mock agent returned by create_react_agent
        mock_agent_instance = MagicMock()
        mock_create_agent.return_value = mock_agent_instance

        # Yield the mocks if needed in tests, otherwise just let the context manager handle it
        yield {
            "llm_instance": mock_llm_instance,
            "agent_instance": mock_agent_instance,
            "mock_tool_check_dr": mock_tool_check_dr,
        }



@pytest.fixture
def test_supervisor_node_route_to_info(agent_instance, mock_dependencies):
    """Test supervisor node routing to information_node."""
    # Configure the mock LLM's structured output for this test
    mock_llm = mock_dependencies["llm_instance"]
    mock_llm.with_structured_output.return_value.invoke.return_value = Router(
        next="information_node",
        reasoning="User is asking for doctor availability."
    )

    initial_state = AgentState(
        messages=[HumanMessage(content="Is Dr. Smith available?")],
        id_number=123,
        next="",
        query="",
        current_reasoning=""
    )

    command = agent_instance.supervisor_node(initial_state)

    assert isinstance(command, Command)
    assert command.goto == "information_node"
    assert command.update['next'] == "information_node"
    assert command.update['query'] == "Is Dr. Smith available?"
    assert command.update['current_reasoning'] == "User is asking for doctor availability."
    # Check that the id_number message was added correctly
    assert len(command.update['messages']) == 1
    assert isinstance(command.update['messages'][0], HumanMessage)
    assert "user's identification number is 123" in command.update['messages'][0].content

    # Verify LLM call
    mock_llm.with_structured_output.assert_called_once_with(Router)
    mock_llm.with_structured_output.return_value.invoke.assert_called_once()
    call_args = mock_llm.with_structured_output.return_value.invoke.call_args[0][0]
    assert call_args[0]['role'] == 'system' # system prompt
    assert call_args[1]['role'] == 'user' and "123" in call_args[1]['content'] # id number
    assert call_args[2]['role'] == 'user' and "Is Dr. Smith available?" in call_args[2]['content'] # user query


def test_supervisor_node_route_to_finish(agent_instance, mock_dependencies):
    """Test supervisor node routing to END."""
    mock_llm = mock_dependencies["llm_instance"]
    mock_llm.with_structured_output.return_value.invoke.return_value = Router(
        next="FINISH",
        reasoning="Conversation is complete."
    )

    state = AgentState(
        messages=[HumanMessage(content="Thanks!")],
        id_number=456,
        next="",
        query="Thanks!", # Assume query was set in a previous step
        current_reasoning=""
    )

    command = agent_instance.supervisor_node(state)

    assert command.goto == END
    assert command.update['next'] == "FINISH" # 'next' state field still holds the original LLM response
    assert command.update['current_reasoning'] == "Conversation is complete."
    assert 'query' not in command.update # Query shouldn't be updated if it wasn't the first message



def test_information_node(agent_instance, mock_dependencies):
    """Test the information node logic."""
    mock_agent = mock_dependencies["agent_instance"]
    mock_agent.invoke.return_value = {
        "messages": [AIMessage(content="Dr. Smith is available tomorrow at 10 AM.")]
    }

    initial_state = AgentState(
        messages=[HumanMessage(content="Is Dr. Smith available?")],
        id_number=789,
        next="information_node",
        query="Is Dr. Smith available?",
        current_reasoning="Checking availability."
    )

    command = agent_instance.information_node(initial_state)

    assert command.goto == "supervisor"
    assert len(command.update["messages"]) == 2 # Initial + AI response
    new_message = command.update["messages"][-1]
    assert isinstance(new_message, AIMessage)
    assert new_message.content == "Dr. Smith is available tomorrow at 10 AM."
    assert new_message.name == "information_node"

    # Verify the react agent was invoked correctly
    mock_agent.invoke.assert_called_once_with(initial_state)


def test_booking_node(agent_instance, mock_dependencies):
    """Test the booking node logic."""
    mock_agent = mock_dependencies["agent_instance"]
    mock_agent.invoke.return_value = {
        "messages": [AIMessage(content="OK. Appointment is booked.")]
    }

    initial_state = AgentState(
        messages=[HumanMessage(content="Book it.")],
        id_number=101,
        next="booking_node",
        query="Book it.",
        current_reasoning="Booking appointment."
    )

    command = agent_instance.booking_node(initial_state)

    assert command.goto == "supervisor"
    # Note: Your current booking_node replaces messages, it doesn't append
    assert len(command.update["messages"]) == 1
    new_message = command.update["messages"][0]
    assert isinstance(new_message, AIMessage)
    assert new_message.content == "OK. Appointment is booked."
    assert new_message.name == "booking_node"

    # Verify the react agent was invoked correctly
    mock_agent.invoke.assert_called_once_with({"messages": initial_state["messages"]})

