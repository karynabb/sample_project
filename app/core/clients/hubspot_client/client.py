import logging
from typing import cast

from django.conf import settings
from django.utils.functional import SimpleLazyObject
from hubspot import HubSpot
from hubspot.crm import contacts, deals
from hubspot.crm.contacts.exceptions import (
    NotFoundException as ContactNotFoundException,
)

from .enums import (
    AssociationCategory,
    AssociationType,
    DealStage,
    ErrorReason,
    FilterOperators,
    LifecycleStage,
)
from .exceptions import ContactDoesNotExistException

logger = logging.getLogger(__name__)


class HubSpotClient:
    _client: HubSpot

    def __init__(self, access_token: str = settings.HUBSPOT_ACCESS_TOKEN):
        self._client = HubSpot(access_token=access_token)

    def create_contact(self, email: str, first_name: str = "", last_name: str = ""):
        """
        Creates a new HubSpot contact with the given email.

        Example response from the HubSpot:
            {
                'archived': False,
                'archived_at': None,
                'created_at': datetime.datetime(2023, 8, 29, 23, 56, 35, 652000, tzinfo=tzlocal()),
                'id': '1051',
                'properties': {
                    'createdate': '2023-08-29T23:56:35.652Z',
                    'email': 'user@example.com',
                    'firstname': 'a',
                    'hs_all_contact_vids': '1051',
                    'hs_email_domain': 'test.com',
                    'hs_is_contact': 'true',
                    'hs_is_unworked': 'true',
                    'hs_lifecyclestage_lead_date': '2023-08-29T23:56:35.652Z',
                    'hs_marketable_status': 'false',
                    'hs_marketable_until_renewal': 'false',
                    'hs_object_id': '1051',
                    'hs_object_source': 'INTEGRATION',
                    'hs_object_source_id': '2056460',
                    'hs_pipeline': 'contacts-lifecycle-pipeline',
                    'lastmodifieddate': '2023-08-29T23:56:35.652Z',
                    'lastname': 'b',
                    'lifecyclestage': 'lead'
                },
                'properties_with_history': None,
                'updated_at': datetime.datetime(2023, 8, 29, 23, 56, 35, 652000, tzinfo=tzlocal())
            }
        """
        try:
            if first_name and last_name:
                contact = contacts.SimplePublicObjectInputForCreate(
                    properties={
                        "email": email,
                        "firstname": first_name,
                        "lastname": last_name,
                    }
                )

            else:
                contact = contacts.SimplePublicObjectInputForCreate(
                    properties={"email": email}
                )
            self._client.crm.contacts.basic_api.create(
                simple_public_object_input_for_create=contact
            )
        except contacts.ApiException as e:
            if e.reason == ErrorReason.CONFLICT.value:
                logger.warning(
                    f"Contact with email {email} already exists in the HubSpot."
                )
                return
            logger.error(
                f"Unexpected error when creating HubSpot contact for user {email}: {e}"
            )
            raise e

    def get_contact_id_by_email(self, email: str) -> str:
        """
        Returns id of the contact with the given email.

        Example responses from the HubSpot:

            Contact exists:
                {
                    'paging': None,
                    'results': [
                        {
                            'archived': False,
                            'archived_at': None,
                            'created_at': datetime.datetime(
                                2023, 8, 30, 0, 9, 27, 93000, tzinfo=tzlocal()
                            ),
                            'id': '1151',
                            'properties': {
                                'createdate': '2023-08-30T00:09:27.093Z',
                                'email': 'user@example.com',
                                'firstname': None,
                                'hs_object_id': '1151',
                                'lastmodifieddate': '2023-08-30T00:09:43.663Z',
                                'lastname': None
                            },
                            'properties_with_history': None,
                            'updated_at': datetime.datetime(
                                2023, 8, 30, 0, 9, 43, 663000, tzinfo=tzlocal()
                            )
                        }
                    ],
                    'total': 1
                }

            Contact does not exist:
                {
                    'paging': None,
                    'results': [],
                    'total': 0
                }
        """
        search_request = contacts.PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "value": email,
                            "propertyName": "email",
                            "operator": FilterOperators.EQUALS.value,
                        }
                    ]
                }
            ]
        )
        try:
            api_response = self._client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )
            if not api_response.results:
                raise ContactDoesNotExistException(
                    f"Couldn't find HubSpot contact with {email=}"
                )
            return api_response.results[0].id
        except contacts.ApiException as e:
            logger.error(
                f"Unexpected error when searching for HubSpot contact for user {email}: {e}"
            )
            raise e

    def update_lifecycle_stage(self, email: str, stage: LifecycleStage):
        contact = contacts.SimplePublicObjectInputForCreate(
            properties={"lifecyclestage": stage.value}
        )
        try:
            self._client.crm.contacts.basic_api.update(
                contact_id=email,
                simple_public_object_input=contact,
                id_property="email",
            )
        except ContactNotFoundException as e:
            logger.error(f"Could not find HubSpot contact for user {email}: {e}")
            raise e
        except contacts.ApiException as e:
            logger.error(
                "Unexpected error when updating lifecycle stage "
                f"of HubSpot contact for user {email}: {e}"
            )
            raise e

    def create_deal(self, email: str, payment_type: str, amount: int):
        contact_id = self.get_contact_id_by_email(email)
        try:
            amount_in_dollars = f"{amount / 100:.2f}"
            deal = deals.SimplePublicObjectInputForCreate(
                properties={
                    "amount": amount_in_dollars,
                    "dealname": payment_type,
                    "dealstage": DealStage.CLOSED_WON.value,
                },
                associations=[
                    {
                        "to": {"id": contact_id},
                        "types": [
                            {
                                "associationCategory": AssociationCategory.HUBSPOT_DEFINED.value,
                                "associationTypeId": AssociationType.DEAL_TO_CONTACT.value,
                            }
                        ],
                    }
                ],
            )
            self._client.crm.deals.basic_api.create(
                simple_public_object_input_for_create=deal
            )
        except deals.ApiException as e:
            logger.error(f"Exception when creating HubSpot deal for user {email}: {e}")
            raise e


hubspot_client = cast(HubSpotClient, SimpleLazyObject(HubSpotClient))
