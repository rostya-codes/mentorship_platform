import requests


url = 'http://127.0.0.1:8000/api/profile/'
access_token = ''

headers = {
    'Authorization': f'Bearer {access_token}',
}

response = requests.get(url, headers=headers)
print(response.status_code)
print(response.json())
