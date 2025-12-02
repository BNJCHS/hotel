from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservas', '0004_alter_reserva_metodo_pago'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='codigo_checkin',
            field=models.CharField(
                max_length=10,
                null=True,
                blank=True,
                help_text='Código de seguridad para realizar el check-in',
            ),
        ),
    ]

