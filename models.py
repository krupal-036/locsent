import requests
import os
from datetime import datetime
import uuid
import math

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
USERS_DB_ID = os.getenv('NOTION_DATABASE_ID_USERS')
LOCATIONS_DB_ID = os.getenv('NOTION_DATABASE_ID_LOCATIONS')
GEOFENCES_DB_ID = os.getenv('NOTION_DATABASE_ID_GEOFENCES')
SETTINGS_DB_ID = os.getenv('NOTION_DATABASE_ID_SETTINGS') 

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

class User:
    def __init__(self, id, page_id, username, role, password_hash):
        self.id = id; self.page_id = page_id; self.username = username; self.role = role; self.password_hash = password_hash
    def is_active(self): return True
    def get_id(self): return self.id
    def is_authenticated(self): return True
    @staticmethod
    def get(user_id):
        url = f"https://api.notion.com/v1/databases/{USERS_DB_ID}/query"
        query = {"filter": {"property": "UserID", "title": {"equals": user_id}}}
        response = requests.post(url, json=query, headers=HEADERS)
        if response.status_code != 200: print(f"NOTION API ERROR (get): {response.json()}"); return None
        data = response.json()
        if data.get('results'):
            user_data = data['results'][0]; props = user_data['properties']
            return User(id=props['UserID']['title'][0]['text']['content'], page_id=user_data['id'], username=props['Username']['rich_text'][0]['text']['content'], role=props['Role']['select']['name'], password_hash=props['PasswordHash']['rich_text'][0]['text']['content'])
        return None
    @staticmethod
    def get_by_username(username):
        url = f"https://api.notion.com/v1/databases/{USERS_DB_ID}/query"
        query = {"filter": {"property": "Username", "rich_text": {"equals": username}}}
        response = requests.post(url, json=query, headers=HEADERS)
        if response.status_code != 200: print(f"NOTION API ERROR (get_by_username): {response.json()}"); return None
        data = response.json()
        if data.get('results'):
            user_data = data['results'][0]; props = user_data['properties']
            return User(id=props['UserID']['title'][0]['text']['content'], page_id=user_data['id'], username=props['Username']['rich_text'][0]['text']['content'], role=props['Role']['select']['name'], password_hash=props['PasswordHash']['rich_text'][0]['text']['content'])
        return None

def delete_user(user_page_id):
    """Archives a user page in Notion, effectively deleting them."""
    url = f"https://api.notion.com/v1/pages/{user_page_id}"
    payload = {"archived": True}
    response = requests.patch(url, json=payload, headers=HEADERS)
    if response.status_code != 200:
        print(f"NOTION API ERROR (delete_user): {response.json()}")
        return False
    return True

def get_app_setting(setting_name):
    """Fetches a specific setting from the AppSettings database."""
    if not SETTINGS_DB_ID: return None
    url = f"https://api.notion.com/v1/databases/{SETTINGS_DB_ID}/query"
    query = {"filter": {"property": "Setting", "title": {"equals": setting_name}}}
    response = requests.post(url, json=query, headers=HEADERS)
    if response.status_code != 200: return None
    data = response.json()
    if data.get('results'):
        return data['results'][0] 
    return None

def is_signup_enabled():
    """Checks if the SignUpEnabled setting is true."""
    setting = get_app_setting('SignUpEnabled')
    if setting:
        value = setting['properties']['Value']['rich_text'][0]['text']['content']
        return value.lower() == 'true'
    return True 

def set_signup_status(enabled):
    """Updates the SignUpEnabled setting in Notion."""
    setting = get_app_setting('SignUpEnabled')
    if setting:
        page_id = setting['id']
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {
            "properties": {
                "Value": {"rich_text": [{"text": {"content": "true" if enabled else "false"}}]}
            }
        }
        response = requests.patch(url, json=payload, headers=HEADERS)
        if response.status_code != 200:
            print(f"NOTION API ERROR (set_signup_status): {response.json()}")
            return False
        return True
    return False

def get_all_users():
    url = f"https://api.notion.com/v1/databases/{USERS_DB_ID}/query"
    response = requests.post(url, headers=HEADERS)
    if response.status_code != 200: print(f"NOTION API ERROR (get_all_users): {response.json()}"); return []
    data = response.json(); users = []
    if 'results' in data:
        for item in data['results']:
            props = item['properties']
            if props.get('Role') and props['Role'].get('select') and props['Role']['select']['name'] == 'User':
                users.append({'id': props['UserID']['title'][0]['text']['content'], 'page_id': item['id'], 'username': props['Username']['rich_text'][0]['text']['content'], 'role': props['Role']['select']['name']})
    return users
