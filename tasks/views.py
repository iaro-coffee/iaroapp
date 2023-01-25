from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

from .models import Task, Author, TaskInstance, Weekdays

def index(request):
    """View function for home page of site."""
    # Generate counts of some of the main objects
    num_tasks = Task.objects.all().count()
    num_instances = TaskInstance.objects.all().count()
    # Available copies of tasks
    num_instances_available = TaskInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()  # The 'all()' is implied by default.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits+1

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={'num_tasks': num_tasks, 'num_instances': num_instances,
                 'num_instances_available': num_instances_available, 'num_authors': num_authors,
                 'num_visits': num_visits},
    )


from django.views import generic


class TaskListView(generic.ListView):
    """Generic class-based view for a list of tasks."""
    model = Task
    paginate_by = 10


class TaskDetailView(generic.DetailView):
    """Generic class-based detail view for a task."""
    model = Task


class AuthorListView(generic.ListView):
    """Generic class-based list view for a list of authors."""
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    """Generic class-based detail view for an author."""
    model = Author


from django.contrib.auth.mixins import LoginRequiredMixin


class LoanedTasksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing tasks on loan to current user."""
    model = TaskInstance
    template_name = 'tasks/taskinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return TaskInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_done')


# Added as part of challenge!
from django.contrib.auth.mixins import PermissionRequiredMixin


class LoanedTasksAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing all tasks on loan. Only visible to users with can_mark_returned permission."""
    model = TaskInstance
    permission_required = 'tasks.can_mark_returned'
    template_name = 'tasks/taskinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return TaskInstance.objects.filter(status__exact='o').order_by('due_done')


from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib.auth.decorators import login_required, permission_required

# from .forms import RenewTaskForm
from tasks.forms import RenewTaskForm


@login_required
@permission_required('tasks.can_mark_returned', raise_exception=True)
def renew_task_librarian(request, pk):
    """View function for renewing a specific TaskInstance by librarian."""
    task_instance = get_object_or_404(TaskInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewTaskForm(request.POST)

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
        form = RenewTaskForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'task_instance': task_instance,
    }

    return render(request, 'tasks/task_renew_librarian.html', context)


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_joined', 'date_of_quited']
    initial = {'date_of_quited': '11/06/2020'}
    permission_required = 'tasks.can_mark_returned'


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = '__all__' # Not recommended (potential security issue if more fields added)
    permission_required = 'tasks.can_mark_returned'


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'tasks.can_mark_returned'


# Classes created for the forms challenge
class TaskCreate(PermissionRequiredMixin, CreateView):
    model = Task
    fields = ['title', 'author', 'summary', 'weekdays']
    permission_required = 'tasks.can_mark_returned'


class TaskUpdate(PermissionRequiredMixin, UpdateView):
    model = Task
    fields = ['title', 'author', 'summary', 'weekdays']
    permission_required = 'tasks.can_mark_returned'


class TaskDelete(PermissionRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('tasks')
    permission_required = 'tasks.can_mark_returned'
