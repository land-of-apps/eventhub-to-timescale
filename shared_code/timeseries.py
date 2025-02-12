from enum import Enum
from typing import Any, List


class PayloadType(Enum):
    """Enum for the types of payload that can be sent to TimescaleDB"""

    NUMBER: str = "number"
    STRING: str = "string"
    BOOLEAN: str = "boolean"
    GEOGRAPHY: str = "geography"


def create_atomic_record(
    source_timestamp: str,
    measurement_subject: str,
    measurement_publisher: str,
    measurement_of: str,
    measurement_value: Any,
    measurement_data_type: PayloadType,
    correlation_id: str = None,
) -> dict[str, Any]:
    """Creates a record in the format expected by the TimescaleDB publisher
    Args:
        timestamp (str): timestamp in ISO format with timezone
        subject (str): subject of the record
        payload (Any): payload of the record
        payload_type (PayloadType): type of the payload
    Returns:
        dict: record in the format expected by TimescaleDB
    """
    return {
        "timestamp": source_timestamp,
        "measurement_subject": measurement_subject,
        "measurement_publisher": measurement_publisher,
        "measurement_of": measurement_of,
        "measurement_value": measurement_value,
        "measurement_data_type": measurement_data_type.value,
        "correlation_id": correlation_id,
    }


def create_record_recursive(
    payload: dict,
    records: List,
    timestamp: str,
    correlation_id: str,
    measurement_publisher: str,
    measurement_subject: str,
    ignore_keys: list = None,
    measurement_of_prefix: str = None,
) -> List[dict[str, Any]]:
    """recursively creates records in the format expected by the TimescaleDB publisher
    Args:
        payload (dict): payload of the record to be parsed
        records (Array[TimescaleRecord]): list of records to be returned
        timestamp (str): timestamp in ISO format with timezone
        correlation_id (str): unique id for the record set
        measurement_publisher (str): publisher of the record
        measurement_subject (str): subject of the record
        ignore_keys (list): list of keys to ignore (also will not be recursed)
        measurement_of_prefix (str): prefix to add to the measurement_of field
    Returns:
        dict: record in the format expected by TimescaleDB
    """
    # if the payload is None or empty, return an empty list
    if payload is None or not payload:
        return records
    for key in payload:
        if ignore_keys is None or key not in ignore_keys:
            if isinstance(payload[key], dict):
                create_record_recursive(
                    payload=payload[key],
                    records=records,
                    timestamp=timestamp,
                    correlation_id=correlation_id,
                    measurement_publisher=measurement_publisher,
                    measurement_subject=measurement_subject,
                    ignore_keys=ignore_keys,
                    measurement_of_prefix=measurement_of_prefix,
                )
            else:
                records.append(
                    create_atomic_record(
                        source_timestamp=timestamp,
                        measurement_publisher=measurement_publisher,
                        measurement_subject=measurement_subject,
                        measurement_of=(key
                                        if measurement_of_prefix is None
                                        else f"{measurement_of_prefix}_{key}"),
                        measurement_value=payload[key],
                        measurement_data_type=get_record_type(payload[key]),
                        correlation_id=correlation_id,
                    )
                )
    return records


def get_record_type(payload):
    """Gets the type of the payload and maps it to the PayloadType enum.
       This is important as we store different types of data in different columns in the database.

    Args:
        payload (Any): payload of the record to be parsed

    Returns:
        PayloadType: type of the payload

    Raises:
        TypeError: If the payload type is not recognized or if a list payload is not a coordinate pair.
    """
    if isinstance(payload, str):
        return PayloadType.STRING
    elif type(payload) == type(True):  # noqa E721
        return PayloadType.BOOLEAN
    elif isinstance(payload, (int, float)):
        return PayloadType.NUMBER
    elif isinstance(payload, list):
        if len(payload) == 2 and all(isinstance(x, (int, float)) for x in payload):
            return PayloadType.GEOGRAPHY
        else:
            raise TypeError(f"List is not a valid coordinate pair: {payload}")
    else:
        raise TypeError(f"Unknown payload type: {type(payload).__name__}")
