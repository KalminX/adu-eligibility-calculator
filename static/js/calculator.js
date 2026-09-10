/**
 * ADU Eligibility Calculator - Stepped Questionnaire UI
 * Progressive enhancement for single-question navigation and live progress tracking.
 */

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("questionnaire-form");
  if (!form) return;

  const cards = Array.from(document.querySelectorAll(".question-step-card"));
  if (cards.length === 0) return;

  let currentStep = 0;
  const totalSteps = cards.length;

  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-step-text");
  const prevBtn = document.getElementById("btn-prev-step");
  const nextBtn = document.getElementById("btn-next-step");
  const submitBtn = document.getElementById("btn-submit-all");

  function updateStepView() {
    cards.forEach((card, idx) => {
      if (idx === currentStep) {
        card.classList.remove("hidden");
      } else {
        card.classList.add("hidden");
      }
    });

    const percent = Math.round(((currentStep + 1) / totalSteps) * 100);
    if (progressBar) {
      progressBar.style.width = `${percent}%`;
    }
    if (progressText) {
      progressText.textContent = `Question ${currentStep + 1} of ${totalSteps}`;
    }

    if (prevBtn) {
      if (currentStep === 0) {
        prevBtn.classList.add("invisible");
      } else {
        prevBtn.classList.remove("invisible");
      }
    }

    if (nextBtn && submitBtn) {
      if (currentStep === totalSteps - 1) {
        nextBtn.classList.add("hidden");
        submitBtn.classList.remove("hidden");
      } else {
        nextBtn.classList.remove("hidden");
        submitBtn.classList.add("hidden");
      }
    }
  }

  // Radio button click listener to auto-highlight and enable easy progression
  cards.forEach((card, stepIndex) => {
    const radios = card.querySelectorAll("input[type='radio']");
    radios.forEach((radio) => {
      radio.addEventListener("change", function () {
        // Highlight chosen option
        card.querySelectorAll(".option-label").forEach((lbl) => {
          lbl.classList.remove("border-blue-600", "bg-blue-50", "ring-2", "ring-blue-500");
          lbl.classList.add("border-slate-200", "bg-white");
        });
        const chosenLabel = radio.closest("label");
        if (chosenLabel) {
          chosenLabel.classList.remove("border-slate-200", "bg-white");
          chosenLabel.classList.add("border-blue-600", "bg-blue-50", "ring-2", "ring-blue-500");
        }

        // Auto-advance to next question if not at final step
        if (stepIndex < totalSteps - 1) {
          setTimeout(() => {
            currentStep = stepIndex + 1;
            updateStepView();
          }, 220);
        }
      });
    });
  });

  if (prevBtn) {
    prevBtn.addEventListener("click", function (e) {
      e.preventDefault();
      if (currentStep > 0) {
        currentStep--;
        updateStepView();
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", function (e) {
      e.preventDefault();
      // Verify current question is answered
      const activeCard = cards[currentStep];
      const answered = activeCard.querySelector("input[type='radio']:checked");
      if (!answered) {
        const errorAlert = document.getElementById("step-validation-error");
        if (errorAlert) {
          errorAlert.classList.remove("hidden");
          setTimeout(() => errorAlert.classList.add("hidden"), 3000);
        }
        return;
      }
      if (currentStep < totalSteps - 1) {
        currentStep++;
        updateStepView();
      }
    });
  }

  // Initialize view
  updateStepView();
});
