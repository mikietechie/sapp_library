import datetime
from typing import Iterable

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django import forms
from django.utils.functional import cached_property
from django.core.exceptions import ValidationError
from rest_framework.request import Request

from sapp.models import SM, AbstractUser, ImageField, AbstractSettings, AbstractType, cls, AbstractAction


class Settings(AbstractSettings):

    class Meta(SM.Meta):
        verbose_name = "SAPP Library Settings"
        verbose_name_plural = "SAPP Library Settings"

    default_lease_days = models.PositiveIntegerField(default=7)
    default_booking_days = models.PositiveIntegerField(default=30)


class Member(SM):
    icon = "fas fa-book-reader"
    cols_css_class = cls.COL_MD6
    list_field_names = ("id", "full_name", "user", "role", "about")
    filter_field_names = ("active", "role")

    ROLES = ("One", "Two")

    user: models.ForeignKey[AbstractUser] = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sapp_library_member_user", blank=True, null=True)
    full_name = models.CharField(max_length=128, blank=True)
    role = models.CharField(max_length=16, choices=SM.iter_as_choices(*ROLES), default="One")
    active = models.BooleanField(default=True)
    about = models.TextField(max_length=512, blank=True, null=True)
    termination_reason = models.TextField(max_length=512, blank=True, null=True)

    def __str__(self):
        return f"{self.sm_str} {self.full_name}"
    
    def set_full_name(self):
        if not self.full_name and self.user:
            self.full_name = self.user.get_full_name()
    
    def save(self, *args, **kwargs):
        self.set_full_name()
        return super().save(*args, **kwargs)
    

class Genre(SM):
    icon = "fas fa-folder"
    list_field_names = ("id", "image", "name", "description")
    detail_field_names = list_field_names
    api_methods = ("get_genre_book_stats_api", )

    name = models.CharField(max_length=128)
    description = models.TextField(max_length=512, blank=True, null=True)
    image = ImageField()


    def __str__(self):
        return self.name
    
    @classmethod
    def get_genre_book_stats_api(cls, request: Request, kwds: dict):
        return cls.get_genre_book_stats()

    @classmethod
    def get_genre_book_stats(cls):
        data = {}
        for i in Genre.objects.all():
            data[f"{i.name}"] = Book.objects.filter(genre_id=i.pk).count()
        data["other"] = Book.objects.filter(genre_id=None).count()
        return data


class Series(SM):
    icon = "fas fa-atlas"
    list_field_names = ("id", "title", "image", "genre", "author", "publisher")

    title = models.CharField(max_length=128)
    image = ImageField(blank=True, null=True)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT)
    publisher = models.CharField(max_length=256, blank=True, null=True)
    author = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.title


class BookType(AbstractType):
    pass


class Book(SM):
    icon = "fas fa-book"
    cols_css_class = cls.COL_12MD6LG4
    list_field_names = ("id", "title", "series", "genre", "year", "author")
    detail_field_names = ("id", "title", "image", "book_type", "isbn", "genre", "series", "author", "publisher", "year", "language", )
    queryset_names = ("items", )

    confirm_delete = True

    title = models.CharField(max_length=128, serialize=cls.CLS_COL_12)
    image = ImageField(blank=True, null=True)
    book_type = models.ForeignKey(BookType, on_delete=models.PROTECT)
    isbn = models.CharField(max_length=64)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT, blank=True, null=True)
    series = models.ForeignKey(Series, on_delete=models.SET_NULL, blank=True, null=True)
    author = models.CharField(max_length=256, blank=True, null=True)
    publisher = models.CharField(max_length=256, blank=True, null=True)
    year = models.PositiveIntegerField()
    language = models.CharField(max_length=32, default="English")

    def __str__(self):
        return f"{self.title} {self.year}"

    @cached_property
    def items(self):
        return BookItem.objects.filter(book=self)


class BookItem(SM):
    icon = "fas fa-bookmark"
    list_field_names = ("id", "book", "code", "retired_on", "available")
    filter_field_names = ("book", "code", "condition", "retired_on", "available")
    distinct_on_options = ("book",)

    has_notes = True
    confirm_delete = True
    per_page = 10

    CONDITIONS = ("New", "As New", "Fine", "Very Good", "Good", "Fair", "Poor", "Binding Copy")

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    code = models.CharField(max_length=32)
    retired_on = models.DateField(blank=True, null=True)
    retirement_reason = models.TextField(blank=True, null=True)
    condition = models.CharField(max_length=128, choices=SM.iter_as_choices(*CONDITIONS), default="New")
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.book} {self.code}"
    
    @property
    def list_url(self):
        return (self.book and self.book.detail_url) or super().list_url
    
    def sync_availability(self):
        self.available = not Lease.objects.filter(book_item=self, returned=None).exists()

    def save(self, *args, **kwargs):
        self.sync_availability()
        return super().save(*args, **kwargs)


