import re
from datetime import datetime
from random import sample

from django.db.models import QuerySet

from app.algorithm.models import LMMCache, NameCandidate, Pathway, Result
from app.core.models import Questionnaire
from app.tracker.models import QueryLog


def validate_new_name_candidate(questionnaire: Questionnaire, new_name: str):
    """Validates uniqueness of the name across all related questionnaires"""
    valid_pks = [questionnaire.pk]
    if questionnaire.parent:
        valid_pks.append(questionnaire.parent.pk)
    if questionnaire.siblings:
        valid_pks.append(questionnaire.siblings.values_list("pk", flat=True))
    results_with_name = Result.objects.filter(
        name=new_name, batch__questionnaire__pk__in=valid_pks
    )
    candidates_with_name = NameCandidate.objects.filter(
        name=new_name, questionnaire__pk__in=valid_pks
    )
    if results_with_name.exists() or candidates_with_name.exists():
        raise ValueError("Result or Candidate with that name already exists.")


def random_ids_from_qs(queryset: QuerySet, quantity=1):
    all_ids = list(queryset.values_list("id", flat=True))
    if quantity > len(all_ids):  # avoids ValueError from sample
        return all_ids
    return sample(all_ids, quantity)


def candidates_from_pathway(pathway, questionnaire):
    pathway_candidates = NameCandidate.objects.filter(
        pathway=pathway, questionnaire=questionnaire
    )
    return random_ids_from_qs(pathway_candidates, quantity=pathway.candidates_per_batch)


def questionnaire_data_to_algorithm_representation(answers: dict):
    results = {}
    list_keys = ["FA", "FN", "DRA", "DN", "V", "EA", "EN", "EDA", "MA", "UCA", "UCN"]
    optional_keys = ["RA", "GN1"]
    constant_keys = ["CN1", "CN2", "N1", "N2"]
    for _key in list_keys:
        for index, value in enumerate(answers[_key], 1):
            results[f"{_key}{index}"] = value
    for _key in optional_keys:
        if value := answers.get(_key):
            results[_key] = value
    for _key in constant_keys:
        results[_key] = answers[_key]
    return results


def log_pathway_usage(
    pathway_code: str, questionnaire: Questionnaire, algorithm_return: list[dict]
):
    pathway = Pathway.objects.get(code=pathway_code)
    for log_dict in algorithm_return:
        create_log_from_dict(log_dict, pathway, questionnaire)


def create_log_from_dict(
    log_dict, pathway: Pathway, questionnaire: Questionnaire
) -> QueryLog:
    return QueryLog.objects.create(
        pathway=pathway,
        questionnaire=questionnaire,
        query=log_dict["query"],
        start_time=datetime.fromtimestamp(log_dict["start_time"]),
        end_time=datetime.fromtimestamp(log_dict["end_time"]),
        tokens_consumed=log_dict["tokens_consumed"],
        input_word=log_dict["input_word"],
    )


def create_cache(pathway: Pathway, questionnaire: Questionnaire, cache: list):
    try:
        LMMCache.objects.get(pathway=pathway, questionnaire=questionnaire)
    except LMMCache.DoesNotExist:
        LMMCache.objects.create(
            pathway=pathway, questionnaire=questionnaire, cache=cache
        )


def retrieve_cache(pathway: Pathway, questionnaire: Questionnaire):
    try:
        cache_object = LMMCache.objects.get(
            pathway=pathway, questionnaire=questionnaire
        )
        return cache_object.cache
    except LMMCache.DoesNotExist:
        return None


def capitalize_name(name: str) -> str:
    """
    Capitalize each word's first letter and preserve existing uppercase letters.
    Strips leading and trailing special characters from each word before capitalization.
    """
    if not name:
        return ""

    words: list[str] = name.split()
    capitalized_words: list[str] = []

    for word in words:
        stripped_word = word.strip("[]{}()<>,.;:!@#$%^&*-_+=/\\\"'`~|?")
        if stripped_word:
            capitalized_word = stripped_word[0].upper() + stripped_word[1:]
            capitalized_words.append(capitalized_word)

    return " ".join(capitalized_words)


def capitalize_rationale(name: str, rationale: str) -> str:
    """
    Capitalize name in the rationale regardless of the place name appear.
    """
    capitalized_name = capitalize_name(name=name)
    cleaned_rationale = re.sub(r"['\"]", "", rationale)

    sentences = re.split(r"(?<=[.!?])\s+", cleaned_rationale)

    capitalized_sentences = []
    for sentence in sentences:
        if sentence.lower().startswith(capitalized_name.lower()):
            capitalized_sentence = capitalized_name + sentence[len(capitalized_name) :]
        else:
            capitalized_sentence = sentence.capitalize()
        capitalized_sentences.append(capitalized_sentence)

    cleaned_rationale = " ".join(capitalized_sentences)

    capitalized_words = capitalize_name(name=name).split()
    for word in capitalized_words:
        cleaned_rationale = re.sub(
            rf"(?i)\b{re.escape(word)}\b", word, cleaned_rationale
        )

    return cleaned_rationale
