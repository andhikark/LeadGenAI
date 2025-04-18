import logging

# --- State Conversion Utilities ---

def state_abbreviation_to_full(abbr: str) -> str:
    """Convert state abbreviation (e.g., 'NY') to full name ('new york')."""
    state_dict = {
        'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 'AR': 'arkansas',
        'CA': 'california', 'CO': 'colorado', 'CT': 'connecticut', 'DE': 'delaware',
        'FL': 'florida', 'GA': 'georgia', 'HI': 'hawaii', 'ID': 'idaho',
        'IL': 'illinois', 'IN': 'indiana', 'IA': 'iowa', 'KS': 'kansas',
        'KY': 'kentucky', 'LA': 'louisiana', 'ME': 'maine', 'MD': 'maryland',
        'MA': 'massachusetts', 'MI': 'michigan', 'MN': 'minnesota', 'MS': 'mississippi',
        'MO': 'missouri', 'MT': 'montana', 'NE': 'nebraska', 'NV': 'nevada',
        'NH': 'new hampshire', 'NJ': 'new jersey', 'NM': 'new mexico', 'NY': 'new york',
        'NC': 'north carolina', 'ND': 'north dakota', 'OH': 'ohio', 'OK': 'oklahoma',
        'OR': 'oregon', 'PA': 'pennsylvania', 'RI': 'rhode island', 'SC': 'south carolina',
        'SD': 'south dakota', 'TN': 'tennessee', 'TX': 'texas', 'UT': 'utah',
        'VT': 'vermont', 'VA': 'virginia', 'WA': 'washington', 'WV': 'west virginia',
        'WI': 'wisconsin', 'WY': 'wyoming', 'DC': 'district of columbia'
    }
    if not abbr or not isinstance(abbr, str):
        return abbr
    return state_dict.get(abbr.upper(), abbr.lower())


def state_full_to_abbreviation(full_name: str) -> str:
    """Convert full state name (e.g., 'new york') to abbreviation ('NY')."""
    state_dict = {
        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
        'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
        'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
        'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
        'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
        'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
        'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
        'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
        'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
        'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
        'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
        'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
        'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
    }
    if not full_name or not isinstance(full_name, str):
        return full_name
    return state_dict.get(full_name.lower(), full_name)


# --- City Utilities ---

def normalize_city_name(city_name: str) -> str:
    """Normalize known city variants (e.g., 'sf' -> 'san francisco')."""
    if not city_name or not isinstance(city_name, str):
        return city_name

    city_name = city_name.lower().strip()
    city_variants = {
        'san fransisco': 'san francisco',
        'san fran': 'san francisco',
        'sf': 'san francisco',
        'new york city': 'new york',
        'nyc': 'new york',
        'la': 'los angeles',
        'nola': 'new orleans',
        'indy': 'indianapolis',
        'philly': 'philadelphia',
        'saint louis': 'st. louis',
        'saint paul': 'st. paul',
        'ft worth': 'fort worth',
        'ft. worth': 'fort worth',
    }
    return city_variants.get(city_name, city_name)


def city_names_match(expected_city: str, actual_text: str) -> bool:
    """Check if expected city matches part of the actual text, allowing minor variants."""
    if not expected_city or not actual_text:
        return False

    expected = normalize_city_name(expected_city)
    actual_text = actual_text.lower()

    parts = [part.strip() for part in actual_text.split(',')]

    for part in parts:
        if len(part) <= 2:
            continue

        norm_part = normalize_city_name(part)

        if expected == norm_part:
            return True

        if expected in norm_part or norm_part in expected:
            if min(len(expected), len(norm_part)) / max(len(expected), len(norm_part)) > 0.6:
                return True

        match_chars = sum(c1 == c2 for c1, c2 in zip(expected, norm_part))
        max_len = max(len(expected), len(norm_part))
        if max_len > 0 and match_chars / max_len > 0.75:
            return True

    if f" {expected} " in f" {actual_text} ":
        return True

    return False


# --- State Match Utility ---

def state_in_text(expected_state: str, text: str) -> bool:
    """Check if a given state (abbr or full) appears in the text, in various formats."""
    if not expected_state or not text:
        return False

    expected_state = expected_state.lower().strip()
    text = text.lower().strip()

    state_forms = list(set(filter(None, [
        expected_state,
        state_abbreviation_to_full(expected_state),
        state_full_to_abbreviation(expected_state)
    ])))

    logging.debug(f"Checking state match for '{expected_state}' in text: '{text}'")
    logging.debug(f"State forms to match: {state_forms}")

    for form in state_forms:
        if form in text:
            return True
        if f" {form} " in f" {text} ":
            return True
        if f" {form}," in f" {text}" or text.endswith(f" {form}"):
            return True
        if len(form) == 2 and (
            f", {form.upper()}" in text or f" {form.upper()} " in text or text.endswith(f" {form.upper()}")
        ):
            return True

    parts = [part.strip() for part in text.split(',')]
    for part in parts:
        for form in state_forms:
            if form.lower() == part.lower() or (len(form) == 2 and form.upper() == part.upper()):
                return True

    return False
