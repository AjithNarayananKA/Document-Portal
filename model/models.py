from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class Metadata(BaseModel):
    Summary:List[str]
    Title:str
    Author:str
    CreatedDate:str
    LastModifiedDate:str
    Publisher:str
    Language:str
    PageCount:Union[int,str] # Can be "Not Available"
    SentimentTone:str