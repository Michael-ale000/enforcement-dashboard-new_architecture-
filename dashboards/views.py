from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Count, Case, When, IntegerField, Min, Max,Sum,Q
from django.db.models.functions import TruncMonth
from dashboards.models import ArrestRecord,ArrestMonthlyChart,AORHeatMap
import pandas as pd
from datetime import datetime
from django.db import transaction
import json






# dashboards/constants.py

# US States (with "All" as default option)
STATES_FILTER_DROPDOWN = [
    "All",
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
    "Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas",
    "Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota",
    "Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey",
    "New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon",
    "Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas",
    "Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"
]

# Composition categories
COMPOSITIONS_DROPDOWN = [
    "All",
    "Gender",
    "Criminal History"
]

# Age categories
AGE_GROUPS_DROPDOWN = [
    "All",
    "Minors(0-17 years)",
    "Early Adult(18-35 years)",
    "Middle Adult(36-64 years)",
    "Older Adults(65+ years)"
]

# Distinct nationalities from your dataset (192 total)
NATIONALITIES_DROPDOWN = [
    "All",
    "AFGHANISTAN","ALBANIA","ALGERIA","ANGOLA","ANGUILLA","ANTIGUA-BARBUDA","ARGENTINA",
    "ARMENIA","AUSTRALIA","AUSTRIA","AZERBAIJAN","BAHAMAS","BAHRAIN","BANGLADESH",
    "BARBADOS","BELARUS","BELGIUM","BELIZE","BENIN","BHUTAN","BOLIVIA",
    "BOSNIA-HERZEGOVINA","BOTSWANA","BRAZIL","BRITISH VIRGIN ISLANDS","BRUNEI","BULGARIA",
    "BURKINA FASO","BURMA","BURUNDI","CAMBODIA","CAMEROON","CANADA","CAPE VERDE",
    "CAYMAN ISLANDS","CENTRAL AFRICAN REPUBLIC","CHAD","CHILE","CHINA, PEOPLES REPUBLIC OF",
    "COLOMBIA","CONGO","COSTA RICA","CROATIA","CUBA","CURACAO","CYPRUS",
    "CZECH REPUBLIC","CZECHOSLOVAKIA","DEM REP OF THE CONGO","DENMARK","DJIBOUTI",
    "DOMINICAN REPUBLIC","ECUADOR","EGYPT","EL SALVADOR","ERITREA","ESTONIA","ETHIOPIA",
    "FIJI","FINLAND","FRANCE","GABON","GAMBIA","GEORGIA","GERMANY","GHANA","GREECE",
    "GRENADA","GUATEMALA","GUINEA","GUINEA-BISSAU","GUYANA","HAITI","HONDURAS",
    "HONG KONG","HUNGARY","ICELAND","INDIA","INDONESIA","IRAN","IRAQ","IRELAND",
    "ISRAEL","ITALY","IVORY COAST","JAMAICA","JAPAN","JORDAN","KAZAKHSTAN","KENYA",
    "KIRIBATI","KOREA, NORTH","KOREA, SOUTH","KOSOVO","KUWAIT","KYRGYZSTAN","LAOS",
    "LATVIA","LEBANON","LESOTHO","LIBERIA","LIBYA","LIECHTENSTEIN","LITHUANIA",
    "LUXEMBOURG","MACEDONIA","MADAGASCAR","MALAWI","MALAYSIA","MALDIVES","MALI",
    "MALTA","MARSHALL ISLANDS","MAURITANIA","MAURITIUS","MEXICO","MICRONESIA","MOLDOVA",
    "MONACO","MONGOLIA","MONTENEGRO","MOROCCO","MOZAMBIQUE","NAMIBIA","NEPAL",
    "NETHERLANDS","NEW ZEALAND","NICARAGUA","NIGER","NIGERIA","NORWAY","OMAN",
    "PAKISTAN","PANAMA","PAPUA NEW GUINEA","PARAGUAY","PERU","PHILIPPINES","POLAND",
    "PORTUGAL","QATAR","ROMANIA","RUSSIA","RWANDA","SAUDI ARABIA","SENEGAL","SERBIA",
    "SEYCHELLES","SIERRA LEONE","SINGAPORE","SLOVAKIA","SLOVENIA","SOLOMON ISLANDS",
    "SOMALIA","SOUTH AFRICA","SPAIN","SRI LANKA","ST. KITTS-NEVIS","ST. LUCIA",
    "ST. VINCENT-GRENADINES","SUDAN","SURINAME","SWAZILAND","SWEDEN","SWITZERLAND",
    "SYRIA","TAIWAN","TAJIKISTAN","TANZANIA","THAILAND","TOGO","TONGA","TRINIDAD-TOBAGO",
    "TUNISIA","TURKEY","TURKMENISTAN","TUVALU","UGANDA","UKRAINE","UNITED ARAB EMIRATES",
    "UNITED KINGDOM","UNITED STATES","URUGUAY","UZBEKISTAN","VANUATU","VATICAN CITY",
    "VENEZUELA","VIETNAM","WEST BANK/GAZA","YEMEN","ZAMBIA","ZIMBABWE"
]
def get_or_create_monthlyarrest_data(from_date=None, to_date=None,
                          state=None, composition=None,
                          age_group=None, citizenship_country=None):
    """
    Step 1: Try to load from ArrestMonthlyChart (summary table).
    Step 2: If not found, compute from ArrestRecord and insert into summary.
    """

    #1.Try summary table first 
    qs = ArrestMonthlyChart.objects.all()

    if from_date:
        qs = qs.filter(month__gte=from_date)
    if to_date:
        qs = qs.filter(month__lte=to_date)
    if state and state != "All":
        qs = qs.filter(apprehension_state__iexact=state)   
    if age_group and age_group != "All":
        qs = qs.filter(age_category__iexact=age_group)     
    if citizenship_country and citizenship_country != "All":
        qs = qs.filter(citizenship_country__iexact=citizenship_country)  

    # Group by composition
    if composition == "Gender":
        qs = qs.filter(gender__isnull=False).values("month", "gender").order_by("month")
    elif composition == "Criminal History":
        qs = qs.filter(apprehension_criminality__isnull=False).values("month", "apprehension_criminality").order_by("month")
    else:
        qs = qs.values("month").order_by("month")

    data = list(qs.annotate(count=Sum("total")))  # sum totals already stored

    # 2. If no data in summary table, compute from raw records
    if not data:
        raw_qs = ArrestRecord.objects.all()

        if from_date:
            raw_qs = raw_qs.filter(apprehension_date__gte=from_date)
        if to_date:
            raw_qs = raw_qs.filter(apprehension_date__lte=to_date)
        if state and state != "All":
            raw_qs = raw_qs.filter(apprehension_state__iexact=state)
        if age_group and age_group != "All":
            raw_qs = raw_qs.filter(age_category__iexact=age_group)
        if citizenship_country and citizenship_country != "All":
            raw_qs = raw_qs.filter(citizenship_country__iexact=citizenship_country)

        # Compute aggregates depending on composition
        if composition == "Gender":
            raw_data = (
                raw_qs.exclude(gender='Unknown')
                      .annotate(month=TruncMonth("apprehension_date"))
                      .values("month", "gender")
                      .annotate(count=Count("id"))
                      .order_by("month")
            )
        elif composition == "Criminal History":
            raw_data = (
                raw_qs.values('apprehension_criminality')
                      .annotate(month=TruncMonth("apprehension_date"))
                      .values("month", "apprehension_criminality")
                      .annotate(count=Count("id"))
                      .order_by("month")
            )
        else:  # All
            raw_data = (
                raw_qs.annotate(month=TruncMonth("apprehension_date"))
                      .values("month")
                      .annotate(count=Sum("total"))
                      .order_by("month")
            )

        data = list(raw_data)

        # --- Step 3: Save to summary table ---
        with transaction.atomic():
            for row in data:
                ArrestMonthlyChart.objects.create(
                    month=row["month"],
                    apprehension_state=state if state != "All" else 'All',
                    age_category=age_group if age_group != "All" else 'All',
                    citizenship_country=citizenship_country if citizenship_country != "All" else 'All',
                    gender=row.get("gender"),
                    apprehension_criminality=row.get("apprehension_criminality"),
                    total=row["count"]
                )

    return data

