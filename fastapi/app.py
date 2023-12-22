import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional

load_dotenv()

connectionString = os.getenv("CONNECTION_STRING") or os.environ["CONNECTION_STRING"]

app = FastAPI()

# Create an engine instance
engine = create_engine(connectionString)

# calculation_data table class in SQLModel
class CalculationData(SQLModel, table=True):
    category: str = Field(primary_key=True)
    margin_curveA: float
    margin_curveB: float
    ci_a_lower: float
    ci_a_upper: float
    ci_b_lower: float
    ci_b_upper: float

class PriceData(SQLModel, table=True):
    id: int = Field(primary_key=True)
    country_code: str
    category: str
    item_code: str
    date: str
    qty: int
    cogs: float
    sell_price: float

class MarginConfiguration(SQLModel, table=True):
    id: int = Field(primary_key=True)
    key: str
    value: float

# Request Model
# Request model for the price suggestion endpoint
class PriceSuggestionRequest(BaseModel):
    category: str
    item_code: str
    cogs: float

# Response model for the price suggestion endpoint
class PriceSuggestionResponse(BaseModel):
    category: str
    item_code: str
    cogs: float
    suggested_price: float

# Request Response
class CategoryResponse(BaseModel):
    category: str

class PriceDataResponse(BaseModel):
    country_code: str
    category: str
    item_code: str
    date: str
    qty: int
    cogs: float
    sell_price: float


# Helper function to get margin data from the database
def get_margin_data(category: str):
    # Create a Session
    with Session(engine) as session:
        statement = select(CalculationData).where(CalculationData.category == category)
        data = session.exec(statement).first()
        if data:
            return data
        else:
            raise HTTPException(status_code=404, detail="Category not found")

@app.get("/")
async def root():
    return {"message": "Hello from API"}

# Endpoint to get available categories
@app.get("/categories")
async def get_categories():
    # Create a Session
    with Session(engine) as session:
        statement = select(CalculationData.category).distinct()
        data = session.exec(statement).all()
        responses = []
        if data:
            for item in data:
                responses.append(CategoryResponse(category=item))
            return responses
            # return data
        else:
            raise HTTPException(status_code=404, detail="No categories found")


# Endpoint to get price suggestions
@app.post("/price_suggestion", response_model=List[PriceSuggestionResponse])
async def get_price_suggestion(requests: List[PriceSuggestionRequest], confident: Optional[str] = "default"):
    responses = []
    for request in requests:
        margin_data = get_margin_data(request.category)
        # Check if confident parameter is provided and select the appropriate calculation method
        if confident is None:
            confident = 'default'
            
        suggested_price = calculate_price_with_confidence(
            request.cogs, margin_data.margin_curveA, margin_data.margin_curveB, 
            margin_data.ci_a_lower, margin_data.ci_a_upper, margin_data.ci_b_lower, margin_data.ci_b_upper, 
            strategy=confident
        )            

        # Append the result to the responses list
        responses.append(PriceSuggestionResponse(category=request.category, item_code=request.item_code, cogs=request.cogs, suggested_price=suggested_price))

    return responses


# Endpoint to get all price data
@app.get("/price_data", response_model=List[PriceDataResponse])
async def get_price_data(limit: Optional[int] = 10, offset: Optional[int] = 0):
    # Create a Session
    with Session(engine) as session:
        statement = select(PriceData).limit(limit).offset(offset).order_by(PriceData.id)
        data = session.exec(statement).all()
        if data:
            return data
        else:
            raise HTTPException(status_code=404, detail="No price data found")

# Function for calculating price based on the provided formula
def calculate_price(cogs: float, margin_curveA: float, margin_curveB: float) -> float:
    # Calculate the suggested selling price using the formula
    suggested_price = margin_curveA * (cogs ** margin_curveB)
    return suggested_price


def calculate_price_with_confidence(cogs, margin_curveA, margin_curveB, ci_a_lower, ci_a_upper, ci_b_lower, ci_b_upper, strategy='default'):
    margin_min = 0.06
    margin_max = 0.20
    
    if strategy == 'conservative':
        # Use the lower bound of A and the upper bound of B
        A = ci_a_lower
        B = ci_b_upper
    elif strategy == 'aggressive':
        # Use the upper bound of A and the lower bound of B
        A = ci_a_upper
        B = ci_b_lower
    elif strategy == 'average':
        # Use the average of the bounds
        A = (ci_a_lower + ci_a_upper) / 2
        B = (ci_b_lower + ci_b_upper) / 2
    else:
        # Default to using the estimated parameters without confidence intervals
        A = margin_curveA
        B = margin_curveB

    suggested_price = A * (cogs ** B)
    
    # logic to check if suggested price is < margin_min use margin_min else if suggested price is > margin_max use margin_max else use suggested price
    if suggested_price < margin_min:
        suggested_price = cogs / (1 - margin_min)
    elif suggested_price > margin_max:
        suggested_price = cogs / (1 - margin_max)
    else:
        suggested_price = suggested_price
    
    
    return suggested_price
