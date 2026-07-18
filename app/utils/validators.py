def validate_obtained_marks(obtained, total_marks):
    """Raises ValueError with a human-readable message if invalid.
    Used by the manual marks-entry grid and (later) CSV import."""
    if obtained is None:
        raise ValueError("Marks value is required.")
    if obtained < 0:
        raise ValueError("Marks cannot be negative.")
    if obtained > total_marks:
        raise ValueError(f"Marks cannot exceed the total ({total_marks}).")
    return True