# def get_or_create_aor_heatmap_data(from_date=None, to_date=None,
#                           state=None,age_group=None, citizenship_country=None):
#     qs = AORHeatMap.objects.all()
#     if from_date:
#         qs = qs.filter(month__gte=from_date)
#     if to_date:
#         qs = qs.filter(month__lte=to_date)
#     if state and state != "All":
#         qs = qs.filter(apprehension_state__iexact=state)   
#     if age_group and age_group != "All":
#         qs = qs.filter(age_category__iexact=age_group)     
#     if citizenship_country and citizenship_country != "All":
#         qs = qs.filter(citizenship_country__iexact=citizenship_country)
    
#     data = list(
#         qs.values("apprehension_aor")
#           .annotate(count=Sum("total"))
#           .order_by("apprehension_aor")
#     )

#     if not data:
#         raw_qs = ArrestRecord.objects.all()
#         if from_date:
#             raw_qs = raw_qs.filter(apprehension_date__gte=from_date)
#         if to_date:
#             raw_qs = raw_qs.filter(apprehension_date__lte=to_date)
#         if state and state != "All":
#             raw_qs = raw_qs.filter(apprehension_state__iexact=state)
#         if age_group and age_group != "All":
#             raw_qs = raw_qs.filter(age_category__iexact=age_group)
#         if citizenship_country and citizenship_country != "All":
#             raw_qs = raw_qs.filter(citizenship_country__iexact=citizenship_country)

#         raw_data = (
#             raw_qs.values('apprehension_aor')
#                   .annotate(count=Count("id"))
#                   .order_by("apprehension_aor")
#         )

