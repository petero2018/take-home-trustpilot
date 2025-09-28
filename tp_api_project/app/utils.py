import csv
import io
from typing import Any, Iterable, Iterator, Sequence


def stream_csv(rows: Iterable[Sequence[Any]], header: Sequence[Any]) -> Iterator[str]:
    """Yield CSV chunks starting with the header row followed by the provided records."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in rows:
        writer.writerow(row)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
