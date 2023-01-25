from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

from .models import Tips

from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.all()

def index(request):
    return render(
        request,
        'tips.html',
        context={'users': users},
    )


from django.views import generic

class TipsListView(generic.ListView):
    """Generic class-based view for a list of tips."""
    model = Tips
    paginate_by = 10


class TipsDetailView(generic.DetailView):
    """Generic class-based detail view for a task."""
    model = Tips

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib.auth.decorators import login_required, permission_required

# from .forms import RenewTipsForm
from tips.forms import RenewTipsForm


@login_required
@permission_required('tips.can_mark_returned', raise_exception=True)
def renew_task_librarian(request, pk):
    """View function for renewing a specific TipsInstance by librarian."""
    task_instance = get_object_or_404(TipsInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewTipsForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_done field)
            task_instance.due_done = form.cleaned_data['renewal_date']
            task_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewTipsForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'task_instance': task_instance,
    }

    return render(request, 'tips/task_renew_librarian.html', context)


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin

# Classes created for the forms challenge
class TipsCreate(PermissionRequiredMixin, CreateView):
    model = Tips
    fields = ['title']

class TipsUpdate(PermissionRequiredMixin, UpdateView):
    model = Tips
    fields = ['title']

class TipsDelete(PermissionRequiredMixin, DeleteView):
    model = Tips
    success_url = reverse_lazy('tips')