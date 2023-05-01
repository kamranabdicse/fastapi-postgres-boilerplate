from base64 import b64decode, b64encode
from functools import partial
import json
from datetime import date, datetime
from decimal import Decimal

from app.db.base_class import Base

from dateutil import parser

import dataclasses
from collections import defaultdict
from enum import Enum
from pathlib import PurePath
from types import GeneratorType
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE

DATETIME_AWARE = "%m/%d/%Y %I:%M:%S %p %z"
DATE_ONLY = "%m/%d/%Y"

ONE_HOUR_IN_SECONDS = 3600
ONE_DAY_IN_SECONDS = ONE_HOUR_IN_SECONDS * 24
ONE_WEEK_IN_SECONDS = ONE_DAY_IN_SECONDS * 7
ONE_MONTH_IN_SECONDS = ONE_DAY_IN_SECONDS * 30
ONE_YEAR_IN_SECONDS = ONE_DAY_IN_SECONDS * 365

SERIALIZE_OBJ_MAP = {
    str(datetime): parser.parse,
    str(date): parser.parse,
    str(Decimal): Decimal,
    str(bytes): lambda x: b64decode(x.encode()),
}


def object_hook(obj):
    if "_spec_type" not in obj:
        return obj
    _spec_type = obj["_spec_type"]
    if _spec_type not in SERIALIZE_OBJ_MAP:  # pragma: no cover
        raise TypeError(f'"{obj["val"]}" (type: {_spec_type}) is not JSON serializable')
    return SERIALIZE_OBJ_MAP[_spec_type](obj["val"])


def serialize_json(json_dict):
    return json.dumps(
        jsonable_encoder(
            json_dict,
            custom_encoder={
                bytes: lambda x: {
                    "_spec_type": str(bytes),
                    "val": b64encode(x),
                },
            },
            recursion=8,
        )
    )


def deserialize_json(json_str):
    # return json.loads(json_str)
    return json.loads(json_str, object_hook=object_hook)


SetIntStr = Set[Union[int, str]]
DictIntStrAny = Dict[Union[int, str], Any]


def generate_encoders_by_class_tuples(
    type_encoder_map: Dict[Any, Callable[[Any], Any]]
) -> Dict[Callable[[Any], Any], Tuple[Any, ...]]:
    encoders_by_class_tuples: Dict[Callable[[Any], Any], Tuple[Any, ...]] = defaultdict(
        tuple
    )
    for type_, encoder in type_encoder_map.items():
        encoders_by_class_tuples[encoder] += (type_,)
    return encoders_by_class_tuples


encoders_by_class_tuples = generate_encoders_by_class_tuples(ENCODERS_BY_TYPE)


def jsonable_encoder(
    obj: Any,
    include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: Optional[Dict[Any, Callable[[Any], Any]]] = None,
    sqlalchemy_safe: bool = True,
    recursion: int = 10,
) -> Any:
    if recursion is not None:
        recursion -= 1
    if recursion <= 0:
        return None
    custom_encoder = custom_encoder or {}
    if custom_encoder:
        if type(obj) in custom_encoder:
            return custom_encoder[type(obj)](obj)
        else:
            for encoder_type, encoder_instance in custom_encoder.items():
                if isinstance(obj, encoder_type):
                    return encoder_instance(obj)
    if include is not None and not isinstance(include, (set, dict)):
        include = set(include)
    if exclude is not None and not isinstance(exclude, (set, dict)):
        exclude = set(exclude)
    if isinstance(obj, BaseModel):
        encoder = getattr(obj.__config__, "json_encoders", {})
        if custom_encoder:
            encoder.update(custom_encoder)
        obj_dict = obj.dict(
            include=include,  # type: ignore # in Pydantic
            exclude=exclude,  # type: ignore # in Pydantic
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )
        if "__root__" in obj_dict:
            obj_dict = obj_dict["__root__"]
        return jsonable_encoder(
            obj_dict,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            custom_encoder=encoder,
            sqlalchemy_safe=sqlalchemy_safe,
            recursion=recursion,
        )
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, (str, int, float, type(None))):
        return obj
    if isinstance(obj, dict):
        encoded_dict = {}
        for key, value in obj.items():
            if (
                (
                    not sqlalchemy_safe
                    or (not isinstance(key, str))
                    or (not key.startswith("_sa"))
                )
                and (value is not None or not exclude_none)
                and ((include and key in include) or not exclude or key not in exclude)
            ):
                encoded_key = jsonable_encoder(
                    key,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                    recursion=recursion,
                )
                encoded_value = jsonable_encoder(
                    value,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                    recursion=recursion,
                )
                encoded_dict[encoded_key] = encoded_value
        return encoded_dict
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        encoded_list = []
        for item in obj:
            encoded_list.append(
                jsonable_encoder(
                    item,
                    include=include,
                    exclude=exclude,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                    recursion=recursion,
                )
            )
        return encoded_list

    if type(obj) in ENCODERS_BY_TYPE:
        return ENCODERS_BY_TYPE[type(obj)](obj)
    for encoder, classes_tuple in encoders_by_class_tuples.items():
        if isinstance(obj, classes_tuple):
            return encoder(obj)

    errors: List[Exception] = []
    try:
        data = dict(obj)
    except Exception as e:
        errors.append(e)
        try:
            data = vars(obj)
        except Exception as e:
            errors.append(e)
            raise ValueError(errors)
    return jsonable_encoder(
        data,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        custom_encoder=custom_encoder,
        sqlalchemy_safe=sqlalchemy_safe,
        recursion=recursion,
    )
