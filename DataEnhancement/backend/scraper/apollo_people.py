from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

APOLLO_API_KEY = "8gGyji1LXyY3yu78MYwb5g"
APOLLO_API_URL = "https://api.apollo.io/api/v1/mixed_people/search"

priority_titles = [
    "founder", "co-founder", "cofounder", "ceo", "chief executive officer",
    "president", "coo", "chief operating officer", "cmo", "chief marketing officer",
    "svp", "vp", "director", "manager"
]

def get_priority_rank(title):
    if not title:
        return len(priority_titles) + 1
    title = title.lower()
    for idx, keyword in enumerate(priority_titles):
        if keyword in title:
            return idx
    return len(priority_titles) + 1

def get_best_person(domain):
    params = {
        "person_titles[]": "",
        "person_seniorities[]": ["owner", "founder", "c_suite", "vp", "director", "manager"],
        "q_organization_domains_list[]": domain,
        "contact_email_status[]": ""
    }

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY
    }

    response = requests.post(APOLLO_API_URL, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Apollo API error for {domain}: {response.status_code} {response.text}")

    data = response.json()
    people = data.get("people", [])

    if not people:
        return None

    people_sorted = sorted(people, key=lambda x: get_priority_rank(x.get("title")))
    best_person = people_sorted[0]

    result = {
        "domain": domain,
        "first_name": best_person.get("first_name", ""),
        "last_name": best_person.get("last_name", ""),
        "title": best_person.get("title", ""),
        "email": best_person.get("email", ""),
        "linkedin_url": best_person.get("linkedin_url", ""),
        "phone_number": best_person.get("organization", {}).get("primary_phone", {}).get("sanitized_number", "No phone found"),
        "company": best_person.get("organization", {}).get("name", "")
    }
    return result