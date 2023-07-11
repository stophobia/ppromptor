import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from dataclasses_json import dataclass_json
from langchain.prompts import PromptTemplate
from ppromptor.utils import bulletpointize
from sqlalchemy import JSON, Column, ForeignKey, Table
from sqlalchemy.orm import (DeclarativeBase, Mapped, MappedAsDataclass,
                            mapped_column, relationship)


class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""


class PromptCandidate(Base):
    __tablename__ = "prompt_candidate"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    role: Mapped[str] = mapped_column()
    goal: Mapped[str] = mapped_column()
    guidelines: Mapped[List[str]] = Column(JSON)
    constraints: Mapped[List[str]] = Column(JSON)
    examples: Mapped[List[str]] = Column(JSON)
    output_format: Mapped[str] = mapped_column(default="")

    @property
    def prompt(self):
        guidelines = bulletpointize(self.guidelines)
        constraints = bulletpointize(self.constraints)

        prompt_str = (f"You are a {self.role}. Your job is to {self.goal}.",
                      "Always follow below guidelines:",
                      "",
                      "Guideline:",
                      f"{guidelines}",
                      "",
                      "Strickly follow below constraints:",
                      "",
                      "Constraints:",
                      f"{constraints}",
                      "",
                      "Input:",
                      "{input}",
                      "",
                      "Now, generate output accordingly:")

        print(prompt_str)
        return PromptTemplate(template=textwrap.dedent("\n".join(prompt_str)),
                              input_variables=["input"])


@dataclass_json
class IOPair(Base):
    __tablename__ = "io_pair"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    input: Mapped[str] = mapped_column()
    output: Mapped[str] = mapped_column()

    def __str__(self):
        return f"Input: {self.input}; Output: {self.output}"


class EvalResult(Base):
    __tablename__ = "eval_result"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    evaluator_name: Mapped[str] = mapped_column()

    prompt: Mapped["PromptCandidate"] = relationship()
    data: Mapped["IOPair"] = relationship()

    prediction: Mapped[str] = mapped_column()

    scores: Mapped[Dict[str, float]] = Column(JSON)
    llm_params: Mapped[Dict[str, Any]] = Column(JSON)

    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompt_candidate.id"),
                                           default=None)
    data_id: Mapped[int] = mapped_column(ForeignKey("io_pair.id"),
                                         default=None)

    def __str__(self):
        return (f"Input: [{self.data.input}],"
                f" Prediction: [{self.prediction}],"
                f" Answer: [{self.data.output}]")


class Recommendation(Base):
    __tablename__ = "recommendation"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    thoughts: Mapped[str] = mapped_column()
    revision: Mapped[str] = mapped_column()

    role: Mapped[str] = mapped_column()
    goal: Mapped[str] = mapped_column()
    guidelines: Mapped[List[str]] = Column(JSON)
    constraints: Mapped[List[str]] = Column(JSON)
    examples: Mapped[List[str]] = Column(JSON)
    output_format: Mapped[Optional[str]] = mapped_column(default=None)


association_result_analysis = Table(
    "association_result_analysis",
    Base.metadata,
    Column("analysis_id", ForeignKey("analysis.id")),
    Column("eval_result_id", ForeignKey("eval_result.id")),
)


class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    analyzer_name: Mapped[str] = mapped_column()

    results: Mapped[List[EvalResult]] = relationship(secondary=association_result_analysis)
    recommendation: Mapped["Recommendation"] = relationship()

    rcm_id: Mapped[int] = mapped_column(ForeignKey("recommendation.id"),
                                        default=None)