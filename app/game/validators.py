from rest_framework.exceptions import ValidationError

from app.algorithm.models import Result


def validate_options_id_list(value):
    if len(value) != len(set(value)):
        raise ValidationError("The options_id_list must not contain duplicate values.")

    options = Result.objects.filter(id__in=value)
    if options.count() != len(value):
        raise ValidationError(f"Missing Results from id list {value}.")

    for option in options:
        if not option.offering_description or not option.offering_description.strip():
            raise ValidationError("The offering_description must not be empty.")
        if not option.rationale.strip():
            raise ValidationError("The rationale must not be empty.")
