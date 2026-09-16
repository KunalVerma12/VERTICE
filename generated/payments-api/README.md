# payments-api

Payments and billing microservice

## Metadata
- **Owner**: checkout-team
- **Language**: Python
- **Framework**: FastAPI

## Getting Started

### Local Development

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. Run the tests:
   ```bash
   pytest
   ```
