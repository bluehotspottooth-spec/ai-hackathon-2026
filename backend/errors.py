"""
errors.py: one kind of error for problems the USER should see.

Every part of the backend raises ServiceError with:
  - message: friendly text that is safe to show on screen
  - status:  the HTTP status code main.py sends back
             400 = bad request (e.g. empty or too-noisy recording)
             401 = wrong access code
             404 = appointment not found / already ended
             429 = 20-turn limit reached
             502 = an AI service failed (translation)
"""


class ServiceError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status
