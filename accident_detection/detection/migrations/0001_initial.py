# Generated migration for detection app models

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VideoSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('video_file', models.FileField(upload_to='videos/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('total_frames', models.IntegerField(default=0)),
                ('processed_frames', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('error', 'Error')], default='pending', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Accident',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('location', models.CharField(max_length=255)),
                ('video_id', models.CharField(max_length=255)),
                ('image', models.ImageField(upload_to='accident_images/')),
                ('confidence_score', models.FloatField(default=0.0, validators=[lambda x: 0 <= x <= 100])),
                ('vehicle_count', models.IntegerField(default=0)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
