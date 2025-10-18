# Generated manually for role field addition

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Admin"),
                    ("manager", "Manager"),
                    ("member", "Member"),
                ],
                default="member",
                help_text="User role for oncall scheduling",
                max_length=10,
                verbose_name="Role",
            ),
        ),
    ]
