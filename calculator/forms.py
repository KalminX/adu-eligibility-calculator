"""
Questionnaire form for ADU eligibility calculation.
"""

from django import forms
from .eligibility import QUESTIONS

YES_NO_CHOICES = [
    ("yes", "Yes"),
    ("no", "No"),
]


class QuestionnaireForm(forms.Form):
    """
    Form validating the 7 core eligibility questions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for q in QUESTIONS:
            q_id = q["id"]
            self.fields[q_id] = forms.ChoiceField(
                label=q["text"],
                help_text=q["help_text"],
                choices=YES_NO_CHOICES,
                widget=forms.RadioSelect(
                    attrs={
                        "class": "sr-only peer",
                    }
                ),
                required=True,
                error_messages={
                    "required": f"Please select Yes or No for '{q['text']}'",
                },
            )

    def clean(self):
        cleaned = super().clean()
        # Ensure all 7 questions have valid answers
        for q in QUESTIONS:
            val = cleaned.get(q["id"])
            if val not in ("yes", "no"):
                self.add_error(q["id"], "Selection is required.")
        return cleaned
