import re

from django.apps import apps


HMS_APPS = (
    "accounts",
    "allocation",
    "audit",
    "complaints",
    "core",
    "fees",
    "reports",
)


def test_hms_models_do_not_store_card_data():
    forbidden_substrings = re.compile(r"card|cvv|expiry", re.IGNORECASE)
    violations = []

    for app_name in HMS_APPS:
        models = apps.get_app_config(app_name).get_models()
        for model in models:
            for field in model._meta.get_fields():
                field_name = field.name
                if (
                    forbidden_substrings.search(field_name)
                    or "pan" in field_name.casefold().split("_")
                ):
                    violations.append(f"{model._meta.label}.{field_name}")

    assert not violations, (
        "HMS model fields must not store card data; offending fields: "
        + ", ".join(violations)
    )
