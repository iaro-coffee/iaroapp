from django.test import TestCase

# Create your tests here.


from catalog.models import Author
from django.urls import reverse


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create authors for pagination tests
        number_of_authors = 13
        for author_id in range(number_of_authors):
            Author.objects.create(first_name='Christian {0}'.format(author_id),
                                  last_name='Surname {0}'.format(author_id))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/authors/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] is True)
        self.assertEqual(len(response.context['author_list']), 10)

    def test_lists_all_authors(self):
        # Get second page and confirm it has (exactly) the remaining 3 items
        response = self.client.get(reverse('authors')+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] is True)
        self.assertEqual(len(response.context['author_list']), 3)


import datetime
from django.utils import timezone

from catalog.models import TaskInstance, Task, Category
from django.contrib.auth.models import User  # Required to assign User as a borrower


class LoanedTaskInstancesByUserListViewTest(TestCase):

    def setUp(self):
        # Create two users
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')

        test_user1.save()
        test_user2.save()

        # Create a task
        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_category = Category.objects.create(name='Fantasy')
        test_task = Task.objects.create(
            title='Task Title',
            summary='My task summary',
            author=test_author,
        )
        # Create category as a post-step
        category_objects_for_task = Category.objects.all()
        test_task.category.set(category_objects_for_task)
        test_task.save()

        # Create 30 TaskInstance objects
        number_of_task_copies = 30
        for task_copy in range(number_of_task_copies):
            return_date = timezone.now() + datetime.timedelta(days=task_copy % 5)
            if task_copy % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            status = 'm'
            TaskInstance.objects.create(task=test_task, description='Unlikely Description, 2016', due_done=return_date,
                                        borrower=the_borrower, status=status)

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/mytasks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(response, 'catalog/taskinstance_list_borrowed_user.html')

    def test_only_borrowed_tasks_in_list(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check that initially we don't have any tasks in list (none on loan)
        self.assertTrue('taskinstance_list' in response.context)
        self.assertEqual(len(response.context['taskinstance_list']), 0)

        # Now change all tasks to be on loan
        get_ten_tasks = TaskInstance.objects.all()[:10]

        for copy in get_ten_tasks:
            copy.status = 'o'
            copy.save()

        # Check that now we have borrowed tasks in the list
        response = self.client.get(reverse('my-borrowed'))
        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        self.assertTrue('taskinstance_list' in response.context)

        # Confirm all tasks belong to testuser1 and are on loan
        for taskitem in response.context['taskinstance_list']:
            self.assertEqual(response.context['user'], taskitem.borrower)
            self.assertEqual(taskitem.status, 'o')

    def test_pages_paginated_to_ten(self):

        # Change all tasks to be on loan.
        # This should make 15 test user ones.
        for copy in TaskInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Confirm that only 10 items are displayed due to pagination
        # (if pagination not enabled, there would be 15 returned)
        self.assertEqual(len(response.context['taskinstance_list']), 10)

    def test_pages_ordered_by_due_date(self):

        # Change all tasks to be on loan
        for copy in TaskInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Confirm that of the items, only 10 are displayed due to pagination.
        self.assertEqual(len(response.context['taskinstance_list']), 10)

        last_date = 0
        for copy in response.context['taskinstance_list']:
            if last_date == 0:
                last_date = copy.due_done
            else:
                self.assertTrue(last_date <= copy.due_done)


from django.contrib.auth.models import Permission  # Required to grant the permission needed to set a task as returned.


class RenewTaskInstancesViewTest(TestCase):

    def setUp(self):
        # Create a user
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user1.save()

        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')
        test_user2.save()
        permission = Permission.objects.get(name='Set task as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Create a task
        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_category = Category.objects.create(name='Fantasy')
        test_task = Task.objects.create(title='Task Title', summary='My task summary',
                                        author=test_author,)
        # Create category as a post-step
        category_objects_for_task = Category.objects.all()
        test_task.category.set(category_objects_for_task)
        test_task.save()

        # Create a TaskInstance object for test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_taskinstance1 = TaskInstance.objects.create(task=test_task,
                                                              description='Unlikely Description, 2016', due_done=return_date,
                                                              borrower=test_user1, status='o')

        # Create a TaskInstance object for test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_taskinstance2 = TaskInstance.objects.create(task=test_task, description='Unlikely Description, 2016',
                                                              due_done=return_date, borrower=test_user2, status='o')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}))
        # Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_forbidden_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}))
        self.assertEqual(response.status_code, 403)


    def test_logged_in_with_permission_borrowed_task(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance2.pk}))

        # Check that it lets us login - this is our task and we have the right permissions.
        self.assertEqual(response.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_task(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}))

        # Check that it lets us login. We're a librarian, so we can view any users task
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}))
        self.assertEqual(response.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(response, 'catalog/task_renew_librarian.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}))
        self.assertEqual(response.status_code, 200)

        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(response.context['form'].initial['renewal_date'], date_3_weeks_in_future)

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')

        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        response = self.client.post(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}),
                                    {'renewal_date': date_in_past})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        response = self.client.post(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}),
                                    {'renewal_date': invalid_date_in_future})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')

    def test_redirects_to_all_borrowed_task_list_on_success(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        response = self.client.post(reverse('renew-task-librarian', kwargs={'pk': self.test_taskinstance1.pk}),
                                    {'renewal_date': valid_date_in_future})
        self.assertRedirects(response, reverse('all-borrowed'))

    def test_HTTP404_for_invalid_task_if_logged_in(self):
        import uuid
        test_uid = uuid.uuid4()  # unlikely UID to match our taskinstance!
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-task-librarian', kwargs={'pk': test_uid}))
        self.assertEqual(response.status_code, 404)


class AuthorCreateViewTest(TestCase):
    """Test case for the AuthorCreate view (Created as Challenge)."""

    def setUp(self):
        # Create a user
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')

        test_user1.save()
        test_user2.save()

        permission = Permission.objects.get(name='Set task as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Create a task
        test_author = Author.objects.create(first_name='John', last_name='Smith')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('author-create'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/author/create/')

    def test_forbidden_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_form.html')

    def test_form_date_of_quited_initially_set_to_expected_date(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)

        expected_initial_date = datetime.date(2020, 6, 11)
        response_date = response.context['form'].initial['date_of_quited']
        response_date = datetime.datetime.strptime(response_date, "%d/%m/%Y").date()
        self.assertEqual(response_date, expected_initial_date)

    def test_redirects_to_detail_view_on_success(self):
        login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
        response = self.client.post(reverse('author-create'),
                                    {'first_name': 'Christian Name', 'last_name': 'Surname'})
        # Manually check redirect because we don't know what author was created
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/catalog/author/'))
