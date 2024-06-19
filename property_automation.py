import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os

# Load the CSV file
def load_csv(file_path):
    return pd.read_csv(file_path)

# Deduplicate properties based on Address and Sale Date
def deduplicate_data(data):
    return data.drop_duplicates(subset=['Address', 'Sale Date'], keep='last')

# Get contact info using an API (placeholder function, replace with actual API)
def get_contact_info(address):
    # Replace with actual API request
    response = requests.get(f'https://api.example.com/lookup?address={address}')
    if response.status_code == 200:
        data = response.json()
        return data.get('phone', ''), data.get('email', '')
    return '', ''

# Add contact info to data
def add_contact_info(data):
    data['Seller Phone'] = ''
    data['Seller Email'] = ''
    for index, row in data.iterrows():
        phone, email = get_contact_info(row['Address'])
        data.at[index, 'Seller Phone'] = phone
        data.at[index, 'Seller Email'] = email
    return data

# Format data for PETE
def format_for_pete(data):
    pete_data = pd.DataFrame()
    pete_data['External ID'] = data['Address']
    pete_data['Phase'] = 'Lead'
    pete_data['Status'] = 'New'
    pete_data['Campaign'] = 'Default'
    pete_data['Auction Date'] = data['Sale Date']
    pete_data['Seller'] = data['Defendant']
    pete_data['Full Address'] = data['Address']
    pete_data['Street'] = data['Address']
    pete_data['City'] = data['Municipality']
    pete_data['State'] = 'WI'  # Assuming state is always Wisconsin
    pete_data['Seller Phone'] = data['Seller Phone']
    pete_data['Seller Email'] = data['Seller Email']
    return pete_data

# Save data to CSV
def save_csv(data, file_path):
    data.to_csv(file_path, index=False)

# Upload data to PETE using Selenium
def upload_to_pete(file_path, username, password):
    driver = webdriver.Chrome()
    driver.get('https://pete-login-url.com')
    username_field = driver.find_element_by_name('username')
    password_field = driver.find_element_by_name('password')
    username_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    time.sleep(5)
    driver.get('https://pete-import-url.com')
    upload_field = driver.find_element_by_name('file_upload')
    upload_field.send_keys(file_path)
    upload_field.submit()
    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    input_file = 'sheriffs_data.csv'
    deduplicated_file = 'deduplicated_sheriffs_data.csv'
    contact_info_file = 'contact_info_sheriffs_data.csv'
    pete_file = 'pete_formatted_data.csv'
    username = os.getenv('PETE_USERNAME')
    password = os.getenv('PETE_PASSWORD')

    data = load_csv(input_file)
    deduplicated_data = deduplicate_data(data)
    save_csv(deduplicated_data, deduplicated_file)
    
    data_with_contact_info = add_contact_info(deduplicated_data)
    save_csv(data_with_contact_info, contact_info_file)
    
    pete_data = format_for_pete(data_with_contact_info)
    save_csv(pete_data, pete_file)
    
    upload_to_pete(pete_file, username, password)
