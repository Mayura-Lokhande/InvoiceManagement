from django import forms
from django.forms import formset_factory
from .models import Product, Invoice, InvoiceDetail


# Common bootstrap styling
COMMON_CLASS = 'form-control'


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            'product_name',
            'product_price',
            'product_unit',
        ]

        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter product name',
                'maxlength': '100',
                'autocomplete': 'off',
            }),

            'product_price': forms.NumberInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter product price',
                'min': '1',
                'step': '0.01',
            }),

            'product_unit': forms.TextInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter product unit',
                'maxlength': '20',
            }),
        }

    # Product name validation
    def clean_product_name(self):
        product_name = self.cleaned_data.get('product_name')

        if len(product_name.strip()) < 2:
            raise forms.ValidationError(
                "Product name must contain at least 2 characters."
            )

        return product_name

    # Product price validation
    def clean_product_price(self):
        product_price = self.cleaned_data.get('product_price')

        if product_price <= 0:
            raise forms.ValidationError(
                "Product price must be greater than 0."
            )

        return product_price


class InvoiceForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = [
            'customer',
            'comments',
            'contact',
            'email',
        ]

        widgets = {
            'customer': forms.TextInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter customer name',
                'maxlength': '100',
            }),

            'contact': forms.TextInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter customer contact number',
                'maxlength': '10',
            }),

            'email': forms.EmailInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter customer email',
            }),

            'comments': forms.Textarea(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter invoice comments',
                'rows': 3,
            }),
        }

    # Contact validation
    def clean_contact(self):
        contact = self.cleaned_data.get('contact')

        if not contact.isdigit():
            raise forms.ValidationError(
                "Contact number should contain digits only."
            )

        if len(contact) != 10:
            raise forms.ValidationError(
                "Contact number must contain exactly 10 digits."
            )

        return contact

    # Customer validation
    def clean_customer(self):
        customer = self.cleaned_data.get('customer')

        if len(customer.strip()) < 3:
            raise forms.ValidationError(
                "Customer name is too short."
            )

        return customer


class InvoiceDetailForm(forms.ModelForm):

    class Meta:
        model = InvoiceDetail
        fields = [
            'product',
            'amount',
        ]

        widgets = {
            'product': forms.Select(attrs={
                'class': COMMON_CLASS,
            }),

            'amount': forms.NumberInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter quantity',
                'min': '1',
            }),
        }

    # Amount validation
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount <= 0:
            raise forms.ValidationError(
                "Quantity must be greater than 0."
            )

        return amount


class ExcelUploadForm(forms.Form):

    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': COMMON_CLASS,
            'accept': '.xlsx,.xls,.csv',
        })
    )

    # File validation
    def clean_file(self):
        file = self.cleaned_data.get('file')

        allowed_extensions = ['xlsx', 'xls', 'csv']

        extension = file.name.split('.')[-1].lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Only Excel and CSV files are allowed."
            )

        # File size validation (5MB max)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "File size must be less than 5MB."
            )

        return file


# Dynamic formset
InvoiceDetailFormSet = formset_factory(
    InvoiceDetailForm,
    extra=1,
    can_delete=True
)
