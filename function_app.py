import azure.functions as func
import logging

import pandas as pd
import requests
import math
from openai import OpenAI
from datetime import datetime
from datetime import time
from zoneinfo import ZoneInfo
import json
from twilio.rest import Client

import pandas as pd


import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Access the secrets
account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')
openai_api_key = os.getenv('openai_api_key')
openweather_api_key = os.getenv('openweather_api_key')



# Define helper functions
def get_coordinates(zipcode: str, api_key: str) -> list:
    """
    Get the coordinates (latitude and longitude) of an address using the OpenWeather Geocoding API.
    Parameters:
    zipcode (str): The zipcode to geocode.
    api_key (str): Your OpenWeather API key.
    Returns:
    list: A list containing the latitude and longitude of the address.
    """

    base_url = "http://api.openweathermap.org/geo/1.0/zip"
    params = {
        'zip': str(zipcode) + ",US",
        'appid': api_key
    }

    response = requests.get(base_url, params=params)
    data = response.json()
    return [data.get('lat'), data.get('lon')]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers. Use 3956 for miles.
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def get_urgency_score(user, shelter):
    if user == "Today":
        if shelter == "Immidiate": return 0
        if shelter == "High": return 0.75
        if shelter == "Moderate": return 1
    elif user == "In the next few days":
        if shelter == "Immidiate": return 0.25
        if shelter == "High": return 0
        if shelter == "Moderate": return 0.75
    elif user == "In a week or more":
        if shelter == "Immidiate": return 0.75
        if shelter == "High": return 0.25
        if shelter == "Moderate": return 0

def get_duration_score(user, shelter):
    if user == "Overnight":
        if shelter == "Overnight": return 0
        if shelter == "Temporary": return 0.5
        if shelter == "Transitional": return 0.75
        if shelter == "Long-Term": return 1
    elif user == "A month or less":
        if shelter == "Overnight": return 0.5
        if shelter == "Temporary": return 0
        if shelter == "Transitional": return 0.25
        if shelter == "Long-Term": return 0.75
    elif user == "A couple of months":
        if shelter == "Overnight": return 0.75
        if shelter == "Temporary": return 0.25
        if shelter == "Transitional": return 0
        if shelter == "Long-Term": return 0.5
    elif user == "A year or more":
        if shelter == "Overnight": return 1
        if shelter == "Temporary": return 0.75
        if shelter == "Transitional": return 0.5
        if shelter == "Long-Term": return 0

def call_gpt(user_needs, shelter_services, api_key):
    client = OpenAI(api_key = api_key)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Given two variables 'user needs' (the ideal qualities/services of a shelter) and 'shelter services' (the services offered by a shelter), return an integer 0-10 that scores how well the 'shelter services' match the 'user needs' where 0 is the best fit and 10 is the worst fit. IMPORTANT: NO MATTER WHAT, ONLY RETURN THE INTEGER (NO EXTRA WORDS, PUNCTUATION, ETC.)"},
            {"role": "user", "content": f"user_needs: {user_needs}, shelter_services: {shelter_services}"}
        ]
    )

    score = completion.choices[0].message.content.strip()
    return int(score)

def get_time_score(current_datetime, shelter):
    current_day = current_datetime.strftime("%A")

    if current_day not in shelter['Days']:
        return 1

    weekday = current_datetime.weekday()

    current_hour = current_datetime.strftime("%H")
    current_minute = current_datetime.strftime("%M")
    current_time = time(int(current_hour), int(current_minute))

    hour_start = shelter['Hour Start'].split(',')
    minute_start = shelter['Minute Start'].split(',')
    shelter_start = time(int(hour_start[weekday]), int(minute_start[weekday]))

    hour_end = shelter['Hour End'].split(',')
    minute_end = shelter['Minute End'].split(',')
    shelter_end = time(int(hour_end[weekday]), int(minute_end[weekday]))

    if shelter_start < shelter_end:
        if shelter_start <= current_time <= shelter_end: return 0
        else: return 1
    else:
        if current_time >= shelter_start or current_time <= shelter_end: return 0
        else: return 1
