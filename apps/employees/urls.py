from django.urls import path

from .views import AssignOrdersView, EmployeeCalendarView, EmployeeDetailView, EmployeeListView

app_name = "employees"

urlpatterns = [
    path("", EmployeeListView.as_view(), name="employee_list"),
    path("<int:pk>/", EmployeeDetailView.as_view(), name="employee_detail"),
    path("<int:pk>/kalender/", EmployeeCalendarView.as_view(), name="employee_calendar"),
    path("<int:pk>/zuweisen/", AssignOrdersView.as_view(), name="assign_orders"),
]
