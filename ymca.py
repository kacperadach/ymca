import logging
import os
from time import sleep
from datetime import datetime
import json
from functools import partial

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_PATH = os.path.dirname(__file__)

logger = logging.getLogger('ymca')
hdlr = logging.FileHandler(os.path.join(BASE_PATH, 'ymca.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

POOL_URL = 'https://outlook.office365.com/owa/calendar/ParkwayIndoorPool@ymcaboston.org/bookings/'
LAP_SWIM_NAME = 'Lap Swim'

FITNESS_URL = 'https://outlook.office365.com/owa/calendar/ParkwayFitnessCenter@ymcaboston.org/bookings/'
FREE_WEIGHTS_NAME = 'Free Weights'

KACPER = 'Kacper'
ALEX = 'Alex'

def kacper_time(dt):
    if dt.weekday() >= 5:
        return False

    if dt.hour == 8 and dt.minute >= 30:
        return True

    # Monday
    if dt.weekday() == 0:
        if dt.hour == 11 and dt.minute >= 30:
            return True
        elif dt.hour == 12 and dt.minute <= 15:
            return True
    # Tuesday
    elif dt.weekday == 1:
        if dt.hour == 11 and dt.minute <= 30:
            return True
    # Wednesday
    elif dt.weekday == 2:
        if dt.hour == 11 and dt.minute >= 30:
            return True
        elif dt.hour == 12 and dt.minute <= 45:
            return True
    # Thursday
    elif dt.weekday == 3:
        if dt.hour == 11 and dt.minute >= 30:
            return True
        elif dt.hour == 12:
            return True
    # Friday
    elif dt.weekday == 4:
        if dt.hour == 11 and dt.minute >= 30:
            return True
        elif dt.hour == 12:
            return True
    else:
        return False


def alex_time(dt):
    if dt.weekday == 2:
        return False

    if dt.hour == 11 and dt.minute >= 30:
        return True
    elif dt.hour == 12 and dt.minute <= 30:
        return True
    else:
        return False


def book(url, workout_name, name):
    logger.info('Attempting to schedule {} for {}'.format(workout_name, name))
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(executable_path=os.path.join(BASE_PATH, "webdriver/chromedriver_linux"), options=chrome_options)
    driver.get(url)
    sleep(1)

    workout_label = None
    workout_labels = driver.find_elements_by_tag_name("label")
    for label in workout_labels:
        if workout_name in label.text:
            workout_label = label

    if workout_label is None:
        raise Exception("Could not find workout: " + workout_name)

    workout_label.click()
    sleep(1)

    calendar = driver.find_element_by_class_name('dates')
    bookable_dates = calendar.find_elements_by_class_name('bookable')

    booking_selected = False

    for bookable_date in bookable_dates:
        if booking_selected is True:
            break

        date_string = bookable_date.get_attribute('data-value')
        bookable_date.click()

        sleep(0.1)
        time_picker = driver.find_element_by_class_name("timePicker")
        time_slots = time_picker.find_elements_by_tag_name('li')
        for slot in time_slots:
            time_string = slot.find_element_by_tag_name('span').text
            dt = datetime.strptime(date_string.split('T')[0] + ' ' + time_string, '%Y-%m-%d %I:%M %p')
            logger.info('Available workout: {}'.format(dt.strftime('%Y-%m-%d %I:%M %p')))
            time_func = None
            if name == KACPER:
                time_func = partial(kacper_time, dt)
            elif name == ALEX:
                time_func = partial(alex_time, dt)

            if time_func is not None and time_func():
                logger.info('Selected workout: {}'.format(dt.strftime('%Y-%m-%d %I:%M %p')))
                slot.click()
                booking_selected = True
                break

    if booking_selected is False:
        logger.info('No booking selected')
        return

    user = None
    with open(os.path.join(BASE_PATH, 'users.json'), 'r') as f:
        user_json = json.load(f)
        if name in user_json.keys():
            user = user_json[name]

    if user is None:
        raise Exception('Could not find user {} in users.json'.format(name))

    customer_details = driver.find_element_by_class_name('customerDetails')

    inputs = customer_details.find_elements_by_tag_name('input')
    for input in inputs:
        field = input.get_attribute('aria-label')

        if field == 'Name':
            input.send_keys(name)
        elif 'Email' in field:
            input.send_keys(user['email'])
        elif 'Phone' in field:
            input.send_keys(user['phone'])
        elif 'address' in field:
            input.send_keys(user['address'])

    question_list = driver.find_element_by_class_name('questionList')
    questions = question_list.find_elements_by_tag_name('select')
    for question in questions:
        for option in question.find_elements_by_tag_name('option'):
            if option.text == 'Yes':
                option.click()
                break

    driver.find_element_by_class_name('bookButton').click()
    logger.info('Submitted reservation')
    driver.quit()


book(FITNESS_URL, FREE_WEIGHTS_NAME, KACPER)
