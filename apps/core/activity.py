from apps.core.models import ActivityLog


def log_activity(*, actor, subject_type, subject_label, action, details="", from_state="", to_state="", icon="📝"):
    ActivityLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        subject_type=subject_type,
        subject_label=subject_label,
        action=action,
        details=details,
        from_state=from_state,
        to_state=to_state,
        icon=icon,
    )
