"""
Comprehensive unit and integration tests for the Calculator app.
Tests eligibility logic, question matrix, forms, and view lifecycle.
"""

from django.test import TestCase, Client
from django.urls import reverse
from calculator.eligibility import (
    calculate_eligibility,
    normalize_bool,
    QUESTIONS,
    STATUS_ELIGIBLE,
    STATUS_REVIEW,
    STATUS_UNLIKELY,
)
from calculator.forms import QuestionnaireForm


class EligibilityLogicTestCase(TestCase):
    """
    Validates deterministic decision logic across multiple property conditions.
    """

    def setUp(self):
        self.base_eligible_answers = {
            "owns_property": "yes",
            "located_in_california": "yes",
            "is_residential": "yes",
            "is_single_family": "yes",
            "has_sufficient_space": "yes",
            "has_existing_structure": "yes",
            "has_restrictions": "no",
        }

    def test_all_qualifying_answers_yields_potentially_eligible(self):
        result = calculate_eligibility(self.base_eligible_answers)
        self.assertEqual(result.status, STATUS_ELIGIBLE)
        self.assertEqual(result.status_code, "eligible")
        self.assertTrue(len(result.key_factors) >= 4)
        self.assertIn("California", result.summary)

    def test_non_owner_is_unlikely_to_qualify(self):
        answers = dict(self.base_eligible_answers)
        answers["owns_property"] = "no"
        result = calculate_eligibility(answers)
        self.assertEqual(result.status, STATUS_UNLIKELY)
        self.assertEqual(result.status_code, "unlikely")
        self.assertTrue(any("ownership" in f.lower() for f in result.key_factors))

    def test_non_residential_is_unlikely_to_qualify(self):
        answers = dict(self.base_eligible_answers)
        answers["is_residential"] = "no"
        result = calculate_eligibility(answers)
        self.assertEqual(result.status, STATUS_UNLIKELY)
        self.assertEqual(result.status_code, "unlikely")
        self.assertTrue(any("residential" in f.lower() for f in result.key_factors))

    def test_no_space_and_no_structure_is_unlikely_to_qualify(self):
        answers = dict(self.base_eligible_answers)
        answers["has_sufficient_space"] = "no"
        answers["has_existing_structure"] = "no"
        result = calculate_eligibility(answers)
        self.assertEqual(result.status, STATUS_UNLIKELY)
        self.assertEqual(result.status_code, "unlikely")
        self.assertTrue(any("neither open yard space" in f.lower() for f in result.key_factors))

    def test_outside_california_requires_further_review(self):
        answers = dict(self.base_eligible_answers)
        answers["located_in_california"] = "no"
        result = calculate_eligibility(answers)
        self.assertEqual(result.status, STATUS_REVIEW)
        self.assertEqual(result.status_code, "review")
        self.assertTrue(any("outside california" in f.lower() for f in result.key_factors))

    def test_site_restrictions_requires_further_review(self):
        answers = dict(self.base_eligible_answers)
        answers["has_restrictions"] = "yes"
        result = calculate_eligibility(answers)
        self.assertEqual(result.status, STATUS_REVIEW)
        self.assertEqual(result.status_code, "review")
        self.assertTrue(any("restrictions" in f.lower() for f in result.key_factors))

    def test_multi_family_requires_further_review(self):
        answers = dict(self.base_eligible_answers)
        answers["is_single_family"] = "no"
        result = calculate_eligibility(answers)
        self.assertEqual(result.status, STATUS_REVIEW)
        self.assertEqual(result.status_code, "review")
        self.assertTrue(any("multi-family" in f.lower() for f in result.key_factors))

    def test_no_yard_space_with_existing_structure_requires_review(self):
        # Feasible conversion candidate
        answers = dict(self.base_eligible_answers)
        answers["has_sufficient_space"] = "no"
        answers["has_existing_structure"] = "yes"
        result = calculate_eligibility(answers)
        self.assertEqual(result.status, STATUS_REVIEW)
        self.assertEqual(result.status_code, "review")
        self.assertTrue(any("garage" in f.lower() or "conversion" in f.lower() for f in result.key_factors))

    def test_normalize_bool_utility(self):
        self.assertTrue(normalize_bool("yes"))
        self.assertTrue(normalize_bool("Yes"))
        self.assertTrue(normalize_bool("true"))
        self.assertTrue(normalize_bool(True))
        self.assertTrue(normalize_bool(1))

        self.assertFalse(normalize_bool("no"))
        self.assertFalse(normalize_bool("false"))
        self.assertFalse(normalize_bool(False))
        self.assertFalse(normalize_bool(0))
        self.assertFalse(normalize_bool(None))


class QuestionnaireFormTestCase(TestCase):
    """
    Tests the 7-question QuestionnaireForm validation.
    """

    def test_valid_form(self):
        form_data = {q["id"]: "yes" for q in QUESTIONS}
        form = QuestionnaireForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_question_fails_validation(self):
        form_data = {q["id"]: "yes" for q in QUESTIONS}
        del form_data["owns_property"]
        form = QuestionnaireForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("owns_property", form.errors)

    def test_invalid_choice_fails_validation(self):
        form_data = {q["id"]: "yes" for q in QUESTIONS}
        form_data["owns_property"] = "maybe"
        form = QuestionnaireForm(data=form_data)
        self.assertFalse(form.is_valid())


class CalculatorViewsTestCase(TestCase):
    """
    Tests public anonymous access, view routing, and session state.
    """

    def setUp(self):
        self.client = Client()

    def test_homepage_renders_cleanly(self):
        response = self.client.get(reverse("calculator:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ADU Advisor")
        self.assertContains(response, "Start 7-Question Check")

    def test_questions_get_renders_form(self):
        response = self.client.get(reverse("calculator:questions"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Property Qualification Check")
        self.assertContains(response, "Do you own the property?")

    def test_questions_post_valid_redirects_to_result(self):
        form_data = {q["id"]: "yes" for q in QUESTIONS}
        response = self.client.post(reverse("calculator:questions"), data=form_data)
        self.assertRedirects(response, reverse("calculator:result"))

        # Verify answers are saved in session
        session = self.client.session
        self.assertIn("adu_answers", session)
        self.assertEqual(session["adu_answers"]["owns_property"], "yes")

    def test_result_view_redirects_if_no_session(self):
        # Accessing result without prior answers should redirect back to questions
        response = self.client.get(reverse("calculator:result"))
        self.assertRedirects(response, reverse("calculator:questions"))

    def test_result_view_displays_calculated_outcome(self):
        session = self.client.session
        session["adu_answers"] = {q["id"]: "yes" for q in QUESTIONS}
        session["adu_answers"]["has_restrictions"] = "no"
        session.save()

        response = self.client.get(reverse("calculator:result"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Potentially Eligible")
        self.assertContains(response, "Proceed to Contact Form")

    def test_restart_view_clears_session(self):
        session = self.client.session
        session["adu_answers"] = {"owns_property": "yes"}
        session["eligibility_result"] = "Potentially Eligible"
        session.save()

        response = self.client.get(reverse("calculator:restart"))
        self.assertRedirects(response, reverse("calculator:index"))
        self.assertNotIn("adu_answers", self.client.session)
