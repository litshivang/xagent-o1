"""
Schema definition for AI Travel Agent
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class TripInquiry(BaseModel):
    """Pydantic model for validating and formatting trip inquiry data"""
    
    num_travelers: Optional[int] = Field(None, description="Total number of travelers")
    num_adults: Optional[int] = Field(None, description="Number of adult travelers")
    num_children: Optional[int] = Field(None, description="Number of child travelers")
    destinations: List[str] = Field(default_factory=list, description="List of travel destinations")
    start_date: Optional[str] = Field(None, description="Trip start date")
    end_date: Optional[str] = Field(None, description="Trip end date")
    duration_nights: Optional[int] = Field(None, description="Number of nights for the trip")
    hotel_preferences: Optional[str] = Field(None, description="Hotel category preferences")
    meal_preferences: Optional[str] = Field(None, description="Meal plan preferences")
    activities: List[str] = Field(default_factory=list, description="List of desired activities")
    needs_flight: Optional[bool] = Field(None, description="Whether flights are required")
    needs_visa: Optional[bool] = Field(None, description="Whether visa assistance is needed")
    needs_insurance: Optional[bool] = Field(None, description="Whether travel insurance is needed")
    budget: Optional[str] = Field(None, description="Budget information")
    departure_city: Optional[str] = Field(None, description="City of departure")
    special_requests: Optional[str] = Field(None, description="Special requests or requirements")
    guide_language: Optional[str] = Field(None, description="Preferred guide language")
    deadline: Optional[str] = Field(None, description="Response deadline requested by customer (e.g., 'reply tomorrow', 'asap', 'within 2 days')")
    
    # Additional fields for tracking
    customer_name: Optional[str] = Field(None, description="Customer name")
    contact_info: Optional[str] = Field(None, description="Contact information")
    file_name: Optional[str] = Field(None, description="Source file name")
    processing_status: Optional[str] = Field(None, description="Processing status")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    extraction_method: Optional[str] = Field(None, description="Primary extraction method used")
    
    class Config:
        """Pydantic configuration"""
        extra = "forbid"  # Forbid extra fields
        validate_assignment = True  # Validate on assignment