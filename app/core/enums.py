from enum import Enum


class DonationSourceEnum(Enum):
    SECONDARY = "Secondary"
    APP = "App"

    @classmethod
    def choices(cls) -> tuple:
        return tuple((element.value, element.value) for element in cls)


class DonationEmailTemplateType(Enum):
    SECONDARY = "Secondary"
    APP = "App"
