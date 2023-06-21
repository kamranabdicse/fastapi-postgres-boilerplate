import httpx

def test_reset_password():
    url = "http://127.0.0.1:8000/api/v1/users/reset-password/"  # Replace with your actual endpoint URL
    payload = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODczNTUwNDQsInN1YiI6IjEifQ.LIyfxHMIy-U1SHLzTveh8acSYANgicDwnhUUBI0WEck",
        "new_password": "admin123"
    }
    #vaild token test
    with httpx.Client() as client:
        response = client.post(url, json=payload)
        assert response.status_code ==200
        assert response.json() =={'msg': 'Password updated successfully'}
    #unvalid token test
    payload = {
        "token": "invalid",
        "new_password": "admin123"
    }
    with httpx.Client() as client:
        response = client.post(url, json=payload)
        assert response.status_code == 400
        assert response.json()['content'] == 'Invalid token.'


