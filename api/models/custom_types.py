from typing import Any, Optional, List
from sqlalchemy.types import UserDefinedType
import numpy as np


class Vector(UserDefinedType):
    """PostgreSQL vector type for pgvector"""

    def __init__(self, dimension: int):
        self.dimension = dimension

    def get_col_spec(self, **kw: Any) -> str:
        return f"vector({self.dimension})"

    def bind_processor(self, dialect):
        def process(value: Optional[List[float]]) -> Optional[str]:
            if value is None:
                return None
            # Convert list to PostgreSQL vector format
            if isinstance(value, np.ndarray):
                value = value.tolist()
            if len(value) != self.dimension:
                raise ValueError(f"Vector must be {self.dimension} dimensions")
            # Format as PostgreSQL vector string
            return f"[{','.join(str(x) for x in value)}]"

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            # Convert PostgreSQL vector format back to list
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                return [float(x) for x in value[1:-1].split(',')]
            return value

        return process