"""
Data migration: seed AllowedEmailDomain with known Kenyan university domains.

If any existing users have a university text value that matches an
institution_name in this seed list, their university FK is set accordingly.
Users whose stored text does not match any seeded institution are left with
university=NULL so they are not silently mis-assigned.
"""
from django.db import migrations


KENYAN_UNIVERSITIES = [
    ("cuk.ac.ke",       "Co-operative University of Kenya"),
    ("uonbi.ac.ke",     "University of Nairobi"),
    ("ku.ac.ke",        "Kenyatta University"),
    ("jkuat.ac.ke",     "Jomo Kenyatta University of Agriculture and Technology"),
    ("mku.ac.ke",       "Mount Kenya University"),
    ("strathmore.edu",  "Strathmore University"),
    ("usiu.ac.ke",      "United States International University Africa"),
    ("dkut.ac.ke",      "Dedan Kimathi University of Technology"),
    ("egerton.ac.ke",   "Egerton University"),
    ("maseno.ac.ke",    "Maseno University"),
    ("mmust.ac.ke",     "Masinde Muliro University of Science and Technology"),
    ("tukenya.ac.ke",   "Technical University of Kenya"),
    ("must.ac.ke",      "Meru University of Science and Technology"),
    ("kabianga.ac.ke",  "University of Kabianga"),
    ("chuka.ac.ke",     "Chuka University"),
]


def seed_domains(apps, schema_editor):
    AllowedEmailDomain = apps.get_model("authentication", "AllowedEmailDomain")
    for domain, name in KENYAN_UNIVERSITIES:
        AllowedEmailDomain.objects.get_or_create(
            domain=domain,
            defaults={"institution_name": name, "is_active": True},
        )


def unseed_domains(apps, schema_editor):
    """Reverse: remove only the rows we inserted (leave any manually added ones)."""
    AllowedEmailDomain = apps.get_model("authentication", "AllowedEmailDomain")
    domains = [d for d, _ in KENYAN_UNIVERSITIES]
    AllowedEmailDomain.objects.filter(domain__in=domains).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_domains, reverse_code=unseed_domains),
    ]
