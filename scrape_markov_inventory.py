"""
Scrape Inventory Cost from Markov Dashboard
Converts n8n workflow to Python function
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


def scrape_markov_inventory(
    company: str,
    email: str,
    password: str,
    dashboard_id: str = "100-ShottysLLC",
    item_id: str = "gridDashboardItem6"
) -> List[Dict]:
    """
    Scrape inventory data from Markov dashboard.

    Args:
        company: Company name for login
        email: Login email
        password: Login password
        dashboard_id: Dashboard ID to fetch data from
        item_id: Dashboard item ID

    Returns:
        List of inventory records with aggregated quantities and values
    """
    base_url = "https://mcs.mar-kov.com/MCS_7-22-00_Dashboard"
    login_url = f"{base_url}/Identity/Account/Login?ReturnUrl=/100-SHOTTYSLLC"
    logout_url = f"{base_url}/Identity/Account/Logout"
    dashboard_api_url = f"{base_url}/api/dashboard/data/DashboardItemGetAction"

    session = requests.Session()

    try:
        # Step 1: Get Login Form to extract CSRF token
        print("Fetching login form...")
        login_form_response = session.get(login_url)
        login_form_response.raise_for_status()

        # Extract the __RequestVerificationToken from the HTML
        soup = BeautifulSoup(login_form_response.text, 'html.parser')
        verifier_input = soup.find('input', {'name': '__RequestVerificationToken'})

        if not verifier_input or 'value' not in verifier_input.attrs:
            raise ValueError("Could not find verification token in login form")

        verification_token = verifier_input['value']
        initial_cookies = login_form_response.cookies

        # Step 2: Login to Markov
        print("Logging in...")
        login_data = {
            'Input.Company': company,
            'Input.Email': email,
            'Input.Password': password,
            '__RequestVerificationToken': verification_token
        }

        login_response = session.post(
            login_url,
            data=login_data,
            allow_redirects=False
        )

        if login_response.status_code not in [302, 200]:
            raise ValueError(f"Login failed with status code: {login_response.status_code}")

        # Step 3: Get Dashboard Data
        print("Fetching dashboard data...")
        dashboard_params = {
            'dashboardId': dashboard_id,
            'itemId': item_id
        }

        dashboard_response = session.get(
            dashboard_api_url,
            params=dashboard_params
        )
        dashboard_response.raise_for_status()
        dashboard_data = dashboard_response.json()

        # Step 4: Transform Data
        print("Transforming data...")
        transformed_data = transform_dashboard_data(dashboard_data)

        # Step 5: Logout
        print("Logging out...")
        session.get(logout_url)

        return transformed_data

    except Exception as e:
        print(f"Error scraping Markov inventory: {e}")
        # Attempt logout even on error
        try:
            session.get(logout_url)
        except:
            pass
        raise
    finally:
        session.close()


def transform_dashboard_data(dashboard_data: Dict) -> List[Dict]:
    """
    Transform raw dashboard data into structured inventory records.

    Args:
        dashboard_data: Raw JSON response from dashboard API

    Returns:
        List of aggregated inventory records
    """
    # Calculate date for yesterday (based on the workflow logic)
    date_now = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Extract data structures from response
    data_storage = dashboard_data.get('ItemData', {}).get('DataStorageDTO', {})
    slices_data = data_storage.get('Slices', [{}])[0].get('Data', {})
    encode_maps = data_storage.get('EncodeMaps', {})

    columns = dashboard_data.get('ViewModel', {}).get('Columns', [])
    column_mappings = [
        {'name': col.get('Caption'), 'dataId': col.get('DataId')}
        for col in columns
    ]

    # Owner mapping
    owner_map = {
        "4": "SHOTTYS",
        "100314": "MARKETING",
        "100374": "IMPACKFUL"
    }

    # Process raw data into objects
    output = []
    for item_key, item_value in slices_data.items():
        if not item_key.startswith('['):
            continue

        try:
            item_arr = json.loads(item_key)
        except json.JSONDecodeError:
            continue

        obj = {}
        for i, value in enumerate(item_arr):
            if value == -1:
                continue

            if i >= len(column_mappings):
                continue

            column = column_mappings[i]
            data_id = column['dataId']

            try:
                if data_id in encode_maps and value < len(encode_maps[data_id]):
                    obj[column['name']] = encode_maps[data_id][value]
            except (KeyError, IndexError):
                continue
        # Map owner if present
        if 'Owner' in obj:
            owner_value = str(obj['Owner'])
            if owner_value in owner_map:
                obj['Owner'] = owner_map[owner_value]


        # Filter by date
        if 'Date' in obj and obj['Date'].startswith(date_now) and obj['Owner'] in ['SHOTTYS', 'IMPACKFUL']:
            output.append(obj)

    # Convert to inventory format and aggregate
    inventory_items = []
    for d in output:
        item_code = d.get('ItemCode', '')
        sublot = d.get('Sublot', '0')
        key = f"{item_code}-{sublot}-{obj['Owner']}-{d.get('Date', '')[:10]}"
        date = d.get('Date', '')[:10]
        qty = float(d.get('Qty', 0)) if d.get('Qty') else 0
        actual_value = float(d.get('ActualValue', 0)) if d.get('ActualValue') else 0
        actual_unit_cost = 0
        if qty and actual_value:
            actual_unit_cost = actual_value / qty
        inventory_items.append({
            'key': key,
            'date': date,
            'item': item_code,
            'area': d.get('Owner'),
            'qty': qty,
            'actual_value': actual_value,
            'actual_unit_cost': actual_unit_cost,
            'gl_group': d.get('GLGroup'),
            'type': d.get('Type', ''),
            'unit': d.get('Unit', '')
        })

    # Aggregate by ID (itemCode-sublot combination)
    aggregated = {}
    for item in inventory_items:
        item_id = item['key']
        if item_id in aggregated:
            aggregated[item_id]['qty'] += item['qty']
            aggregated[item_id]['actual_value'] += item['actual_value']
            aggregated[item_id]['actual_unit_cost'] = aggregated[item_id]['actual_value'] / aggregated[item_id]['qty']

        else:
            aggregated[item_id] = item

    return list(aggregated.values())


if __name__ == "__main__":
    # Example usage
    try:
        inventory_data = scrape_markov_inventory()
        print(f"\nSuccessfully scraped {len(inventory_data)} inventory items")
        print("\nSample records:")
        for item in inventory_data[:3]:
            print(json.dumps(item, indent=2))
    except Exception as e:
        print(f"Failed to scrape inventory: {e}")
