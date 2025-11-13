from django.db import models
from django.db.models import Q, Count, Avg
# for raw data
class ArrestRecord(models.Model):
    apprehension_date = models.DateField(null=True, blank=True, db_index=True)
    apprehension_state = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    apprehension_aor = models.CharField(max_length=100, null=True, blank=True)
    apprehension_criminality = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    birth_year = models.IntegerField(null=True, blank=True)
    citizenship_country = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    gender = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    unique_identifier = models.CharField(max_length=100, null=True, blank=True, unique=True)
    age = models.IntegerField(null=True, blank=True)
    age_category = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    class Meta:
        db_table = "arrest_record"
        indexes = [
            # Common two-field combinations with date
            models.Index(fields=['apprehension_state', 'apprehension_date']),
            models.Index(fields=['age_category', 'apprehension_date']),
            models.Index(fields=['gender', 'apprehension_date']),
            models.Index(fields=['citizenship_country', 'apprehension_date']),
            models.Index(fields=['apprehension_criminality', 'apprehension_date']),

            # Multi-field combinations for frequent filter usage
            models.Index(fields=['apprehension_state', 'age_category', 'apprehension_date']),
            models.Index(fields=['apprehension_state', 'gender', 'apprehension_date']),
            models.Index(fields=['apprehension_state', 'citizenship_country', 'apprehension_date']),
            models.Index(fields=['age_category', 'gender', 'apprehension_date']),
            models.Index(fields=['age_category', 'citizenship_country', 'apprehension_date']),

            # Optional single-field indexes
            models.Index(fields=['apprehension_state']),
            models.Index(fields=['age_category']),
            models.Index(fields=['apprehension_date']),
        ]
        ordering = ['-apprehension_date', 'apprehension_state']

    def __str__(self):
        return f"{self.unique_identifier} | {self.apprehension_state} | {self.apprehension_criminality}"


class ArrestMonthlyChart(models.Model):
    apprehension_state = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    month = models.DateField(null=True,blank=True,db_index=True)
    gender = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    apprehension_criminality = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    citizenship_country = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    age_category = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    total = models.IntegerField(default=0)

    class Meta:
        db_table = "arrest_monthly_chart"



class AORHeatMap(models.Model):
    apprehension_state = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    apprehension_aor = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    month = models.DateField(null=True,blank=True,db_index=True)
    citizenship_country = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    age_category = models.CharField(max_length=50, null=True, blank=True, db_index=True)    
    total = models.IntegerField(default=0)
    percent_of_total = models.FloatField(default=0.0)
    class Meta:
        db_table = "aor_heat_map"
