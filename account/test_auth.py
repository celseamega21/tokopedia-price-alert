from rest_framework_simplejwt.tokens import AccessToken

def test_login(api_client, user, refresh_url):
    data = {
        'username': 'test',
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    response = api_client.post(refresh_url, data, format='json')

    assert response.status_code == 200
    assert 'message' in response.data
    assert 'refresh' in response.data

    token = AccessToken(response.data['access'])
    assert token['email'] == 'test@example.com'