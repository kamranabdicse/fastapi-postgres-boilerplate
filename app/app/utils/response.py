from abc import ABC
from typing import Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import Field
from pydantic.generics import GenericModel
from starlette.responses import Response

from app import utils

T = TypeVar("T")


class ApiResponseHeader(GenericModel, Generic[T], ABC):
    """Header type of APIResponseType"""

    status: int = 0
    message: str = "Successful Operation"
    persianMessage: str = "عملیات موفق"
    messageCode: int = Field(
        ..., description=str(utils.MessageCodes.messages_names)
    )


class PaginatedContent(GenericModel, Generic[T]):
    """Content data type for lists with pagination"""

    data: T
    total_count: int = 0
    limit: int = 100
    offset: int = 0


class APIResponseType(GenericModel, Generic[T]):
    """
    an api response type for using as the api's router response_model
    use this for apis that use our APIResponse class for their output
    """

    header: ApiResponseHeader
    content: T | None


class APIResponse(GenericModel, Generic[T]):
    """
    Custom reponse class for apis
    Adds custom header, messages to reponses
    """

    header: ApiResponseHeader
    content: T | None

    def __new__(
        cls, data: T, *args, msg_code: int = 0, msg_status: int = 0, **kwargs
    ):
        if data:
            if isinstance(data, Response):
                return data
        cls.header = {
            "status": msg_status,
            "message": utils.MessageCodes.messages_names[msg_code],
            "persianMessage": utils.MessageCodes.persian_message_names[
                msg_code
            ],
            "messageCode": msg_code,
        }
        cls.content = data
        return {
            "header": cls.header,
            "content": cls.content,
        }


class APIErrorResponse(JSONResponse):
    """
    Custom error reponse class for apis
    Adds custom header, messages to error reponses
    """

    def __init__(self, data, msg_code=0, msg_status=0, **kwargs):
        self.response_data = {
            "header": {
                "status": msg_status,
                "message": utils.MessageCodes.messages_names[msg_code],
                "persianMessage": utils.MessageCodes.persian_message_names[
                    msg_code
                ],
                "messageCode": msg_code,
            },
            "content": jsonable_encoder(data),
        }
        super().__init__(self.response_data, **kwargs)

    def __new__(cls, *args, **kwargs):
        """
        If response data is an instance of the main Response class
        then return the response without manipulating it to correctly
        process file, streaming and other types of responses passed
        """
        if args:
            if isinstance(args[0], Response):
                return args[0]
        return super().__new__(cls)
