import csv
import io

from app.utils.validators import validate_obtained_marks


def parse_marks_csv(file_stream, students_by_email, total_marks):
    """
    file_stream: werkzeug FileStorage stream (from request.files)
    students_by_email: dict of {email: User} for this course's enrolled students
    total_marks: activity.total_marks, for range validation

    Returns (rows, errors) where rows is a list of (User, obtained_marks) for
    valid rows, and errors is a list of human-readable strings. If errors is
    non-empty, the caller should reject the whole batch (all-or-nothing).
    """
    errors = []
    rows = []

    try:
        text = file_stream.read().decode("utf-8-sig")  # handles Excel's BOM
    except UnicodeDecodeError:
        return [], ["Could not read the file — please save it as UTF-8 CSV."]

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        return [], ["The file appears to be empty."]

    # Map normalized (stripped, lowercased) header name -> actual header key
    # as stored by DictReader, so stray whitespace in the file's header row
    # (e.g. "obtained_marks " with a trailing space) doesn't cause row.get()
    # to silently miss the column.
    field_map = {f.strip().lower(): f for f in reader.fieldnames}

    if "email" not in field_map or "obtained_marks" not in field_map:
        return [], ["CSV must have 'email' and 'obtained_marks' columns."]

    email_key = field_map["email"]
    marks_key = field_map["obtained_marks"]

    seen_emails = set()

    for line_num, row in enumerate(reader, start=2):  # header is line 1
        email = (row.get(email_key) or "").strip().lower()
        raw_marks = (row.get(marks_key) or "").strip()

        if not email:
            errors.append(f"Row {line_num}: missing email.")
            continue

        if email in seen_emails:
            errors.append(f"Row {line_num}: duplicate row for {email}.")
            continue
        seen_emails.add(email)

        student = students_by_email.get(email)
        if student is None:
            errors.append(f"Row {line_num}: {email} is not enrolled in this course.")
            continue

        if raw_marks == "":
            continue  # blank = skip this student, same convention as the manual grid

        try:
            obtained = float(raw_marks)
            validate_obtained_marks(obtained, total_marks)
        except ValueError as e:
            errors.append(f"Row {line_num} ({email}): {e}")
            continue

        rows.append((student, obtained))

    return rows, errors