# Generated migration for adding accident timestamp and status fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detection', '0004_videosession_alert_sent_videosession_is_processed'),
    ]

    operations = [
        migrations.AddField(
            model_name='accident',
            name='accident_time',
            field=models.CharField(
                default='00:00:00',
                help_text='Timestamp in video (HH:MM:SS format)',
                max_length=12
            ),
        ),
        migrations.AddField(
            model_name='videosession',
            name='accident_detected',
            field=models.BooleanField(
                default=False,
                help_text='Whether accident was detected in video'
            ),
        ),
        migrations.AddField(
            model_name='videosession',
            name='first_accident_time',
            field=models.CharField(
                default='00:00:00',
                help_text='Time of first detected accident in video (HH:MM:SS)',
                max_length=12
            ),
        ),
        migrations.AlterField(
            model_name='videosession',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('detected', 'Accident Detected'),
                    ('not_detected', 'No Accident Detected'),
                    ('failed', 'Failed')
                ],
                default='pending',
                max_length=20
            ),
        ),
    ]