def get_all_users_latest_location():
    all_users = get_all_users()
    latest_locations = []
    for user in all_users:
        url = f"https://api.notion.com/v1/databases/{LOCATIONS_DB_ID}/query"
        query = {"filter": {"property": "User", "relation": {"contains": user['page_id']}}, "sorts": [{"property": "Timestamp", "direction": "descending"}], "page_size": 1}
        response = requests.post(url, json=query, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                props = data['results'][0]['properties']
                latest_locations.append({'username': user['username'], 'latitude': props['Latitude'].get('number'), 'longitude': props['Longitude'].get('number'), 'timestamp': props['Timestamp']['date']['start'], 'battery': props.get('Battery', {}).get('rich_text', [{}])[0].get('text', {}).get('content', 'N/A')})
    return latest_locations
def get_user_location_history(user_page_id, limit=10):
    url = f"https://api.notion.com/v1/databases/{LOCATIONS_DB_ID}/query"
    query = {"filter": {"property": "User", "relation": {"contains": user_page_id}}, "sorts": [{"property": "Timestamp", "direction": "descending"}], "page_size": limit}
    response = requests.post(url, json=query, headers=HEADERS)
    if response.status_code != 200: print(f"NOTION API ERROR (get_user_location_history): {response.json()}"); return []
    data = response.json(); history = []
    if 'results' in data:
        for item in data['results']:
            props = item['properties']
            history.append({'timestamp': props['Timestamp']['date']['start'], 'latitude': props['Latitude'].get('number'), 'longitude': props['Longitude'].get('number'), 'ip_address': props['IPAddress']['rich_text'][0]['text']['content'] if props['IPAddress']['rich_text'] else 'N/A', 'battery': props['Battery']['rich_text'][0]['text']['content'] if props['Battery']['rich_text'] else 'N/A'})
    return history
def get_user_logs_for_export(user_page_id):
    all_logs = []
    url = f"https://api.notion.com/v1/databases/{LOCATIONS_DB_ID}/query"
    query = {"filter": {"property": "User", "relation": {"contains": user_page_id}}, "sorts": [{"property": "Timestamp", "direction": "descending"}]}
    while True:
        response = requests.post(url, json=query, headers=HEADERS)
        if response.status_code != 200: break
        data = response.json()
        all_logs.extend(data.get('results', []))
        if data.get('has_more'): query['start_cursor'] = data.get('next_cursor')
        else: break
    formatted_logs = []
    for item in all_logs:
        props = item['properties']
        device_info_prop = props.get('DeviceInfo')
        device_info_text = 'N/A'
        if device_info_prop and device_info_prop.get('rich_text'):
            device_info_text = device_info_prop['rich_text'][0]['text']['content']
        formatted_logs.append({'Timestamp': props['Timestamp']['date']['start'], 'Latitude': props['Latitude'].get('number'), 'Longitude': props['Longitude'].get('number'), 'IPAddress': props['IPAddress']['rich_text'][0]['text']['content'] if props['IPAddress']['rich_text'] else 'N/A', 'Battery': props['Battery']['rich_text'][0]['text']['content'] if props['Battery']['rich_text'] else 'N/A', 'DeviceInfo': device_info_text})
    return formatted_logs
def log_location(user_page_id, latitude, longitude, ip_address, battery, device_info):
    url = "https://api.notion.com/v1/pages"
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_id = f"{user_page_id.split('-')[0]}-{int(datetime.utcnow().timestamp())}"
    properties_payload = {"LogID": { "title": [{"text": {"content": log_id}}] }, "User": { "relation": [{"id": user_page_id}] }, "Timestamp": { "date": {"start": timestamp} }, "Latitude": { "number": float(latitude) if latitude is not None else 0 }, "Longitude": { "number": float(longitude) if longitude is not None else 0 }, "IPAddress": { "rich_text": [{"text": {"content": str(ip_address)}}] }, "Battery": { "rich_text": [{"text": {"content": str(battery)}}] }, "DeviceInfo": { "rich_text": [{"text": {"content": str(device_info)}}] }}
    new_page_data = {"parent": {"database_id": LOCATIONS_DB_ID}, "properties": properties_payload}
    response = requests.post(url, json=new_page_data, headers=HEADERS)
    if response.status_code != 200: print(f"NOTION API ERROR (log_location): {response.json()}"); return False
    return True
def get_geofences():
    if not GEOFENCES_DB_ID: return []
    url = f"https://api.notion.com/v1/databases/{GEOFENCES_DB_ID}/query"
    response = requests.post(url, headers=HEADERS)
    if response.status_code != 200: return []
    data = response.json()
    zones = []
    for item in data.get('results', []):
        props = item['properties']
        zones.append({'name': props['Name']['title'][0]['text']['content'], 'lat': props['Latitude'].get('number'), 'lon': props['Longitude'].get('number'), 'radius': props['Radius'].get('number')})
    return zones
def check_geofence(lat, lon):
    zones = get_geofences()
    for zone in zones:
        R = 6371e3
        phi1 = math.radians(lat); phi2 = math.radians(zone['lat'])
        delta_phi = math.radians(zone['lat'] - lat); delta_lambda = math.radians(zone['lon'] - lon)
        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        if distance <= zone['radius']: return f"is inside the '{zone['name']}' zone."
    return None
def create_user(username, password_hash):
    if User.get_by_username(username): return None
    url = "https://api.notion.com/v1/pages"
    user_id = f"user-{uuid.uuid4().hex[:6]}"
    new_user_data = {"parent": { "database_id": USERS_DB_ID }, "properties": {"UserID": { "title": [{ "text": { "content": user_id }}]}, "Username": { "rich_text": [{ "text": { "content": username }}]}, "PasswordHash": { "rich_text": [{ "text": { "content": password_hash }}]}, "Role": { "select": { "name": "User" }}}}
    response = requests.post(url, json=new_user_data, headers=HEADERS)
    if response.status_code != 200: print(f"NOTION API ERROR (create_user): {response.json()}"); return None
    return User.get_by_username(username)