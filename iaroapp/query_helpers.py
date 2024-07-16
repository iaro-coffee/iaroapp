from django.db.models import Q


def qif(*args, _if=True, **kwargs):
    if _if:
        return Q(*args, **kwargs)
    return Q()
