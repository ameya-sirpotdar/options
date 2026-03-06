from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, field_validator


INVALID_KEY_CHARS_PATTERN = re.compile(r'[/\\#?\x00-\x1f\x7f-\x9f]')


def _validate_azure_table_key(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > 1024:
        raise ValueError(f"{field_name} must not exceed 1024 characters")
    if INVALID_KEY_CHARS_PATTERN.search(value):
        raise ValueError(
            f"{field_name} contains invalid characters for Azure Table Storage keys. "
            "Characters /, \\, #, ?, and control characters (U+0000–U+001F, U+007F–U+009F) "
            "are not allowed."
        )
    return value


class AzureTableModel(BaseModel):
    """
    Base class for Azure Table Storage entity models.

    Subclasses must define PartitionKey and RowKey fields and may
    override to_entity() / from_entity() for custom serialization.

    Azure Table Storage key constraints enforced:
    - Must be non-empty strings
    - Must not exceed 1024 characters
    - Must not contain: / \\ # ? or control characters (U+0000–U+001F, U+007F–U+009F)
    """

    PartitionKey: str
    RowKey: str

    @field_validator("PartitionKey", mode="before")
    @classmethod
    def validate_partition_key(cls, value: Any) -> str:
        return _validate_azure_table_key(str(value) if not isinstance(value, str) else value, "PartitionKey")

    @field_validator("RowKey", mode="before")
    @classmethod
    def validate_row_key(cls, value: Any) -> str:
        return _validate_azure_table_key(str(value) if not isinstance(value, str) else value, "RowKey")

    def to_entity(self) -> dict[str, Any]:
        """
        Serialize the model to a dict suitable for Azure Table Storage.

        Returns a flat dictionary with all fields, ready to be passed
        to the Azure SDK's create_entity / upsert_entity methods.
        """
        return self.model_dump()

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> "AzureTableModel":
        """
        Deserialize an Azure Table Storage entity dict into this model.

        Parameters
        ----------
        entity:
            A dictionary returned by the Azure SDK (e.g. from
            TableClient.get_entity or TableClient.list_entities).

        Returns
        -------
        An instance of the calling subclass populated with the entity data.
        """
        return cls(**entity)

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": False,
        "validate_assignment": True,
    }