#### Ends here ####

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Params
    city = req.params.get('city')
    zipcode = req.params.get('zipcode')
    sex = req.params.get('sex')
    identity = req.params.get('identity')
    experience = req.params.get('experience')
    urgency = req.params.get('urgency')
    duration = req.params.get('duration')
    needs = req.params.get('needs')
    phone_number = req.params.get('phone_number')
    consent = req.params.get('consent')

    # Dataframe
    shelters = pd.read_csv('database.csv')

    # filter city
    shelters = shelters[(shelters['City'] == city)]

    # filter sex
    shelters = shelters[(shelters['Sex'] == sex) | (shelters['Sex'] == 'All')]

    # filter lgbtq
    if identity == 'No':
        shelters = shelters[(shelters['LGBTQ'] == "No")]

    # filter domestic violence
    if experience == "No":
        shelters = shelters[(shelters['Domestic Violence'] == "No")]

    # keep track of which scores are calculated
    scores = []

    # calculate distances between zipcodes
    if zipcode != "Unsure":
        geocoding_api_key = openweather_api_key

        shelters_coordinates = shelters.apply(lambda row: get_coordinates(row['Zip Code'], geocoding_api_key), axis=1).tolist()
        user_coordinates = get_coordinates(zipcode, geocoding_api_key)

        distances = []
        for coordinates in shelters_coordinates:
              distances.append(haversine(coordinates[0], coordinates[1], user_coordinates[0], user_coordinates[1]))

        max_d = max(distances) if (max(distances) != 0) else 1
        shelters['zipcode_score'] = [d / max_d for d in distances]
        scores.append('zipcode_score')

    # get urgency scores
    urgency_scores = shelters.apply(lambda row: get_urgency_score(urgency, row['Urgency']), axis=1).tolist()
    shelters['urgency_score'] = urgency_scores
    scores.append('urgency_score')

    # get duration scores
    duration_scores = shelters.apply(lambda row: get_duration_score(duration, row['Duration']), axis=1).tolist()
    shelters['duration_score'] = duration_scores
    scores.append('duration_score')

    # get services scores
    if needs != "":
        OpenAI_API_KEY = openai_api_key

        services_scores = shelters.apply(lambda row: call_gpt(needs, row['Services'], OpenAI_API_KEY), axis=1).tolist()
        services_scores = [s / 10 for s in services_scores]

        shelters['services_score'] = services_scores
        scores.append('services_score')

    # get time scores
    timezone = ZoneInfo('America/Los_Angeles')
    time_scores = shelters.apply(lambda row: get_time_score(datetime.now(timezone), row), axis=1).tolist()
    if urgency == "Today":
        for i in range(len(scores)):
            shelters[f'time_score_{i}'] = time_scores
            scores.append(f'time_score_{i}')
    elif urgency == "In the next few days":
        shelters['time_score'] = time_scores
        scores.append('time_score')
    elif urgency == "In a week or more":
        pass

    # calcualte cumulative score
    shelters['total_score'] = shelters[scores].sum(axis=1)
    shelters['total_score'] = shelters['total_score'] / len(scores)

    shelters = shelters.sort_values(by='total_score', ascending=True)
    shelters = shelters.head(3)

    # convert pandas df into list of dicts
    shelters = shelters.to_dict(orient='records')

    # text messaging
    if len(phone_number) == 12 and consent == "Yes":
        try:
            account_sid = account_sid
            auth_token = auth_token
            twilio_client = Client(account_sid, auth_token)

            message_body = "Here's some key shelter information from using ShelterSearch today:\n\n"
            for i in range(len(shelters)):
                phone = str(shelters[i]['Phone'])
                message_body += f"{shelters[i]['Organization Name']}: {shelters[i]['Program Name']}\n"
                message_body += f"🕒 Open Hours: {shelters[i]['Open Hours']}\n"
                message_body += f"📍 Address: {shelters[i]['Address']}\n"
                message_body += f"📞 Phone Number: ({phone[1:4]}) {phone[4:7]}-{phone[7:]}\n\n"

            message = twilio_client.messages.create(
                body = message_body,
                from_= "+15107212356",
                to = phone_number
            )
        except: pass

    if shelters:
        # Convert the shelters dictionary to a JSON string
        return func.HttpResponse(
            json.dumps(shelters), 
            mimetype="application/json", 
            status_code=200
        )
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )