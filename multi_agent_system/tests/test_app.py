
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
sys.path.append("./.")

from app import app



# Create a TestClient instance
client = TestClient(app)

@pytest.fixture
def mock_workflow():
    """Fixture to mock the compiled LangGraph workflow."""
    # Create a mock object that simulates the compiled workflow's invoke method
    mock = MagicMock()
    # Configure the mock's invoke method to return a sample response
    mock.invoke.return_value = {
        "messages": [{"role": "assistant", "content": "Mocked response"}],
        "next": "__end__",
        # Add other expected keys from your AgentState if necessary
    }
    return mock

# Use patch to replace the actual workflow instance during tests
@patch('app.workflow', new_callable=MagicMock)
def test_chat_endpoint_success(mock_workflow_instance):
    """Test the /chat endpoint with a valid request."""
    # Configure the mock return value for this specific test if needed
    mock_workflow_instance.invoke.return_value = {
         "messages": [{"type": "ai", "content": "Appointment confirmed for Dr. Smith."}],
         "next": "__end__",
         "id_number": 12345678,
         "query": "Book appointment",
         "current_reasoning": "User wants to book."
    }

    response = client.post("/chat", json={"query": "Book me an appointment", "id_number": 12345678})

    assert response.status_code == 200
    response_data = response.json()
    assert "messages" in response_data
    assert response_data["messages"][-1]["content"] == "Appointment confirmed for Dr. Smith."
    assert response_data["id_number"] == 12345678

    # Verify that the mocked workflow's invoke method was called correctly
    mock_workflow_instance.invoke.assert_called_once()
    call_args, call_kwargs = mock_workflow_instance.invoke.call_args
    # Check the structure of the input passed to invoke
    assert "messages" in call_args[0]
    assert call_args[0]["messages"][0].content == "Book me an appointment"
    assert "id_number" in call_args[0]
    assert call_args[0]["id_number"] == 12345678


def test_chat_endpoint_invalid_input():
    """Test the /chat endpoint with invalid input data (e.g., missing field)."""
    response = client.post("/chat", json={"query": "Just asking"}) # Missing id_number
    # FastAPI typically returns 422 for validation errors
    assert response.status_code == 422


def test_health_endpoint():
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {'status_code': 200, 'message': 'Api is active'}

