from django import forms
from django.forms import formset_factory
from .models import Product, Invoice, InvoiceDetail


# Common Bootstrap class
COMMON_CLASS = 'form-control'


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ['product_name', 'product_price', 'product_unit']

        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter product name',
                'maxlength': '100',
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
            }),
        }

    # Custom validation
    def clean_product_price(self):
        price = self.cleaned_data.get('product_price')

        if price <= 0:
            raise forms.ValidationError(
                "Product price must be greater than 0."
            )

        return price


class InvoiceForm(forms.ModelForm):

    class Meta:
        model = Invoice
        fields = ['customer', 'comments', 'contact', 'email']

        widgets = {
            'customer': forms.TextInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter customer name',
            }),

            'contact': forms.TextInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter customer contact',
                'maxlength': '10',
            }),

            'email': forms.EmailInput(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Enter customer email',
            }),

            'comments': forms.Textarea(attrs={
                'class': COMMON_CLASS,
                'placeholder': 'Additional comments',
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

        if len(contact) < 10:
            raise forms.ValidationError(
                "Contact number must be at least 10 digits."
            )

        return contact


class InvoiceDetailForm(forms.ModelForm):

    class Meta:
        model = InvoiceDetail
        fields = ['product', 'amount']

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

    # Quantity validation
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount <= 0:
            raise forms.ValidationError(
                "Amount must be greater than 0."
            )

        return amount


class ExcelUploadForm(forms.Form):

    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': COMMON_CLASS,
            'accept': '.xlsx,.xls,.csv'
        })
    )

    # File validation
    def clean_file(self):
        file = self.cleaned_data.get('file')

        allowed_extensions = ['xlsx', 'xls', 'csv']

        extension = file.name.split('.')[-1]

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Only Excel or CSV files are allowed."
            )

        return file


InvoiceDetailFormSet = formset_factory(
    InvoiceDetailForm,
    extra=1,
    can_delete=True
)
