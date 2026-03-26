from django.db import migrations

KENYAN_UNIVERSITY_DOMAINS = [
    # Public Universities
    {"domain": "cuk.ac.ke",              "institution_name": "Co-operative University of Kenya"},
    {"domain": "uonbi.ac.ke",            "institution_name": "University of Nairobi"},
    {"domain": "ku.ac.ke",               "institution_name": "Kenyatta University"},
    {"domain": "jkuat.ac.ke",            "institution_name": "Jomo Kenyatta University of Agriculture and Technology"},
    {"domain": "mu.ac.ke",               "institution_name": "Moi University"},
    {"domain": "egerton.ac.ke",          "institution_name": "Egerton University"},
    {"domain": "maseno.ac.ke",           "institution_name": "Maseno University"},
    {"domain": "tukenya.ac.ke",          "institution_name": "Technical University of Kenya"},
    {"domain": "tum.ac.ke",              "institution_name": "Technical University of Mombasa"},
    {"domain": "mmust.ac.ke",            "institution_name": "Masinde Muliro University of Science and Technology"},
    {"domain": "dkut.ac.ke",             "institution_name": "Dedan Kimathi University of Technology"},
    {"domain": "chuka.ac.ke",            "institution_name": "Chuka University"},
    {"domain": "kisiiuniversity.ac.ke",  "institution_name": "Kisii University"},
    {"domain": "kabianga.ac.ke",         "institution_name": "University of Kabianga"},
    {"domain": "kyu.ac.ke",              "institution_name": "Kirinyaga University"},
    # Private Universities
    {"domain": "mku.ac.ke",              "institution_name": "Mount Kenya University"},
    {"domain": "daystar.ac.ke",          "institution_name": "Daystar University"},
    {"domain": "usiu.ac.ke",             "institution_name": "United States International University Africa"},
    {"domain": "cuea.edu",               "institution_name": "Catholic University of Eastern Africa"},
    {"domain": "strathmore.edu",         "institution_name": "Strathmore University"},
    {"domain": "spu.ac.ke",              "institution_name": "St. Paul's University"},
    {"domain": "anu.ac.ke",              "institution_name": "Africa Nazarene University"},
    {"domain": "kca.ac.ke",              "institution_name": "KCA University"},
    {"domain": "riarauniversity.ac.ke",  "institution_name": "Riara University"},
    {"domain": "gretsauniversity.ac.ke", "institution_name": "Gretsa University"},
    {"domain": "zetech.ac.ke",           "institution_name": "Zetech University"},
]


def seed_domains(apps, schema_editor):
    AllowedEmailDomain = apps.get_model("authentication", "AllowedEmailDomain")
    for entry in KENYAN_UNIVERSITY_DOMAINS:
        AllowedEmailDomain.objects.get_or_create(
            domain=entry["domain"],
            defaults={"institution_name": entry["institution_name"], "is_active": True},
        )


def unseed_domains(apps, schema_editor):
    AllowedEmailDomain = apps.get_model("authentication", "AllowedEmailDomain")
    domains = [e["domain"] for e in KENYAN_UNIVERSITY_DOMAINS]
    AllowedEmailDomain.objects.filter(domain__in=domains).delete()


class Migration(migrations.Migration):

    # ⚠️ Update this dependency to match your actual latest migration file
    dependencies = [
        ("authentication", "0003_allowedemaildomain"),
    ]

    operations = [
        migrations.RunPython(seed_domains, reverse_code=unseed_domains),
    ]
