from django.db import models
from django.conf import settings

class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField()
    title = models.CharField(max_length=200, blank=True, null=True)  # Add title field
    start_date = models.DateField()
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=[
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ])
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.description


class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    description = models.TextField()
    due_date = models.DateField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.description
