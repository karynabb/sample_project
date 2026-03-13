from django.urls import path

from app.core import views

urlpatterns = [
    path(
        "questionnaire/create/",
        views.CreateQuestionnaireView.as_view(),
        name="questionnaire_create",
    ),
    path(
        "questionnaire/<int:id>/",
        views.QuestionnaireDetailView.as_view(),
        name="questionnaire_detail",
    ),
    path(
        "questionnaire/list/",
        views.QuestionnaireListView.as_view(),
        name="questionnaire_list",
    ),
    path(
        "questionnaire/create_child/<int:id>/",
        views.CreateChild.as_view(),
        name="questionnaire_create_child",
    ),
    path(
        "draft/create/",
        views.CreateDraftQuestionnaireView.as_view(),
        name="draft_create",
    ),
    path(
        "draft/<int:id>/",
        views.DraftQuestionnaireDetailView.as_view(),
        name="draft_detail",
    ),
    path(
        "draft/list/",
        views.DraftListView.as_view(),
        name="draft_list",
    ),
    path(
        "draft/complete/<int:id>", views.CompleteDraft.as_view(), name="complete_draft"
    ),
    path("user/", views.UpdateAndViewUserInfo.as_view(), name="user_management"),
    path("payments/webhook", views.stripe_payment_webhook, name="payments_webhook"),
    path(
        "payments/webhook/<str:source>",
        views.stripe_payment_webhook,
        name="payments_webhook_source",
    ),
    path(
        "payments/create/",
        views.CreatePayment.as_view(),
        name="payments_create",
    ),
    path(
        "payments/buy_more/",
        views.BuyMore.as_view(),
        name="payments_buy_more",
    ),
    path(
        "payments/donate/",
        views.MakeDonation.as_view(),
        name="payments_donation",
    ),
    path(
        "gift-cards/buy",
        views.get_gift_card_session,
        name="gift_cards_buy",
    ),
    path(
        "gift-cards/email",
        views.get_email_with_promo_codes,
        name="gift_cards_email",
    ),
    path("payments/info/<int:id>/", views.PaymentInfo.as_view(), name="payments_info"),
    path("results/<int:id>/", views.ResultsListView.as_view(), name="results"),
    path(
        "presentation/<int:id>/",
        views.PresentationListView.as_view(),
        name="presentation",
    ),
    path("feedback/<int:id>/", views.FeedBackUpdateView.as_view(), name="feedback"),
    path("continue/", views.ContinueView.as_view(), name="continue"),
    path("feature-config/", views.FeatureConfigRetrieveView.as_view(), name="config"),
]
