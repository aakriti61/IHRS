# Generated manually -- adds unique=True to Patient.phone.
#
# IMPORTANT: if you already have patients in the database, this
# migration will FAIL if any two Patient rows currently share a phone
# number (which the bug being fixed here made possible). Before
# running `python manage.py migrate`, check for existing duplicates:
#
#   python manage.py shell
#   >>> from django.db.models import Count
#   >>> from accounts.models import Patient
#   >>> Patient.objects.values("phone").annotate(c=Count("id")).filter(c__gt=1)
#
# If that returns any rows, fix/merge those duplicate Patient records
# first (update one of the phone numbers, or merge the records), then
# run migrate. Run this on BOTH Bir's and TUTH's databases separately
# -- they are two entirely different databases, one migration run
# never touches the other.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_customuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='phone',
            field=models.CharField(max_length=15, unique=True),
        ),
    ]
