from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict

class ErrorDetail(BaseModel):
    code: str = Field(default="UNSPECIFIED_ERROR", description="A unique code identifying the error type.")
    message: str = Field(description="A human-readable message explaining the error.")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional additional context about the error, like field validation issues.")
    # Example context for validation: {"field_errors": [{"field": "email", "message": "Invalid format"}]}

class HTTPErrorResponse(BaseModel):
    errors: List[ErrorDetail] = Field(description="A list containing one or more error details.")

if __name__ == "__main__":
    # Example Usage
    validation_error = HTTPErrorResponse(
        errors=[
            ErrorDetail(
                code="VALIDATION_ERROR",
                message="Input validation failed.",
                context={"field_errors": [{"field": "email", "message": "Email is not valid."}, {"field": "age", "message": "Must be 18 or over."}]}
            )
        ]
    )
    print("Validation Error Example:")
    print(validation_error.model_dump_json(indent=2))

    server_error = HTTPErrorResponse(
        errors=[
            ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred on the server."
            )
        ]
    )
    print("\nInternal Server Error Example:")
    print(server_error.model_dump_json(indent=2))

    not_found_error = HTTPErrorResponse(
        errors=[
            ErrorDetail(
                code="RESOURCE_NOT_FOUND",
                message="The requested resource was not found."
            )
        ]
    )
    print("\nNot Found Error Example:")
    print(not_found_error.model_dump_json(indent=2))
