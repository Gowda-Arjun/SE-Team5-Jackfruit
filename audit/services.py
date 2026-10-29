from .models import AuditLog


def write_audit(actor, action, target=None, outcome=AuditLog.Outcome.SUCCESS, details=None):
    """Insert one audit row (SAD 4.3 internal interface).

    Call it inside the caller's transaction.atomic() block so the audit entry and the
    change it describes commit or roll back together.

        write_audit(request.user, "ROOM_ALLOCATED", allocation, details={"room": room.pk})
    """
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_type=type(target).__name__ if target is not None else "",
        target_id=str(target.pk) if getattr(target, "pk", None) is not None else "",
        outcome=outcome,
        details=details or {},
    )
