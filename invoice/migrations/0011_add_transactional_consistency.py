
# Generated migration for transactional consistency

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0010_auto_20221214_1059'),
    ]

    operations = [
        # Add CHECK constraint to ensure invoice total is never negative
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.CheckConstraint(check=models.Q(('total__gte', 0)), name='invoice_total_non_negative'),
        ),
        # Add timestamp fields to InvoiceDetail for audit trail
        migrations.AddField(
            model_name='invoicedetail',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='invoicedetail',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Change InvoiceDetail.invoice foreign key from SET_NULL to CASCADE
        migrations.AlterField(
            model_name='invoicedetail',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.invoice'),
        ),
        # Add CHECK constraint to ensure invoice detail amount is positive
        migrations.AddConstraint(
            model_name='invoicedetail',
            constraint=models.CheckConstraint(check=models.Q(('amount__gt', 0)), name='detail_amount_positive'),
        ),
    ]

