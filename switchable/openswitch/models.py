"""SQLAlchemy 2.0 ORM models for Open-Switch."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from openswitch.db import engine


def utc_now() -> datetime:
    return datetime.now(UTC)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base model."""

    pass


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_json: Mapped[str] = mapped_column(Text, nullable=False)
    n_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=1337)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    examples: Mapped[list["Example"]] = relationship(
        "Example", back_populates="dataset", cascade="all, delete-orphan"
    )
    experiments: Mapped[list["Experiment"]] = relationship("Experiment", back_populates="dataset")


class Example(Base):
    __tablename__ = "examples"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    dataset_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str] = mapped_column(Text, nullable=False)
    reference_source: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    train_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    split: Mapped[str] = mapped_column(
        String(16), nullable=False, default="train"
    )  # train, dev, test
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="examples")
    generations: Mapped[list["Generation"]] = relationship("Generation", back_populates="example")

    __table_args__ = (Index("ix_examples_dataset_split", "dataset_id", "split"),)


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id"), nullable=False)
    session_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    git_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="experiments")
    runs: Mapped[list["Run"]] = relationship(
        "Run", back_populates="experiment", cascade="all, delete-orphan"
    )
    finetunes: Mapped[list["FineTune"]] = relationship("FineTune", back_populates="experiment")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="experiment")


class ModelDef(Base):
    __tablename__ = "model_defs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    experiment_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("experiments.id"), nullable=True
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    family: Mapped[str] = mapped_column(String(64), nullable=False)
    license: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="openai_compat")
    price_in_per_mtok: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_out_per_mtok: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_verified_on: Mapped[str | None] = mapped_column(String(32), nullable=True)
    price_source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    experiment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    model_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    est_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="runs")
    generations: Mapped[list["Generation"]] = relationship(
        "Generation", back_populates="run", cascade="all, delete-orphan"
    )


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    example_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("examples.id", ondelete="CASCADE"), nullable=False
    )
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ttft_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    run: Mapped["Run"] = relationship("Run", back_populates="generations")
    example: Mapped["Example"] = relationship("Example", back_populates="generations")
    scores: Mapped[list["Score"]] = relationship(
        "Score", back_populates="generation", cascade="all, delete-orphan"
    )
    judgments: Mapped[list["Judgment"]] = relationship(
        "Judgment", back_populates="generation", cascade="all, delete-orphan"
    )
    human_labels: Mapped[list["HumanLabel"]] = relationship(
        "HumanLabel", back_populates="generation", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("run_id", "example_id", name="uq_run_example"),)


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    generation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("generations.id", ondelete="CASCADE"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    generation: Mapped["Generation"] = relationship("Generation", back_populates="scores")


class Judgment(Base):
    __tablename__ = "judgments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    generation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("generations.id", ondelete="CASCADE"), nullable=False
    )
    judge_model: Mapped[str] = mapped_column(String(128), nullable=False)
    verdict_ab: Mapped[str] = mapped_column(String(16), nullable=False)
    verdict_ba: Mapped[str] = mapped_column(String(16), nullable=False)
    final: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # win, loss, tie, inconsistent, invalid
    rationale_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    generation: Mapped["Generation"] = relationship("Generation", back_populates="judgments")


class HumanLabel(Base):
    __tablename__ = "human_labels"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    generation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("generations.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(32), nullable=False)  # better, worse, tie
    labeler: Mapped[str] = mapped_column(String(128), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    generation: Mapped["Generation"] = relationship("Generation", back_populates="human_labels")


class FineTune(Base):
    __tablename__ = "finetunes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    experiment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("experiments.id"), nullable=False
    )
    base_model: Mapped[str] = mapped_column(String(128), nullable=False)
    method: Mapped[str] = mapped_column(String(64), nullable=False, default="lora")
    hyperparams_json: Mapped[str] = mapped_column(Text, nullable=False)
    train_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    provider_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    time_s: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    result_model_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="finetunes")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    experiment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("experiments.id"), nullable=False
    )
    json_path: Mapped[str] = mapped_column(String(512), nullable=False)
    html_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="reports")


class Session(Base):
    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


async def init_db(engine_override=None) -> None:
    """Create all database tables and apply lightweight column migrations."""
    target_engine = engine_override or engine
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE experiments ADD COLUMN session_hash VARCHAR(64)"))
        except Exception:
            pass  # Already exists
