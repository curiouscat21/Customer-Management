import pytest
from flask import Flask
from flask.testing import FlaskClient
from unittest.mock import MagicMock, patch
from werkzeug.exceptions import BadRequest
from api import app, data_fetch

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["MYSQL_HOST"] = "mock_host"
    app.config["MYSQL_USER"] = "mock_user"
    app.config["MYSQL_PASSWORD"] = "mock_password"
    app.config["MYSQL_DB"] = "mock_db"
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db(mocker):
    # Create a mock cursor
    mock_cursor = MagicMock()
    
    # Create a mock connection
    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    
    # Create a mock MySQL instance
    mock_mysql = MagicMock()
    mock_mysql.connection = mock_connection
    
    # Patch the MySQL instance in your application
    with patch('api.mysql', mock_mysql):
        yield mock_cursor

# Basic Route Tests
def test_hello_world(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello, World!" in response.data

# Permission Levels Endpoint Tests
def test_get_permission_levels_success(client: FlaskClient, mock_db):
    mock_db.fetchall.return_value = [
        {"Permission_Level_ID": 1, "Permission_Level_Code": "READ"}
    ]
    response = client.get("/permission_levels")
    assert response.status_code == 200

def test_update_permission_level(client: FlaskClient, mock_db):
    data = {
        "Permission_Level_Description": "Updated Description"  # Correct field name
    }
    response = client.put("/permission_levels/1", json=data)
    assert response.status_code == 200
    assert "Permission level updated successfully" in response.get_data(as_text=True)

def test_invalid_permission_level_data(client: FlaskClient):
    response = client.post("/permission_levels", json={})
    assert response.status_code == 400

# People Endpoint Tests
def test_add_person_success(client: FlaskClient, mock_db):
    person_data = {
        "Permission_Level_Code": "READ",
        "Login_Name": "testuser",
        "Password": "password123",
        "Personal_Details": "Test User",
        "Other_Details": "None",
        "Country_Name": "US",
        "Role_Description": "USER"
    }
    response = client.post("/people", json=person_data)
    assert response.status_code == 201
    assert "Person added successfully" in response.get_data(as_text=True)

def test_get_people_success(client: FlaskClient, mock_db):
    mock_db.fetchall.return_value = [
        {"Person_ID": 1, "Login_Name": "testuser"}
    ]
    response = client.get("/people")
    assert response.status_code == 200

# Internal Messages Endpoint Tests
def test_get_internal_messages_success(client: FlaskClient, mock_db):
    mock_db.fetchall.return_value = [
        {"Message_ID": 1, "message_text": "Test message"}
    ]
    response = client.get("/internal_messages")
    assert response.status_code == 200

# Payments Endpoint Tests
def test_get_payments_success(client: FlaskClient, mock_db):
    mock_db.fetchall.return_value = [
        {"Payment_ID": 1, "Amount": 100.00}
    ]
    response = client.get("/payments")
    assert response.status_code == 200

# Monthly Reports Endpoint Tests
def test_get_monthly_reports_success(client: FlaskClient, mock_db):
    mock_db.fetchall.return_value = [
        {"Report_ID": 1, "Report_Text": "Monthly Report"}
    ]
    response = client.get("/monthly_reports")
    assert response.status_code == 200

def test_delete_nonexistent_person(client: FlaskClient, mock_db):
    mock_db.rowcount = 0
    response = client.delete("/people/999")
    assert response.status_code == 404

def test_delete_nonexistent_message(client: FlaskClient, mock_db):
    mock_db.rowcount = 0
    response = client.delete("/internal_messages/999")
    assert response.status_code == 404

def test_delete_nonexistent_payment(client: FlaskClient, mock_db):
    mock_db.rowcount = 0
    response = client.delete("/payments/999")
    assert response.status_code == 404

def test_delete_nonexistent_monthly_report(client: FlaskClient, mock_db):
    mock_db.rowcount = 0
    response = client.delete("/monthly_reports/999")
    assert response.status_code == 404

def test_add_permission_level_duplicate(client: FlaskClient, mock_db):
    mock_db.fetchall.return_value = []  # Simulate no existing permission levels
    data = {
        "Permission_Level_Code": "ADMIN",
        "Permission_Level_Description": "Administrator"
    }
    client.post("/permission_levels", json=data)  # Add first
    response = client.post("/permission_levels", json=data)  # Try to add duplicate
    assert response.status_code == 400
    assert "Permission_Level_Code already exists." in response.get_data(as_text=True)

def test_update_person_not_found(client: FlaskClient, mock_db):
    mock_db.rowcount = 0  # Simulate person not found
    data = {
        "Login_Name": "updateduser"
    }
    response = client.put("/people/999", json=data)  # Non-existent ID
    assert response.status_code == 404
    assert "Person not found" in response.get_data(as_text=True)

# Additional Tests for Internal Messages
def test_add_internal_message_missing_fields(client: FlaskClient):
    data = {
        "msg_from_person_id": 1,
        "msg_to_person_id": 2
        # Missing other required fields
    }
    response = client.post("/internal_messages", json=data)
    assert response.status_code == 400

def test_update_payment_not_found(client: FlaskClient, mock_db):
    mock_db.rowcount = 0  # Simulate payment not found
    data = {
        "amount": 150.00,
        "payment_date": "2023-01-02",
        "payment_method": "DEBIT"
    }
    response = client.put("/payments/999", json=data)  # Non-existent ID
    assert response.status_code == 404
    assert "Payment not found" in response.get_data(as_text=True)

# Additional Tests for Monthly Reports
def test_add_monthly_report_missing_fields(client: FlaskClient):
    data = {
        "Person_ID": 1,
        "Date_Report_Sent": "2023-01-01"
        # Missing Report_Text
    }
    response = client.post("/monthly_reports", json=data)
    assert response.status_code == 400

def test_update_monthly_report_not_found(client: FlaskClient, mock_db):
    mock_db.rowcount = 0  # Simulate report not found
    data = {
        "report_title": "Updated Title",
        "report_date": "2023-01-02",
        "report_content": "Updated content"
    }
    response = client.put("/monthly_reports/999", json=data)  # Non-existent ID
    assert response.status_code == 404
    assert "Monthly report not found" in response.get_data(as_text=True)