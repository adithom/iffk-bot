from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def setup_webdriver():
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir=/Users/adithtomalex/Library/Application Support/Google/Chrome")
    chrome_options.add_argument("profile-directory=Default")  # Change to "Profile 1" or "Profile 2" if needed
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/Users/adithtomalex/Downloads/chromedriver-mac-arm64/chromedriver")  # Update with your ChromeDriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

driver = setup_webdriver()
driver.get("https://www.google.com")
input("Press Enter to close the browser...")
driver.quit()

