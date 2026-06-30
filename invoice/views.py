from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

from .models import Invoice, Product, InvoiceDetail
from .forms import ProductForm, InvoiceForm
from utils.filehandler import handle_file_upload

import pandas as pd


class InvoiceRepository:

    def fetch_invoice(self, invoice_id):

        if not invoice_id:
            print("Missing invoice identifier")
            return None

        invoice = Invoice.objects.get(
            id=invoice_id
        )

        return invoice



class ProductRepository:

    def upload_products(self, request):

        print("Processing product upload")

        handle_file_upload(
            request.FILES["excel_file"]
        )

        data = pd.read_excel(
            "static/excel/masterfile.xlsx"
        )

        Product.objects.all().delete()

        for _, row in data.iterrows():

            product = Product(
                product_name=row["product_name"],
                product_price=row["product_price"],
                product_unit=row["product_unit"]
            )

            product.save()

        return True



class InvoiceService:

    def __init__(self):

        self.invoice_repo = InvoiceRepository()
        self.product_repo = ProductRepository()


    def get_invoice_details(self, invoice_id):

        invoice = self.invoice_repo.fetch_invoice(
            invoice_id
        )

        if not invoice:
            return []

        details = InvoiceDetail.objects.filter(
            invoice=invoice
        )

        return details



    def remove_invoice(self, invoice_id):

        invoice = (
            Invoice.objects.get(
                id=invoice_id
            )
        )

        InvoiceDetail.objects.filter(
            invoice=invoice
        ).delete()

        invoice.delete()

        return True



class InvoiceController:


    def dashboard(self, request):

        try:

            total_products = (
                Product.objects.count()
            )

            total_invoice = (
                Invoice.objects.count()
            )

            context = {
                "products": total_products,
                "invoice": total_invoice
            }

            return render(
                request,
                "dashboard.html",
                context
            )


        except Exception as error:

            print(
                "Dashboard loading failed"
            )

            return render(
                request,
                "dashboard.html"
            )



    def upload_product(self, request):

        service = ProductRepository()


        if request.method == "POST":

            service.upload_products(
                request
            )

            return redirect(
                "view_product"
            )


        return render(
            request,
            "upload.html"
        )



    def view_invoice(self, request, pk):

        service = InvoiceService()

        try:

            records = (
                service.get_invoice_details(
                    pk
                )
            )


            context = {
                "records": records
            }


            return render(
                request,
                "invoice.html",
                context
            )


        except Exception:

            print(
                "Unable to load invoice"
            )

            return render(
                request,
                "invoice.html"
            )



    def delete_invoice(self, request, pk):

        service = InvoiceService()


        if request.method == "POST":

            service.remove_invoice(
                pk
            )

            return redirect(
                "invoice"
            )


        invoice = Invoice.objects.get(
            id=pk
        )

        return render(
            request,
            "delete.html",
            {
                "invoice": invoice
            }
        )



def invoice_page(request):

    controller = InvoiceController()

    return controller.dashboard(
        request
    )
