import os
import sys
import django

sys.path.append('/home/imme-deb-mac/Desktop/iaro-project/iaroapp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iaroapp.settings')
django.setup()

from django.db.models import Q
from django.utils import timezone
from inventory.views import get_current_branch
from tasks.models import Task

def benchmark_get_my_tasks(request):
    import time

    # Benchmark Combined Query Function
    start_time = time.time()
    combined_tasks = get_my_tasks_combined(request)
    combined_duration = time.time() - start_time

    # Benchmark Separated Query Function
    start_time = time.time()
    separated_tasks = get_my_tasks_separated(request)
    separated_duration = time.time() - start_time

    # Benchmark get_tasks Function
    start_time = time.time()
    task_list = get_tasks(request)
    get_tasks_duration = time.time() - start_time

    # Print the results
    print(f"Combined Query Duration: {combined_duration:.6f} seconds")
    print(f"Separated Query Duration: {separated_duration:.6f} seconds")
    print(f"get_tasks Query Duration: {get_tasks_duration:.6f} seconds")

    # Optionally return the durations if needed
    return combined_duration, separated_duration, get_tasks_duration
def get_tasks(request):
    today_weekday = timezone.now().weekday() + 1
    branch = get_current_branch(request)
    user_groups_ids = list(request.user.groups.values_list('id', flat=True))

    return Task.objects.filter(
        users=request.user.id,  # Use user ID directly
        groups__id__in=user_groups_ids,
        branch__name=branch,
        weekdays__id=today_weekday,
        parent_task=None
    ).distinct().order_by("title")
def get_my_tasks_combined(request):
    today_weekday = timezone.now().strftime("%A")
    branch = get_current_branch(request)
    user_groups_ids = list(request.user.groups.values_list("id", flat=True))

    if branch == "All":
        branch_filter = Q()
    else:
        branch_filter = Q(branch__name=branch)

    tasks = Task.objects.filter(
        (Q(weekdays__name=today_weekday) | Q(weekdays__isnull=True)) &
        (Q(users=request.user.id) | Q(groups__id__in=user_groups_ids) |
        (Q(users__isnull=True) & Q(groups__isnull=True))) &
        branch_filter &
        Q(parent_task=None)
    ).distinct().prefetch_related("users", "groups", "branch").order_by("title")

    return tasks

def get_my_tasks_separated(request):
    today_weekday = timezone.now().strftime("%A")

    tasks = Task.objects.filter(
        Q(weekdays__name=today_weekday) | Q(weekdays__isnull=True),
        parent_task=None
    ).prefetch_related("users", "groups", "branch")

    branch = get_current_branch(request)
    user_groups_ids = list(request.user.groups.values_list("id", flat=True))

    if branch == "All":
        branch_filter = Q()
    else:
        branch_filter = Q(branch__name=branch)

    filtered_tasks = tasks.filter(
        Q(users=request.user.id) |
        Q(groups__id__in=user_groups_ids) |
        (Q(users__isnull=True) & Q(groups__isnull=True)),
        branch_filter,
    )

    return filtered_tasks.distinct().order_by("title")

# Mock or create a request object for testing purposes
# This part needs to be customized based on your application's context
class MockQuerySet:
    def __init__(self, items):
        self.items = items

    def values_list(self, *fields, **kwargs):
        flat = kwargs.get('flat', False)
        if flat:
            return [getattr(item, fields[0]) for item in self.items]
        return [[getattr(item, field) for field in fields] for item in self.items]

class MockUser:
    def __init__(self, id, groups):
        self.id = id
        self.groups = MockQuerySet(groups)

class MockRequest:
    def __init__(self, user, get=None):
        self.user = user
        self.GET = get or {}

class MockGroup:
    def __init__(self, id):
        self.id = id

# Create mock groups and user
mock_groups = [MockGroup(id=1), MockGroup(id=2)]
mock_user = MockUser(id=1, groups=mock_groups)

# Create a mock request with GET parameters
mock_request = MockRequest(user=mock_user, get={"branch": "All"})

# Run the benchmark function
benchmark_get_my_tasks(mock_request)

