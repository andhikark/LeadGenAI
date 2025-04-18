import re
import json
import logging

def extract_industry_from_json_data(page_source):
    """
    Extracts the industry name from embedded JSON structures in a LinkedIn page's HTML source.
    Tries multiple known patterns from LinkedIn's JavaScript data layers.
    """
    industry = None

    # Common patterns where industry info is stored
    json_patterns = [
        r'(\{"data":{.*?"industry".*?})',
        r'(voyagerPageJsBeforeHydration.*?"industry".*?})',
        r'("data":{"entityUrn":.*?"industry".*?}})',
        r'("companyPageUrl":.*?,"industryName":"[^"]+?")',
        r'(\{\s*"companyPageUrl".*?"industryV2".*?\})',
        r'("miniCompany":.*?"industries":.*?])',
        r'("industry":\{.*?"name":"[^"]+")',
        r'(\{"\$type":"com\.linkedin\.voyager\.dash\.organization\.Company".*?})'
    ]

    for pattern in json_patterns:
        try:
            matches = re.findall(pattern, page_source, re.DOTALL)
            for match in matches:
                # Pattern: "industryName":"Some Industry"
                if '"industryName":"' in match:
                    match_result = re.search(r'"industryName":"([^"]+)"', match)
                    if match_result:
                        industry = match_result.group(1)
                        logging.info(f"Extracted industry from pattern 'industryName': {industry}")
                        return industry

                # Pattern: "industry":{"name":"Some Industry"}
                if '"industry":{' in match or '"industries":[{' in match:
                    match_result = re.search(r'"name":"([^"]+)"', match)
                    if match_result:
                        industry = match_result.group(1)
                        logging.info(f"Extracted industry from 'industry' object: {industry}")
                        return industry

                # Try parsing miniCompany block if present
                if '"miniCompany":' in match and '"industries":' in match:
                    try:
                        cleaned_json = '{' + match.split('{', 1)[1]
                        if cleaned_json.endswith(','):
                            cleaned_json = cleaned_json[:-1]
                        if not cleaned_json.endswith('}'):
                            cleaned_json += '}'
                        data = json.loads(cleaned_json)
                        if 'industries' in data and isinstance(data['industries'], list):
                            if 'name' in data['industries'][0]:
                                industry = data['industries'][0]['name']
                                logging.info(f"Extracted industry from miniCompany block: {industry}")
                                return industry
                    except json.JSONDecodeError:
                        logging.debug("JSON decode failed while parsing miniCompany block.")
                    except Exception as e:
                        logging.warning(f"Exception while parsing miniCompany JSON: {e}")
        except Exception as e:
            logging.warning(f"Regex search failed for pattern {pattern}: {e}")

    logging.info("No industry found in JSON data.")
    return industry
