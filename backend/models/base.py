from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AzureTableModel(BaseModel):
    """Base class for Azure Table Storage entity models.

    Provides shared serialization helpers so that every concrete model
    can convert itself to and from the flat dictionary format that the
    Azure SDK expects when reading or writing table entities.

    Azure Table Storage entities are plain dictionaries whose keys are
    strings and whose values are Python primitives (str, int, float,
    bool, datetime).  The two mandatory keys are ``PartitionKey`` and
    ``RowKey``; every other key becomes an ordinary column.

    Subclasses must implement:
        partition_key_field (str): name of the model field that maps to
            ``PartitionKey``.
        row_key_field (str): name of the model field that maps to
            ``RowKey``.
    """

    # Subclasses override these class-level attributes.
    partition_key_field: str = ""
    row_key_field: str = ""

    model_config = {"populate_by_name": True}

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def to_entity(self) -> dict[str, Any]:
        """Serialise the model to an Azure Table Storage entity dict.

        The field nominated by ``partition_key_field`` is emitted as
        ``PartitionKey`` and the field nominated by ``row_key_field`` is
        emitted as ``RowKey``.  All other fields are included under
        their own names.  Fields whose value is ``None`` are omitted so
        that optional columns are not written as explicit nulls.

        Returns:
            dict[str, Any]: A flat dictionary ready to be passed to the
                Azure SDK's ``upsert_entity`` / ``create_entity`` calls.

        Raises:
            ValueError: If ``partition_key_field`` or ``row_key_field``
                have not been set on the subclass.
        """
        if not self.partition_key_field:
            raise ValueError(
                f"{type(self).__name__} must define 'partition_key_field'."
            )
        if not self.row_key_field:
            raise ValueError(
                f"{type(self).__name__} must define 'row_key_field'."
            )

        data = self.model_dump(mode="python", exclude_none=True)

        # Remove the internal class-level sentinel fields so they are
        # never written to the table.
        data.pop("partition_key_field", None)
        data.pop("row_key_field", None)

        entity: dict[str, Any] = {}

        pk_value = data.pop(self.partition_key_field, None)
        rk_value = data.pop(self.row_key_field, None)

        if pk_value is None:
            raise ValueError(
                f"Field '{self.partition_key_field}' (PartitionKey) must not "
                "be None."
            )
        if rk_value is None:
            raise ValueError(
                f"Field '{self.row_key_field}' (RowKey) must not be None."
            )

        entity["PartitionKey"] = str(pk_value)
        entity["RowKey"] = str(rk_value)
        entity.update(data)

        return entity

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> "AzureTableModel":
        """Deserialise an Azure Table Storage entity dict into a model.

        ``PartitionKey`` is mapped back to the field named by
        ``partition_key_field`` and ``RowKey`` is mapped back to the
        field named by ``row_key_field``.  All remaining keys in the
        entity dictionary are passed through as-is.

        Azure SDK metadata keys (those starting with ``odata.`` or the
        ``Timestamp`` / ``etag`` system properties) are silently
        ignored.

        Args:
            entity (dict[str, Any]): The raw entity dictionary returned
                by the Azure SDK.

        Returns:
            AzureTableModel: A fully validated instance of the calling
                subclass.

        Raises:
            ValueError: If ``partition_key_field`` or ``row_key_field``
                have not been set on the subclass.
            pydantic.ValidationError: If the entity data fails model
                validation.
        """
        # cls() is the concrete subclass, so we can read class-level
        # defaults from its model_fields or __class_vars__.
        instance_defaults = cls.model_fields

        pk_field = cls.model_fields.get("partition_key_field")
        rk_field = cls.model_fields.get("row_key_field")

        # Prefer the default values declared on the subclass.
        pk_field_name: str = (
            pk_field.default if pk_field and pk_field.default else ""
        )
        rk_field_name: str = (
            rk_field.default if rk_field and rk_field.default else ""
        )

        if not pk_field_name:
            raise ValueError(
                f"{cls.__name__} must define 'partition_key_field'."
            )
        if not rk_field_name:
            raise ValueError(
                f"{cls.__name__} must define 'row_key_field'."
            )

        # Keys to skip – Azure SDK metadata.
        _SKIP_PREFIXES = ("odata.",)
        _SKIP_KEYS = {"Timestamp", "etag"}

        data: dict[str, Any] = {}
        for key, value in entity.items():
            if key in _SKIP_KEYS:
                continue
            if any(key.startswith(p) for p in _SKIP_PREFIXES):
                continue
            if key == "PartitionKey":
                data[pk_field_name] = value
            elif key == "RowKey":
                data[rk_field_name] = value
            else:
                data[key] = value

        return cls(**data)