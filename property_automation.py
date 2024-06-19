import time
import os
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Choose Chrome Browser
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def login_spokeo(username, password):
    driver.get('https://www.spokeo.com/login')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "login_email")))

    email_input = driver.find_element(By.NAME, 'login_email')
    password_input = driver.find_element(By.NAME, 'login_password')
    login_button = driver.find_element(By.XPATH, '//*[@id="login"]/form/button')

    email_input.send_keys(username)
    password_input.send_keys(password)
    login_button.click()

def search_address(address):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))

    search_input = driver.find_element(By.NAME, 'q')
    search_input.clear()
    search_input.send_keys(address)
    search_input.send_keys(Keys.RETURN)

    time.sleep(5)  # Wait for results to load; adjust as necessary

def get_contact_info():
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    phone_numbers = []
    emails = []

    for phone in soup.select('.phone-number'):
        phone_numbers.append(phone.get_text(strip=True))

    for email in soup.select('.email'):
        emails.append(email.get_text(strip=True))

    return phone_numbers, emails

def load_csv(file_path):
    return pd.read_excel(file_path, engine='openpyxl')

def deduplicate_data(data):
    data.drop_duplicates(subset=['Address', 'Sale Date'], inplace=True)
    return data

def add_contact_info(data, username, password):
    login_spokeo(username, password)
    data['Seller Phone'] = ''
    data['Seller Phone2'] = ''
    data['Seller Phone3'] = ''
    data['Seller Phone4'] = ''
    data['Seller Phone5'] = ''
    data['Seller Email'] = ''
    data['Seller Email2'] = ''
    
    for index, row in data.iterrows():
        search_address(row['Address'])
        phones, emails = get_contact_info()
        phone_columns = ['Seller Phone', 'Seller Phone2', 'Seller Phone3', 'Seller Phone4', 'Seller Phone5']
        email_columns = ['Seller Email', 'Seller Email2']
        
        for i, phone in enumerate(phones[:5]):  # Limit to 5 phone numbers
            data.at[index, phone_columns[i]] = phone
        
        for i, email in enumerate(emails[:2]):  # Limit to 2 emails
            data.at[index, email_columns[i]] = email
    
    driver.quit()
    return data

def save_csv(data, file_path):
    data.to_csv(file_path, index=False)

def format_for_pete(data):
    pete_data = pd.DataFrame()
    pete_data['External ID'] = data['Address']
    pete_data['Phase'] = 'Lead'
    pete_data['Status'] = 'New'
    pete_data['Campaign'] = 'Default'
    pete_data['Auction Date'] = data['Sale Date']
    pete_data['Seller'] = data['Defendant']
    pete_data['Full Address'] = data['Address']
    pete_data['Street'] = data['Address'].apply(lambda x: x.split(',')[0])
    pete_data['City'] = data['Municipality']
    pete_data['State'] = 'WI'
    pete_data['Seller Phone'] = data['Seller Phone']
    pete_data['Seller Phone2'] = data['Seller Phone2']
    pete_data['Seller Phone3'] = data['Seller Phone3']
    pete_data['Seller Phone4'] = data['Seller Phone4']
    pete_data['Seller Phone5'] = data['Seller Phone5']
    pete_data['Seller Email'] = data['Seller Email']
    pete_data['Seller Email2'] = data['Seller Email2']
    return pete_data

def upload_to_pete(file_path, username, password):
    # This function should include code to upload the CSV file to PETE
    pass

if __name__ == "__main__":
    input_file = 'sheriffs_data.xlsx'
    deduplicated_file = 'deduplicated_sheriffs_data.csv'
    contact_info_file = 'contact_info_sheriffs_data.csv'
    pete_file = 'pete_formatted_data.csv'
    username = os.getenv('PETE_USERNAME')
    password = os.getenv('PETE_PASSWORD')
    spokeo_username = os.getenv('SPOKEO_USERNAME')
    spokeo_password = os.getenv('SPOKEO_PASSWORD')

    if not os.path.exists(input_file):
        print(f"Error: The input file {input_file} does not exist.")
        exit(1)

    data = load_csv(input_file)
    deduplicated_data = deduplicate_data(data)
    save_csv(deduplicated_data, deduplicated_file)
    
    data_with_contact_info = add_contact_info(deduplicated_data, spokeo_username, spokeo_password)
    save_csv(data_with_contact_info, contact_info_file)
    
    pete_data = format_for_pete(data_with_contact_info)
    save_csv(pete_data, pete_file)
    
    upload_to_pete(pete_file, username, password)