class Lease(SM):
    icon = "fas fa-file-contract"
    cols_css_class = cls.COL_LG6
    list_field_names = ("id", "condition", "book_item", "member",  "leased_on", "due_date", "returned")
    detail_field_names = list_field_names
    filter_field_names = ("condition", "book_item", "member", "leased_on", "due_date", "returned")

    has_notes = True
    confirm_delete = True

    image = ImageField(blank=True, null=True)
    condition = models.CharField(max_length=128, blank=True, choices=SM.iter_as_choices(*BookItem.CONDITIONS), default="Good")
    book_item = models.ForeignKey(BookItem, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, limit_choices_to={"active": True})
    leased_on = models.DateField(default=datetime.date.today)
    due_date = models.DateField(blank=True)
    returned = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.member} borrows {self.book_item}"
    
    def set_due_date(self):
        if not self.due_date:
            library_settings = Settings.objects.first()
            if library_settings:
                self.due_date = self.leased_on + datetime.timedelta(days=library_settings.default_lease_days)

    def save(self, *args, **kwargs):
        self.set_due_date()
        return super().save(*args, **kwargs)
    
    def after_save(self, is_creation: bool):
        super().after_save(is_creation)
        self.book_item.save()

    @classmethod
    def get_filters_form(cls, request: WSGIRequest, _fields: Iterable = None):
        super_form = super().get_filters_form(request, _fields)
        class FormClass(super_form):
            book_item__book = forms.ModelChoiceField(Book.objects, label="Book")
        return FormClass
    

class Booking(SM):
    icon = "fas fa-calendar-day"
    list_field_names = ("id", "book", "member", "status", "expire_date")
    filter_field_names = ("book", "member", "status", "expire_date")

    STATUSES = ("Pending", "Accepted", "Ignored", "Expired", "Granted")

    confirm_delete = True
    has_notes = True

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=SM.iter_as_choices(*STATUSES), default="Pending")
    expire_date = models.DateField(blank=True)
    
    def set_expire_date(self):
        if not self.expire_date:
            library_settings = Settings.objects.first()
            if library_settings:
                self.expire_date = datetime.date.today() + datetime.timedelta(days=library_settings.default_booking_days)

    def save(self, *args, **kwargs):
        self.set_expire_date()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.member} wants {self.book}"
    
    @classmethod
    def get_filters_form(cls, request: WSGIRequest, _fields: Iterable = None):
        super_form_class = super().get_filters_form(request, _fields)
        class FormClass(super_form_class):
            expire_date__lte = forms.DateField(label="Expires Before")
            expire_date__gte = forms.DateField(label="Expires After")
        return FormClass
    

class RestockAction(AbstractAction):
    icon = "fas fa-exchange-alt"
    list_field_names = ("id", "book", "number_of_books", "prefix", "condition", "creation_timestamp", "created_by")
    filter_field_names = ("book", "prefix", "condition")

    STATUSES = ("Pending", "Accepted", "Ignored", "Expired", "Granted")

    confirm_delete = True
    has_notes = True

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    number_of_books = models.PositiveIntegerField()
    codes = models.CharField(max_length=512, blank=True, null=True)
    prefix = models.CharField(max_length=16, default=datetime.date.today)
    generate_codes_from = models.PositiveSmallIntegerField(blank=True, null=True)
    condition = models.CharField(max_length=128, choices=SM.iter_as_choices(*BookItem.CONDITIONS))

    def process_action(self):
        book_items = []
        codes = self.codes.split(",") if self.codes else range(self.generate_codes_from, self.generate_codes_from+self.number_of_books)
        for code in codes:
            book_items.append(BookItem(
                book = self.book,
                code = f"{self.prefix}-{code}",
                condition = self.condition,
                created_by = self.created_by,
                updated_by = self.updated_by
            ))
        BookItem.objects.bulk_create(book_items)
    
    def validate_codes(self):
        if not (self.codes or self.generate_codes_from):
            raise ValidationError("Codes and Generate Codes From can not both be null")
        if self.codes and self.generate_codes_from:
            raise ValidationError("Codes and Generate Codes From are mutually exclusive")
        if self.codes:
            codes = self.codes.split(",")
            if len(codes) != self.number_of_books:
                raise ValidationError(f"Number of codes ({len(codes)}) is not equal to number of books ({self.number_of_books})!")

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        self.validate_codes()
