from django.db import models
from djongo import models
from django import forms

# Create your models here.
class Feature(models.Model):
    header = models.CharField()
    description = models.CharField()

    class Meta:
        abstract = True

class FeatureForm(forms.ModelForm):
    class Meta:
        model = Feature
        fields = ('header', 'description')

class MainSection(models.Model):
    header = models.CharField()
    section_type = models.CharField(max_length=255)
    description = models.CharField()

    class Meta:
        abstract = True

class MainSectionForm(forms.ModelForm):
    class Meta:
        model = MainSection
        fields = ('header', 'section_type', 'description')

class Website(models.Model):
    _id = models.ObjectIdField()
    website_name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    plan = models.IntegerField()
    payment_amount = models.FloatField()
    template_id = models.IntegerField()
    company_name = models.CharField(max_length=255)
    twitter_profile = models.CharField(max_length=255)
    facebook_profile = models.CharField(max_length=255)
    product_description = models.CharField(max_length=512)
    product_image_url = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)