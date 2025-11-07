class HTTPException(Exception):

	def __init__(self, status: int, message: str) -> None:
		super().__init__(message)
		self.status = status
		self.message = message

class InvalidRequestException(HTTPException):

	def __init__(self, message: str = "Bad Request") -> None:
		super().__init__(400, message)
