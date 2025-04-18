from fastapi import FastAPI
from pydantic import BaseModel
from linkedinScraper.main import process_company
import pandas as pd

app = FastAPI(title="LinkedIn Scraper API")

# Request schema
class CompanyInput(BaseModel):
    Company: str
    City: str = None
    State: str = None
    Website: str = None

@app.post("/scrape")
def scrape_company(data: CompanyInput):
    row = pd.Series(data.dict())
    result = process_company(row)
    return result