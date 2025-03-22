# >>> from scripts.find_duplicates import get_duplicates
# >>> get_duplicates()
from django.db.models import Count

from consultation_analyser.consultations.models import (
    Answer,
    Consultation,
    Question,
    QuestionPart,
    Theme,
    ThemeMapping,
)


def get_latest_consultation() -> Consultation:
    return Consultation.objects.latest("created_at")


def get_duplicate_theme_mappings(
    consultation: Consultation, question_number: int
) -> list[ThemeMapping]:
    question = Question.objects.get(consultation=consultation, number=question_number)
    question_part = QuestionPart.objects.get(
        question=question, type=QuestionPart.QuestionType.FREE_TEXT
    )  # Assumes just one part per question
    theme_mappings_for_question = ThemeMapping.objects.filter(answer__question_part=question_part)

    # Concerning theme_mappings are those where there is a duplicate and:
    # - The first mapping does not have stance
    # - There is more than one history object or history object is not "+" (adding)
    # - The first theme mapping is not user_audited
    concerning_theme_mappings = []

    # Annotate the count of each group of (answer, theme)
    duplicates = (
        theme_mappings_for_question.values("answer", "theme")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    # Print the duplicates
    for duplicate in duplicates:
        print("-----------------")
        answer = Answer.objects.get(id=duplicate["answer"])
        theme = Theme.objects.get(id=duplicate["theme"])
        print(f"Theme finder ID: {answer.respondent.themefinder_respondent_id}")
        print(f"Answer: {duplicate['answer']}")
        print(f"Theme: {duplicate['theme']}, Theme name: {theme.name}, Theme key: {theme.key}")
        print(f"Count: {duplicate['count']}")
        theme_mappings = ThemeMapping.objects.filter(answer=answer, theme=theme).order_by(
            "created_at"
        )
        if not theme_mappings[0].user_audited:
            concerning_theme_mappings.append(theme_mappings[0])
        if not theme_mappings[0].stance:
            concerning_theme_mappings.append(theme_mappings[0])
        for theme_mapping in theme_mappings:
            print(f"Theme mapping ID: {theme_mapping.id}")
            print(f"Theme mapping user audited: {theme_mapping.user_audited}")
            if theme_mapping.history.count() > 1:
                concerning_theme_mappings.append(theme_mapping)
            if theme_mapping.history.exclude(history_type="+").count() > 0:
                concerning_theme_mappings.append(theme_mapping)

    return concerning_theme_mappings


def get_duplicates():
    consultation = get_latest_consultation()
    print(f"Consultation: {consultation.title}")
    num_questions = Question.objects.filter(consultation=consultation).count()
    for number in range(1, num_questions):
        print("=================")
        print(f"Question {number}")
        concerning_theme_mappings = get_duplicate_theme_mappings(consultation, number)
        print("concerning theme mappings")
        print(concerning_theme_mappings)


## Result of the analysis

# Whilst there are duplicates, they don't contain any extra information.
# All the first themes have been user audited, have a stance.
# We can't see anything in the history which explains why there are duplicates.
# Each theme mapping (for duplicates) has just one element in history.
