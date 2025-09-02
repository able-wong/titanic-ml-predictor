"""
Request models for FastAPI endpoint validation.

These models define the structure and validation rules for incoming API requests.
"""

from pydantic import BaseModel, Field


class PassengerData(BaseModel):
    """
    Passenger data model for survival prediction requests.
    
    All fields are validated according to the Titanic dataset constraints
    and the preprocessing requirements.
    """
    
    pclass: int = Field(
        ..., 
        ge=1, 
        le=3, 
        description="Passenger class (1=First, 2=Second, 3=Third)"
    )
    
    sex: str = Field(
        ..., 
        pattern="^(male|female)$", 
        description="Sex of the passenger"
    )
    
    age: float = Field(
        ..., 
        ge=0, 
        le=120, 
        description="Age of the passenger in years"
    )
    
    sibsp: int = Field(
        ..., 
        ge=0, 
        description="Number of siblings/spouses aboard"
    )
    
    parch: int = Field(
        ..., 
        ge=0, 
        description="Number of parents/children aboard"
    )
    
    fare: float = Field(
        ..., 
        ge=0, 
        description="Fare paid for the ticket"
    )
    
    embarked: str = Field(
        ..., 
        pattern="^(C|Q|S)$", 
        description="Port of embarkation (C=Cherbourg, Q=Queenstown, S=Southampton)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "First Class Female (High Survival)",
                    "summary": "Wealthy female passenger with high survival probability",
                    "value": {
                        "pclass": 1,
                        "sex": "female",
                        "age": 29.0,
                        "sibsp": 0,
                        "parch": 0,
                        "fare": 211.3375,
                        "embarked": "S"
                    }
                },
                {
                    "name": "Third Class Male (Low Survival)",
                    "summary": "Working class male passenger with lower survival probability", 
                    "value": {
                        "pclass": 3,
                        "sex": "male",
                        "age": 22.0,
                        "sibsp": 1,
                        "parch": 0,
                        "fare": 7.25,
                        "embarked": "S"
                    }
                },
                {
                    "name": "Second Class Female with Family",
                    "summary": "Middle class female passenger traveling with family",
                    "value": {
                        "pclass": 2,
                        "sex": "female",
                        "age": 35.0,
                        "sibsp": 1,
                        "parch": 2,
                        "fare": 26.0,
                        "embarked": "C"
                    }
                },
                {
                    "name": "Child Passenger",
                    "summary": "Young passenger with accompanying adults",
                    "value": {
                        "pclass": 2,
                        "sex": "male",
                        "age": 8.0,
                        "sibsp": 0,
                        "parch": 2,
                        "fare": 29.0,
                        "embarked": "Q"
                    }
                }
            ]
        }