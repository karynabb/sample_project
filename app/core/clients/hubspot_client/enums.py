from enum import Enum


class ErrorReason(Enum):
    """
    Error reason returned by the HubSpot.
    """

    CONFLICT = "Conflict"  # Object already exists


class AssociationCategory(Enum):
    """
    HubSpot association categories and their correponding labels.

    https://developers.hubspot.com/docs/api/crm/associations
    """

    HUBSPOT_DEFINED = "HUBSPOT_DEFINED"
    USER_DEFINED = "USER_DEFINED"


class AssociationType(Enum):
    """
    HubSpot association types and their correponding IDs.

    https://developers.hubspot.com/docs/api/crm/associations
    """

    DEAL_TO_CONTACT = 3


class FilterOperators(Enum):
    """
    HubSpot filter operators for the search endpoint.

    https://developers.hubspot.com/docs/api/crm/search
    """

    EQUALS = "EQ"


class DealStage(Enum):
    """
    Stages of the HubSpot Deals

    More info on deals and stage pipelines:
    https://knowledge.hubspot.com/crm-deals/set-up-and-customize-your-deal-pipelines-and-deal-stages
    """

    CLOSED_WON = "closedwon"


class LifecycleStage(Enum):
    """
    Lifecycle stages of a HubSpot Contact

    https://knowledge.hubspot.com/contacts/use-lifecycle-stages
    """

    LEAD = "lead"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
