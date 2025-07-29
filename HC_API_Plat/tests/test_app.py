# import pytest
# import json
# from run import app
# from app.models import db, User, MockRule, Project
#
# @pytest.fixture
# def client():
#     app.config['TESTING'] = True
#     with app.test_client() as client:
#         yield client
#
# # Helper to parse JSON responses
# def get_json(resp):
#     return json.loads(resp.get_data(as_text=True))
#
# # 1. Test user registration and login
# def test_register_and_login(client):
#     resp = client.post('/api/auth/register', json={'username': 'testuser', 'password': 'pass'})
#     assert resp.status_code == 201
#     data = get_json(resp)
#     assert 'access_token' in data
#
#     resp2 = client.post('/api/auth/login', json={'username': 'testuser', 'password': 'pass'})
#     assert resp2.status_code == 200
#     data2 = get_json(resp2)
#     assert 'access_token' in data2
#
# # 2. Test project CRUD
# def test_project_crud(client):
#     resp = client.post('/api/projects', json={'name': 'Proj1', 'base_url': '/api1', 'description': 'desc'})
#     assert resp.status_code == 201
#     proj = get_json(resp)
#     pid = proj['id']
#
#     resp_list = client.get('/api/projects')
#     assert resp_list.status_code == 200
#     assert any(p['id'] == pid for p in get_json(resp_list))
#
#     resp_upd = client.put(f'/api/projects/{pid}', json={'name': 'Proj1b'})
#     assert resp_upd.status_code == 200
#     assert get_json(resp_upd)['name'] == 'Proj1b'
#
#     resp_del = client.delete(f'/api/projects/{pid}')
#     assert resp_del.status_code == 204
#
# # 3. Test mock rule lifecycle and mock endpoint
# def test_mock_rule_and_endpoint(client):
#     # Setup project
#     resp = client.post('/api/projects', json={'name': 'Proj2', 'base_url': '/api2', 'description': ''})
#     pid = get_json(resp)['id']
#
#     # Create mock login stub
#     rule_data = {
#         'method': 'POST',
#         'path_regex': f'^/projects/{pid}/login$',
#         'status_code': 200,
#         'headers': {'Content-Type': 'application/json'},
#         'body_template': {'template': '{"access_token":"fake-jwt-123"}'}
#     }
#     resp_rule = client.post(f'/api/projects/{pid}/rules', json=rule_data)
#     assert resp_rule.status_code == 201
#     rid = get_json(resp_rule)['id']
#
#     # Call the mock login endpoint
#     resp_m = client.post(f'/api/projects/{pid}/login', json={'foo': 'bar'})
#     assert resp_m.status_code == 200
#     assert get_json(resp_m)['access_token'] == 'fake-jwt-123'
#
#     # List rules
#     resp_list = client.get(f'/api/projects/{pid}/rules')
#     assert resp_list.status_code == 200
#     rules = get_json(resp_list)
#     assert any(r['id'] == rid for r in rules)
#
#     # Toggle rule off
#     resp_t = client.post(f'/api/projects/{pid}/rules/{rid}/toggle')
#     assert resp_t.status_code == 200
#     assert get_json(resp_t)['enabled'] is False
#
#     # Mock endpoint should now 404
#     resp_off = client.post(f'/api/projects/{pid}/login', json={'foo': 'bar'})
#     assert resp_off.status_code == 404
#
#     # Toggle back on
#     client.post(f'/api/projects/{pid}/rules/{rid}/toggle')
#     resp_on = client.post(f'/api/projects/{pid}/login', json={'foo': 'bar'})
#     assert resp_on.status_code == 200
#
#     # Update rule - change delay
#     resp_upd = client.put(f'/api/projects/{pid}/rules/{rid}', json={'delay': 5})
#     assert resp_upd.status_code == 200
#     assert get_json(resp_upd)['delay'] == 5
#
#     # Delete rule
#     resp_del = client.delete(f'/api/projects/{pid}/rules/{rid}')
#     assert resp_del.status_code == 204
#
# # 4. Test logs and clear logs
# def test_logs_and_clear(client):
#     # Clear existing logs to ensure isolation
#     client.delete('/api/logs')
#     resp = client.get('/api/logs')
#     assert get_json(resp) == []
#
#     # Create project and rule, trigger mock
#     resp = client.post('/api/projects', json={'name': 'P3', 'base_url': '/', 'description': ''})
#     pid = get_json(resp)['id']
#     client.post(f'/api/projects/{pid}/rules', json={
#         'method': 'GET',
#         'path_regex': f'^/projects/{pid}/echo$',
#         'status_code': 201,
#         'headers': {'Content-Type': 'application/json'},
#         'body_template': {'template': '{"ok":true}'}
#     })
#     client.get(f'/api/projects/{pid}/echo')
#
#     # Logs should have 1 entry
#     resp_logs = client.get('/api/logs')
#     logs = get_json(resp_logs)
#     assert len(logs) == 1
#     assert logs[0]['method'] == 'GET'
#     assert logs[0]['status_code'] == 201
#
#     # Clear logs
#     resp_clear = client.delete('/api/logs')
#     assert resp_clear.status_code == 200
#     assert get_json(resp_clear)['deleted'] == 1
#
#     # Logs now empty
#     assert get_json(client.get('/api/logs')) == []
