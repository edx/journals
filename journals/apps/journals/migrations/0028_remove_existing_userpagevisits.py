from django.db import migrations

def remove_null_rows(apps, schema_editor):
    UserPageVisit = apps.get_model('journals', 'UserPageVisit')
    for visit in UserPageVisit.objects.all():
        if visit.journal_about == None:
            visit.delete()


class Migration(migrations.Migration):
    """ Removes all previously created UserPageVisit rows with a null journal_about field """

    dependencies = [
        ('journals', '0027_auto_20180925_1839'),
    ]

    operations = [
        migrations.RunPython(remove_null_rows)
    ]



