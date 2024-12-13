import csv
import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# ---------------- USER CONFIGURATION ----------------
USERNAME = "XXXXX"
PASSWORD = "XXXXX"
CSV_FILE_PATH = "./movies.csv"  
DATE_FORMAT = "%Y-%m-%d"  
RETRY_COUNT = 3  
CHROME_PROFILE_PATH = "/Users/adithtomalex/Library/Application Support/Google/Chrome/Default"  
EVENT_SELECTION_URL = "https://registration.iffk.in/index.php/Res/eventSelection"
LOGIN_URL = "https://registration.iffk.in"
# ------------------------------------------------------

def get_tomorrow_date_str():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return tomorrow.strftime(DATE_FORMAT)

def read_movies_for_tomorrow(csv_file_path):
    tomorrow_str = get_tomorrow_date_str()
    print(f"Looking for movies on: {tomorrow_str}")  # Debug print
    movies_for_tomorrow = []
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(f"Row: {row}")  # Debug print
            if row.get("Date") == tomorrow_str:
                movies_for_tomorrow.append(row.get("MovieName"))
    return movies_for_tomorrow


def setup_webdriver():
    chrome_options = uc.ChromeOptions()
    # Correctly set user data directory and profile directory
    chrome_options.add_argument(f"--user-data-dir=/Users/adithtomalex/Library/Application Support/Google/Chrome")
    chrome_options.add_argument("--profile-directory=Default")  # Change "Default" to the correct profile name if needed

    # Additional Chrome options
    #chrome_options.add_argument("--no-sandbox")
    #chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.140 Safari/537.36')
    

    # Create Service object for ChromeDriver
    #service = Service("/Users/adithtomalex/Downloads/chromedriver-mac-arm64/chromedriver")

    # Initialize the driver
    driver = uc.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
          Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
          })
        """
    })
    driver.maximize_window()
    return driver


def login(driver, username, password):
    driver.get(LOGIN_URL)
    print("Logging in...")

    # Wait for and enter username
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "vchr_email"))
    ).send_keys(username)
    
    # Wait for and enter password
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "vchr_pass"))
    ).send_keys(password)

    # If a captcha needs to be solved and your extension handles it, wait for it here
    # Adjust sleep or add your logic to wait until captcha is solved
    time.sleep(60)

    # Wait for and click the submit button
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "Submit"))
    ).click()

    # Add a small wait to allow navigation to occur
    #time.sleep(10)

    WebDriverWait(driver, 10).until(EC.url_contains("Accountrecovery/notifications"))

    # For example, checking if you're redirected to the notifications page or if a logout link is present.


def find_movie_link(driver, movie_name):
    # Attempt to find the movie by its name
    try:
        movie_h3 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//h3[contains(text(), '{movie_name}')]"))
        )
        # Check if there's a parent link (the a.card-link ancestor)
        # ancestor::a[@class='card-link']
        anchor = movie_h3.find_element(By.XPATH, "./ancestor::a[@class='card-link']")
        return anchor.get_attribute("href")
    except:
        return None

def attempt_booking(driver, movie_name, movie_url):
    driver.get(movie_url)

    # Click "Book Now"
    # Adjust the selector based on actual button text/structure
    try:
        book_now_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Book Now')]"))
        )
        book_now_button.click()
    except:
        print("Could not find or click the 'Book Now' button.")
        return False

    # Click "Confirm Booking"
    try:
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btn_book_confirm"))
        )
        confirm_button.click()
    except:
        print("Could not find or click the 'Confirm Booking' button.")
        return False

    # After confirmation, the page redirects back to https://registration.iffk.in/index.php/Res/eventSelection
    # Check for success message
    try:
        success_alert = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='alert alert-success text-center']/font/b"))
        )
        success_text = success_alert.text.strip()
        
        # Example success_text:
        # "You have successfully reserved for the Movie Dust / El polvo on 14 December 2024 8:30 pm at SREE PADMANABHA"
        # Verify that the movie name is in the success message
        if movie_name in success_text:
            print(f"Booking successful for: {movie_name}")
            return True
        else:
            print("Success message found, but the movie name did not match.")
            return False

    except:
        print("No success message found after confirmation.")
        return False


def main():
    movies = read_movies_for_tomorrow(CSV_FILE_PATH)
    if not movies:
        print("No movies to book for tomorrow.")
        return

    driver = setup_webdriver()
    try:
        login(driver, USERNAME, PASSWORD)
        driver.get(EVENT_SELECTION_URL)

        for movie_name in movies:
            print(f"Attempting to book movie: {movie_name}")
            link = find_movie_link(driver, movie_name)
            if not link:
                print(f"No booking link found for {movie_name}. Might be full or not listed.")
                continue

            success = False
            for attempt in range(RETRY_COUNT):
                if attempt > 0:
                    print(f"Retrying booking for {movie_name} (Attempt {attempt+1})...")
                if attempt_booking(driver, link):
                    print(f"Successfully booked {movie_name}")
                    success = True
                    break
                else:
                    print(f"Booking attempt {attempt+1} for {movie_name} failed.")
                    # Possibly wait a bit before retrying
                    time.sleep(5)

            if not success:
                print(f"Could not book {movie_name} after {RETRY_COUNT} attempts.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