#         data = list(raw_data)
#         total_sum = sum(row["count"] for row in data) or 1  # avoid division by zero
#         with transaction.atomic():
#             for row in data:
#                 percent = (row["count"] / total_sum) * 100
#                 AORHeatMap.objects.create(
#                     apprehension_state=state if state != "All" else "All",
#                     age_category=age_group if age_group != "All" else "All",
#                     citizenship_country=citizenship_country if citizenship_country != "All" else "All",
#                     apprehension_aor=row["apprehension_aor"],
#                     total=row["count"],
#                     percent_of_total=round(percent, 2),
#                 )
#     else:
#         total_sum = sum(row["count"] for row in data) or 1
#         for row in data:
#             row["percent_of_total"] = round((row["total_sum"] / total_sum) * 100, 2)
#     return data

def get_or_create_aor_heatmap_data(from_date=None, to_date=None,
                                   state=None, age_group=None, citizenship_country=None):

    # --- Step 1: Try loading from summary table (AORHeatMap) ---
    qs = AORHeatMap.objects.all()

    if from_date:
        qs = qs.filter(month__gte=from_date)
    if to_date:
        qs = qs.filter(month__lte=to_date)
    if state and state != "All":
        qs = qs.filter(apprehension_state__iexact=state)
    if age_group and age_group != "All":
        qs = qs.filter(age_category__iexact=age_group)
    if citizenship_country and citizenship_country != "All":
        qs = qs.filter(citizenship_country__iexact=citizenship_country)

    # Aggregate totals by AOR
    data = list(
        qs.values("apprehension_aor")
          .annotate(count=Sum("total"))
          .order_by("apprehension_aor")
    )

    # --- Step 2: If no data found in summary table, compute from raw arrests ---
    if not data:
        raw_qs = ArrestRecord.objects.all()
        if from_date:
            raw_qs = raw_qs.filter(apprehension_date__gte=from_date)
        if to_date:
            raw_qs = raw_qs.filter(apprehension_date__lte=to_date)
        if state and state != "All":
            raw_qs = raw_qs.filter(apprehension_state__iexact=state)
        if age_group and age_group != "All":
            raw_qs = raw_qs.filter(age_category__iexact=age_group)
        if citizenship_country and citizenship_country != "All":
            raw_qs = raw_qs.filter(citizenship_country__iexact=citizenship_country)

        raw_data = (
            raw_qs.values("apprehension_aor")
                  .annotate(count=Count("id"))
                  .order_by("apprehension_aor")
        )

        data = list(raw_data)

        # --- Step 3: Compute percent of total and store in DB ---
        total_sum = sum(row["count"] for row in data) or 1  # avoid division by zero
        with transaction.atomic():
            for row in data:
                percent = (row["count"] / total_sum) * 100
                AORHeatMap.objects.create(
                    apprehension_state=state if state != "All" else "All",
                    age_category=age_group if age_group != "All" else "All",
                    citizenship_country=citizenship_country if citizenship_country != "All" else "All",
                    apprehension_aor=row["apprehension_aor"],
                    total=row["count"],
                    percent_of_total=round(percent, 2),
                )

    # --- Step 4: If data exists, calculate percent_of_total dynamically ---
    else:
        total_sum = sum(row["count"] for row in data) or 1
        for row in data:
            row["percent_of_total"] = round((row["count"] / total_sum) * 100, 2)

            # Optional: update stored percent in DB for consistency
            AORHeatMap.objects.filter(apprehension_aor=row["apprehension_aor"]).update(
                percent_of_total=row["percent_of_total"]
            )

    return data

def arrests_dashboard(request):
    state = request.GET.get("state", "All")
    composition = request.GET.get("composition", "All")
    age_group = request.GET.get("age_group", "All")
    citizenship_country = request.GET.get("nationality_group", "All")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    monthly_arrest_aggregated_data = get_or_create_monthlyarrest_data(from_date, to_date, state, composition,age_group,citizenship_country)
    aor_heatmap_data = get_or_create_aor_heatmap_data(from_date,to_date,state,age_group,citizenship_country)

    context = {
        "monthly_arrest_aggregated_data": json.dumps(list(monthly_arrest_aggregated_data), default=str),
        "aor_heatmap_data": json.dumps(list(aor_heatmap_data), default=str),
        "selected_state": state,
        "selected_composition": composition,
        "selected_age_group": age_group,
        "selected_citizenship_country": citizenship_country,
        "from_date": from_date,
        "to_date": to_date,
        "states": STATES_FILTER_DROPDOWN,
        "compositions": COMPOSITIONS_DROPDOWN,
        "age_groups": AGE_GROUPS_DROPDOWN,
        "nationalities": NATIONALITIES_DROPDOWN,
    }
    return render(request, "arrests.html", context)


# def arrests_dashboard(request):
    

#     return render(request, 'arrests.html')




def documentation(request):
    return render(request, 'documentation.html')

def detainers_dashboard(request):
    return render(request, 'detainers.html')

def detentions_dashboard(request):
    return render(request, 'detentions.html')

def encounters_dashboard(request):
    return render(request, 'encounters.html')

def removals_dashboard(request):
    return render(request, 'removals.html')
