from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Deletes a superuser with the given username'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='The username of the superuser to delete')

    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()

        try:
            user = User.objects.get(username=username, is_superuser=True)
        except User.DoesNotExist:
            raise CommandError('Superuser with username "%s" does not exist' % username)

        user.delete()

        self.stdout.write(self.style.SUCCESS('Successfully deleted superuser "%s"' % username))
