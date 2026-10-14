"""Dataset importer supporting JSONL and CSV formats."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from openswitch.datasets.pii import PIIWarning, scan_pii
from openswitch.datasets.provenance import resolve_provenance
from openswitch.datasets.schema import validate_row_schema
from openswitch.datasets.splits import assign_splits
from openswitch.db import session_context
from openswitch.models import Dataset, Example


@dataclass
class ImportedDataset:
    name: str
    sha256: str
    seed: int
    rows: list[dict[str, Any]]
    split_counts: dict[str, int]
    pii_warnings: list[PIIWarning] = field(default_factory=list)
    split_warnings: list[str] = field(default_factory=list)


class DatasetImporter:
    """Imports, validates, splits, and guards datasets."""

    def __init__(
        self,
        seed: int = 1337,
        train_pct: float = 0.6,
        dev_pct: float = 0.1,
        max_rows: int = 200,
        attestation_granted: bool = False,
    ):
        self.seed = seed
        self.train_pct = train_pct
        self.dev_pct = dev_pct
        self.max_rows = max_rows
        self.attestation_granted = attestation_granted

    def import_from_bytes(
        self,
        raw_bytes: bytes,
        filename: str,
        name: str | None = None,
    ) -> ImportedDataset:
        """Parse, validate, and process dataset from raw bytes."""
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        dataset_name = name or Path(filename).stem

        # Decode UTF-8
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Dataset file '{filename}' must be UTF-8 encoded: {e}") from e

        if filename.endswith(".csv"):
            raw_rows = self._parse_csv(content)
        elif filename.endswith((".jsonl", ".ndjson", ".json")):
            raw_rows = self._parse_jsonl(content)
        else:
            raise ValueError(
                f"Unsupported dataset format '{filename}'. Must be .jsonl, .json, or .csv."
            )

        if not raw_rows:
            raise ValueError("Dataset file contains 0 valid rows.")

        if len(raw_rows) > self.max_rows:
            raise ValueError(
                f"Dataset contains {len(raw_rows)} rows, exceeding maximum limit of {self.max_rows}."
            )

        # Validate schema and resolve provenance row by row
        processed_rows: list[dict[str, Any]] = []
        validation_errors: list[str] = []

        for line_num, row in enumerate(raw_rows, start=1):
            # Check schema conformance
            try:
                validate_row_schema(row, line_number=line_num)
            except Exception as e:
                validation_errors.append(str(e))
                continue

            # Resolve provenance
            try:
                source, train_allowed = resolve_provenance(
                    source=row.get("reference_source"),
                    explicit_train_allowed=row.get("train_allowed"),
                    attestation_granted=self.attestation_granted,
                    line_number=line_num,
                )
                row["reference_source"] = source
                row["train_allowed"] = train_allowed
            except Exception as e:
                validation_errors.append(str(e))
                continue

            processed_rows.append(row)

        if validation_errors:
            raise ValueError(
                f"Dataset validation failed with {len(validation_errors)} error(s):\n"
                + "\n".join(validation_errors[:10])
                + (
                    f"\n... and {len(validation_errors) - 10} more"
                    if len(validation_errors) > 10
                    else ""
                )
            )

        # Deterministic splitting
        rows_with_splits, split_counts, split_warnings = assign_splits(
            rows=processed_rows,
            seed=self.seed,
            train_pct=self.train_pct,
            dev_pct=self.dev_pct,
        )

        # PII scan
        pii_warnings = scan_pii(rows_with_splits)

        return ImportedDataset(
            name=dataset_name,
            sha256=sha256_hash,
            seed=self.seed,
            rows=rows_with_splits,
            split_counts=split_counts,
            pii_warnings=pii_warnings,
            split_warnings=split_warnings,
        )

    def import_from_file(self, file_path: str | Path, name: str | None = None) -> ImportedDataset:
        p = Path(file_path)
        with open(p, "rb") as f:
            data = f.read()
        return self.import_from_bytes(data, filename=p.name, name=name)

    def _parse_jsonl(self, content: str) -> list[dict[str, Any]]:
        rows = []
        lines = content.strip().splitlines()
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                rows.append(json.loads(line_str))
            except json.JSONDecodeError as e:
                raise ValueError(f"Line {idx} is invalid JSON: {e}") from e
        return rows

    def _parse_csv(self, content: str) -> list[dict[str, Any]]:
        rows = []
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            raise ValueError("CSV file has empty header.")

        for idx, r in enumerate(reader, start=2):
            # Clean CSV cell injection characters if present
            row_dict: dict[str, Any] = {}
            for k, v in r.items():
                if v is None:
                    continue
                v_clean = v.strip()
                # Remove CSV formula escaping prefixes if present
                if v_clean.startswith(("\t", "'")):
                    v_clean = v_clean[1:]
                row_dict[k.strip()] = v_clean

            # Type conversion for CSV boolean fields
            if "train_allowed" in row_dict:
                val = str(row_dict["train_allowed"]).lower()
                row_dict["train_allowed"] = val in ("true", "1", "yes")

            rows.append(row_dict)
        return rows

    async def save_to_db(
        self,
        session: AsyncSession,
        imported: ImportedDataset,
        task_dict: dict[str, Any] | None = None,
    ) -> Dataset:
        """Persist imported dataset and examples to SQLite."""
        task_str = json.dumps(task_dict or {"name": imported.name, "type": "unspecified"})
        dataset_obj = Dataset(
            name=imported.name,
            task_json=task_str,
            n_rows=len(imported.rows),
            sha256=imported.sha256,
            seed=imported.seed,
        )
        session.add(dataset_obj)
        await session.flush()

        example_objs = []
        for idx, r in enumerate(imported.rows):
            inp = r["input"]
            inp_str = json.dumps(inp) if isinstance(inp, list) else str(inp)
            meta_str = json.dumps(r.get("meta")) if r.get("meta") else None

            ex = Example(
                dataset_id=dataset_obj.id,
                idx=idx,
                system_prompt=r.get("system_prompt"),
                input=inp_str,
                reference=str(r["reference"]),
                reference_source=r["reference_source"],
                train_allowed=r["train_allowed"],
                split=r["split"],
                meta_json=meta_str,
            )
            example_objs.append(ex)

        session.add_all(example_objs)
        await session.commit()
        return dataset_obj


async def import_dataset_from_file(
    file_path: Path,
    dataset_name: str,
    seed: int = 1337,
    attest_closed_training: bool = False,
) -> Dataset:
    """Convenience helper to import and persist a dataset from file path."""
    importer = DatasetImporter(seed=seed, attestation_granted=attest_closed_training)
    raw_bytes = file_path.read_bytes()
    imported = importer.import_from_bytes(
        raw_bytes=raw_bytes, filename=file_path.name, name=dataset_name
    )
    async with session_context() as session:
        return await importer.save_to_db(session, imported)
