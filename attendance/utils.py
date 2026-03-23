from leaves.models import Leave
from organization.models import Holiday


def can_mark_attendance(employee, attendance_date):

    # 1. Holiday Check
    if Holiday.objects.filter(date=attendance_date).exists():
        return False, "Cannot mark attendance on a holiday."

    # 2. Approved Leave Check
    is_on_leave = Leave.objects.filter(
        employee=employee,
        status="APPROVED",
        start_date__lte=attendance_date,
        end_date__gte=attendance_date
    ).exists()

    if is_on_leave:
        return False, "Employee is on approved leave."

    return True, None