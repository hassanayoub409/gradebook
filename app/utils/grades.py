def student_activity_mark(student_id, activity):
    for mark in activity.marks:
        if mark.student_id == student_id:
            return mark
    return None


def section_summary(student_id, section):
    """Returns None if nothing in this section has been graded yet.
    Otherwise {obtained, possible, percentage} based only on activities
    that have a mark recorded — ungraded activities are excluded, not
    counted as zero."""
    obtained_total = 0.0
    possible_total = 0.0
    any_marked = False

    for activity in section.activities:
        mark = student_activity_mark(student_id, activity)
        if mark is not None:
            obtained_total += mark.obtained_marks
            possible_total += activity.total_marks
            any_marked = True

    if not any_marked or possible_total == 0:
        return None

    return {
        "obtained": obtained_total,
        "possible": possible_total,
        "percentage": (obtained_total / possible_total) * 100,
    }


def course_total(student_id, course):
    """Weighted total across ALL sections in the course. Sections with no
    graded activities yet contribute 0 to the total — this is a
    conservative 'your grade if nothing else gets graded' view, not a
    projection of final performance. Returns None only if the course has
    no sections at all."""
    if not course.sections:
        return None

    weighted_sum = 0.0
    total_weight = 0.0

    for section in course.sections:
        summary = section_summary(student_id, section)
        percentage = summary["percentage"] if summary is not None else 0.0
        weighted_sum += percentage * section.weight
        total_weight += section.weight

    if total_weight == 0:
        return None

    return {
        "current_percentage": weighted_sum / total_weight,
        "weight_covered": total_weight,
    }