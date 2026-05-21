from django.db import models, transaction
from django.db.models import Sum, F, Q
from django.core.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)



class ConsistencyError(Exception):
    """Raised when Invoice total does not match sum of InvoiceDetail amounts."""
    pass


# Create your models here.
class Product(models.Model):
    product_name = models.CharField(max_length=255)
    product_price = models.FloatField(default=0)
    product_unit = models.CharField(max_length=255)
    product_is_delete = models.BooleanField(default=False)

    def __str__(self):
        return str(self.product_name)


# class Customer(models.Model):
#     GENDER_CHOICES = (
#         ('Male', 'Male'),
#         ('Female', 'Female'),
#         ('Others', 'Others'),
#     )
#     customer_name = models.CharField(max_length=255)
#     customer_gender = models.CharField(max_length=50, choices=GENDER_CHOICES)
#     customer_dob = models.DateField()
#     customer_points = models.IntegerField(default=0)

#     def __str__(self):
#         return str(self.customer_name)


class Invoice(models.Model):
    """
    Invoice model with transactional consistency for totals.
    Ensures that the total field always matches the sum of associated InvoiceDetail amounts.
    """
    date = models.DateField(auto_now_add=True)
    customer = models.TextField(default='')
    contact = models.CharField(
        max_length=255, default='', blank=True, null=True)
    email = models.EmailField(default='', blank=True, null=True)
    comments = models.TextField(default='', blank=True, null=True)
    # Denormalized total field with CHECK constraint to prevent negative values
    total = models.FloatField(default=0)

    class Meta:
        # Database-level constraint to ensure total is never negative
        constraints = [
            models.CheckConstraint(check=Q(total__gte=0), name='invoice_total_non_negative'),
        ]

    def __str__(self):
        return str(self.id)

    def calculate_total_from_details(self):
        """
        Calculate the total from all associated InvoiceDetail records.
        Returns the sum of (product_price * amount) for all details.
        """
        details = self.invoicedetail_set.all()
        calculated_total = 0.0
        for detail in details:
            if detail.product:
                calculated_total += float(detail.product.product_price) * float(detail.amount)
        return calculated_total

    def validate_total_consistency(self):
        """
        Validate that the stored total matches the sum of InvoiceDetail amounts.
        Raises ConsistencyError if totals diverge.
        """
        calculated_total = self.calculate_total_from_details()
        # Allow small floating-point differences (within 0.01)
        if abs(self.total - calculated_total) > 0.01:
            error_msg = (
                f"Invoice total mismatch: stored_total={self.total}, "
                f"calculated_total={calculated_total}, invoice_id={self.id}"
            )
            logger.error(error_msg)
            raise ConsistencyError(error_msg)

    def update_total_atomic(self):
        """
        Atomically update the Invoice total to match the sum of InvoiceDetail amounts.
        Uses SELECT FOR UPDATE to implement row-level locking.
        """
        with transaction.atomic():
            # Row-level locking: SELECT FOR UPDATE
            locked_invoice = Invoice.objects.select_for_update().get(pk=self.pk)
            
            # Recalculate total from all details
            new_total = locked_invoice.calculate_total_from_details()
            
            # Update the total
            locked_invoice.total = new_total
            locked_invoice.full_clean()  # Validate constraints
            locked_invoice.save(update_fields=['total'])
            
            # Verify consistency after update
            locked_invoice.validate_total_consistency()
            
            return locked_invoice


class InvoiceDetail(models.Model):
    """
    InvoiceDetail model representing line items in an invoice.
    Changes to this model trigger atomic updates to the parent Invoice total.
    """
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, blank=False, null=False)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.IntegerField(default=1)
    # Timestamp for audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure referential integrity at database level
        constraints = [
            models.CheckConstraint(check=Q(amount__gt=0), name='detail_amount_positive'),
        ]

    def __str__(self):
        return f"Detail {self.id} for Invoice {self.invoice_id}"

    @property
    def get_total_bill(self):
        """Calculate the total for this detail line."""
        if self.product:
            total = float(self.product.product_price) * float(self.amount)
            return total
        return 0.0

    def save(self, *args, **kwargs):
        """
        Override save to implement atomic transaction handling.
        Updates the parent Invoice total atomically when detail is created or updated.
        """
        with transaction.atomic():
            # Save the detail record
            super().save(*args, **kwargs)
            
            # Atomically update the parent invoice total
            if self.invoice:
                self.invoice.update_total_atomic()

    def delete(self, *args, **kwargs):
        """
        Override delete to implement atomic transaction handling.
        Updates the parent Invoice total atomically when detail is deleted.
        """
        invoice = self.invoice
        with transaction.atomic():
            # Delete the detail record
            super().delete(*args, **kwargs)
            
            # Atomically update the parent invoice total
            if invoice:
                invoice.update_total_atomic()
