import requests

url = 'http://127.0.0.1:8000/api/profile/'
access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ4NTM1NjkwLCJpYXQiOjE3NDg1MzQ3OTAsImp0aSI6IjI5MzUzNDEzNjU0MjQ5OGViMTUzNWU5YjkwNTkxOTMxIiwidXNlcl9pZCI6MX0.Pf-xWcHVbKHTSgQ4-02iyanf-doZpZvbCj-pBGa0E3k'

headers = {
    'Authorization': f'Bearer {access_token}',
}

response = requests.get(url, headers=headers)
print(response.status_code)
print(response.json())
