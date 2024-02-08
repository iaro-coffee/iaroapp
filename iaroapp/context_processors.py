from . import views

def getShowOpening(request):
    return {'showOpening': views.getShowOpening(request)}


def getShowClosing(request):
    return {'showClosing': views.getShowClosing(request)}
