from django.core.management.base import BaseCommand
from attendence.contex import mark_absent_students

class Command(BaseCommand):
    help = 'Marks all students without attendance record as absent'

    def handle(self, *args, **options):
        mark_absent_students()
        self.stdout.write(self.style.SUCCESS('Successfully marked absent students'))
