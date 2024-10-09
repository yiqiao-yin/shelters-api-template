## 🏠 Shelter API

Welcome to the **Shelter API**! This repository contains the code that powers the Shelter API, which helps locate and connect individuals to nearby shelters based on their unique needs and circumstances. This API is deployed on **Azure** using **Azure Function App** with an HTTP trigger, ensuring a reliable, scalable, and secure way to respond to API requests in real-time.

### 🚀 What is this API for?
The Shelter API is designed to assist individuals in finding appropriate shelter options based on a range of criteria, including location, urgency, duration of stay, and other specific needs. This is particularly useful for community services, NGOs, and local organizations who aim to support people in finding immediate safe housing and essential services.

### 🌐 Deployment Details
This API is hosted using **Azure Function App**, specifically utilizing an HTTP trigger to handle incoming requests. The serverless nature of Azure Function App makes this API cost-efficient, scalable, and ideal for unpredictable workloads. The HTTP trigger facilitates easy integration, allowing users to send GET requests and receive responses containing relevant shelter information.

### 💻 How to Invoke the API?

You can easily invoke this API using *Python* to send a request with relevant details to find shelter options. Below is an example of how you can use Python to interact with the Shelter API:

```python
import requests
import json

# Define the API key and base URL
api_key = "xxx"
base_url = "https://azure-function-app-shelter-api-v2.azurewebsites.net/api/http_trigger"

# Parameters for the API request
param = {
    'city': 'Oakland',
    'zipcode': '94611',
    'sex': 'Male',
    'identity': 'Non-LGBTQ+',
    'experience': 'has-not-experienced-domestic-violence',
    'urgency': 'Today',
    'duration': 'Overnight',
    'needs': 'Food-and-clothing',
    'phone_number': '+15102417855',
    'consent': 'Yes'
}

# Construct the full URL with the parameters
url = f"{base_url}?code={api_key}&city={param['city']}&zipcode={param['zipcode']}&sex={param['sex']}&identity={param['identity']}&experience={param['experience']}&urgency={param['urgency']}&duration={param['duration']}&needs={param['needs']}&phone_number={param['phone_number']}&consent={param['consent']}"

# Send the GET request
try:
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response as a list of dictionaries
        result = response.json()
        if isinstance(result, list):
            for shelter in result:
                print(shelter)
        else:
            print("Unexpected response format. Expected a list of dictionaries.")
    else:
        print(f"Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"An error occurred: {e}")
```

### 📋 Parameter Details
To make sure your request is as effective as possible, below are the parameters you can use:

- **city**: The city where the individual is looking for shelter (e.g., "Oakland").
- **zipcode**: The zip code for more specific location targeting (e.g., "94611").
- **sex**: The gender of the individual (e.g., "Male" or "Female").
- **identity**: Any additional identity details, such as LGBTQ+ or Non-LGBTQ+.
- **experience**: Whether the individual has experienced domestic violence (e.g., "has-experienced-domestic-violence").
- **urgency**: How soon shelter is needed (e.g., "Today").
- **duration**: Expected duration of stay (e.g., "Overnight").
- **needs**: Additional needs such as food, clothing, or medical assistance.
- **phone_number**: Contact number for further communication (e.g., "+15102417855").
- **consent**: Consent for sharing information (e.g., "Yes").

### 🔗 How Does It Work?
- The API uses the parameters provided to match individuals with suitable shelters.
- You can invoke the HTTP-triggered Azure Function by sending a GET request with all necessary parameters.
- The response is a JSON object containing a list of shelters that best fit the provided criteria, including details like address, available resources, and contact information.

### 📞 Example Response
If your request is successful, the response will be a JSON list of available shelters that match your criteria. Here is a sample response format:
```json
[
  {
    "shelter_name": "Oakland Safe Haven",
    "address": "123 Main St, Oakland, CA 94611",
    "phone_number": "+15102345678",
    "available_beds": 5,
    "services": ["Food", "Clothing", "Counseling"]
  },
  {
    "shelter_name": "Harbor House",
    "address": "456 Harbor Blvd, Oakland, CA 94612",
    "phone_number": "+15109876543",
    "available_beds": 2,
    "services": ["Medical Assistance", "Emergency Shelter"]
  }
]
```

### ✨ Why Azure Function App?
Using Azure Function App provides several benefits for deploying this API:
- **Scalability**: Automatically scales to handle increased traffic during times of high demand.
- **Cost-Efficient**: You only pay for the resources you use, making it a budget-friendly solution for non-profits and community services.
- **Flexibility**: The serverless architecture allows easy updates and integration into various applications and workflows.

### 🤖 Future Enhancements
We are constantly working on adding new features to the Shelter API. Some upcoming features include:
- Improved **search filters** for better personalization.
- Adding **POST** support to accept detailed intake forms.
- Integration with **mapping services** for easy navigation to shelters.

### 🙏 Contributions & Feedback
We welcome contributions and suggestions to make the Shelter API better. Feel free to open an issue or submit a pull request to this repository. Together, we can make this API a helpful tool for those in need.

Thank you for your interest in the **Shelter API**! 🛡️✨

