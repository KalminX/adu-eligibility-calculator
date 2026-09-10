"""
Views for ADU Eligibility Calculator.
Handles introduction, questionnaire progress, and eligibility result presentation.
"""

from django.shortcuts import render, redirect
from django.urls import reverse
from .eligibility import QUESTIONS, calculate_eligibility
from .forms import QuestionnaireForm


def index(request):
    """Landing page introducing the ADU Eligibility Calculator prototype."""
    return render(
        request,
        "calculator/index.html",
        {
            "questions_count": len(QUESTIONS),
        },
    )


def questions_view(request):
    """
    Renders and processes the 7-question eligibility assessment.
    Stores validated answers in session.
    """
    initial_data = request.session.get("adu_answers", {})

    if request.method == "POST":
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            request.session["adu_answers"] = form.cleaned_data
            return redirect("calculator:result")
    else:
        form = QuestionnaireForm(initial=initial_data)

    return render(
        request,
        "calculator/questions.html",
        {
            "form": form,
            "questions": QUESTIONS,
        },
    )


def result_view(request):
    """
    Calculates eligibility deterministically from session answers and renders outcome.
    Redirects back to questions if session data is missing.
    """
    answers = request.session.get("adu_answers")
    if not answers:
        return redirect("calculator:questions")

    result = calculate_eligibility(answers)

    # Store calculation in session for the lead form
    request.session["eligibility_result"] = result.status

    # Build cleanly formatted list of responses for human display in template (no raw JSON/dict)
    from .eligibility import normalize_bool
    formatted_responses = []
    for q in QUESTIONS:
        val = answers.get(q["id"])
        is_yes = normalize_bool(val)
        formatted_responses.append(
            {
                "id": q["id"],
                "text": q["text"],
                "answer_text": "Yes" if is_yes else "No",
                "is_yes": is_yes,
            }
        )

    return render(
        request,
        "calculator/result.html",
        {
            "result": result,
            "formatted_responses": formatted_responses,
        },
    )


def restart_view(request):
    """Clears calculator session data and redirects to homepage."""
    request.session.pop("adu_answers", None)
    request.session.pop("eligibility_result", None)
    return redirect("calculator:index")
