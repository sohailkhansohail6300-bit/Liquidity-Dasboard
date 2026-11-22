def audit(actor, action, target='', detail=''):
    """Record a sensitive action (internal; no UI). Imported lazily to avoid app-loading cycles."""
    from administration.models import AuditLog
    AuditLog.objects.create(
        actor=actor if (actor is not None and getattr(actor, 'pk', None)) else None,
        actor_email=getattr(actor, 'email', '') or '',
        action=action,
        target=str(target)[:120],
        detail=str(detail)[:2000],
    )
