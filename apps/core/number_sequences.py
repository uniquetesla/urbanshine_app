from django.db import transaction

from .models import NumberSequence, NumberSequenceType


DEFAULT_SEQUENCE_CONFIG = {
    NumberSequenceType.AUFTRAG: {"prefix": "AUF", "separator": "-", "start_value": 1, "padding": 5},
    NumberSequenceType.KUNDE: {"prefix": "KUN", "separator": "-", "start_value": 1, "padding": 5},
    NumberSequenceType.RECHNUNG: {"prefix": "RE", "separator": "-", "start_value": 1, "padding": 5},
    NumberSequenceType.ANGEBOT: {"prefix": "ANG", "separator": "-", "start_value": 1, "padding": 5},
    NumberSequenceType.ARTIKEL: {"prefix": "ART", "separator": "-", "start_value": 1, "padding": 5},
}


def ensure_sequence(sequence_type: str) -> NumberSequence:
    defaults = DEFAULT_SEQUENCE_CONFIG.get(sequence_type, {"prefix": "", "separator": "", "start_value": 1, "padding": 5})
    sequence, _ = NumberSequence.objects.get_or_create(sequence_type=sequence_type, defaults=defaults)
    return sequence


def next_sequence_value(sequence_type: str) -> int:
    with transaction.atomic():
        ensure_sequence(sequence_type)
        sequence = NumberSequence.objects.select_for_update().get(sequence_type=sequence_type)
        next_value = max(sequence.last_value + 1, sequence.start_value)
        sequence.last_value = next_value
        sequence.save(update_fields=["last_value", "updated_at"])
        return next_value


def format_sequence(sequence_type: str, value: int) -> str:
    sequence = ensure_sequence(sequence_type)
    return sequence.format_number(value)


def parse_sequence_value(raw_value: str) -> int | None:
    digits = "".join(ch for ch in (raw_value or "") if ch.isdigit())
    return int(digits) if digits else None
