from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/search"
APOLLO_ENRICH_URL = "https://api.apollo.io/api/v1/people/match"

priority_titles = [
    "founder",
    "co-founder",
    "cofounder",
    "ceo",
    "chief executive officer",
    "president",
    "coo",
    "chief operating officer",
    "cmo",
    "chief marketing officer",
    "svp",
    "vp",
    "director",
    "manager",
]


def get_priority_rank(title):
    if not title:
        return len(priority_titles) + 1
    title = title.lower()
    for idx, keyword in enumerate(priority_titles):
        if keyword in title:
            return idx
    return len(priority_titles) + 1


def enrich_person(first_name, last_name, domain):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY,
    }

    params = {
        "first_name": first_name,
        "last_name": last_name,
        "domain": domain,
        "reveal_personal_emails": "true",
        "reveal_phone_number": "false",
    }

    response = requests.post(APOLLO_ENRICH_URL, headers=headers, params=params)
    print(response.json())
    if response.status_code != 200:
        return None

    return response.json().get("person", {})


def find_best_person(domain):
    params = {
        "person_titles[]": "",
        "person_seniorities[]": ["owner", "founder", "c_suite", "vp", "director", "manager"],
        "q_organization_domains_list[]": domain,
        "contact_email_status[]": "",
    }

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY,
    }

    response = requests.post(APOLLO_SEARCH_URL, headers=headers, params=params)
    if response.status_code != 200:
        return None

    data = response.json()
    people = data.get("people", [])

    if not people:
        return None

    people_sorted = sorted(people, key=lambda x: get_priority_rank(x.get("title")))
    best_person = people_sorted[0]

    # --- Try to enrich ---
    enriched = enrich_person(
        first_name=best_person.get("first_name", ""),
        last_name=best_person.get("last_name", ""),
        domain=domain,
    )

    # --- Combine original + enriched ---
    combined_result = {
        "company": best_person.get("organization", {}).get("name", ""),
        "domain": domain,
        "first_name": best_person.get("first_name", ""),
        "last_name": best_person.get("last_name", ""),
        "title": best_person.get("title", ""),
        "linkedin_url": best_person.get("linkedin_url", ""),
        "email": best_person.get("email", ""),
        "phone_number": best_person.get("organization", {})
        .get("primary_phone", {})
        .get("sanitized_number", "No phone found"),
    }

    # Override with enriched fields if available
    if enriched:
        if enriched.get("email"):
            combined_result["email"] = enriched["email"]
        if enriched.get("linkedin_url"):
            combined_result["linkedin_url"] = enriched["linkedin_url"]
        if enriched.get("phone_number"):
            combined_result["phone_number"] = enriched["phone_number"]

    return combined_result
