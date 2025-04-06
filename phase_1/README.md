# Phase 1 Implementation
### TODO:
1. Make the scraper code recursive by inclusion of zipcode for an area (city/state).
```bash
Input -> Business Industry, geographic location
Output -> List of data objects containing business details (name, industry, address, rating, website, tel.no)
```
2. Build function to get list of all zip codes of an area (city/state).
```bash
Input -> Geographic location (city/state)
Output -> List of zip codes
```

3. Build a function to return company description using a LLM.
```bash
Input -> Name, Location
Output -> LLM Generated Text
```

### Setup Instruction:
1. Clone repo
```bash
git clone https://github.com/CapraeCapital/LeadGenAI.git
```

2. Switch branch
```bash
cd .\LeadGenAI
git switch leadgen/phase-1
```

3. Run init.py within phase_1 directory
```bash
cd .\phase_1
python __init__.py
```
