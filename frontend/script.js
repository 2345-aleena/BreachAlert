/* ===========================================================
   BreachAlert — interaction layer
   Handles: mobile nav toggle, form validation + status
   feedback, back-to-top visibility.
   No external dependencies.
   =========================================================== */

document.addEventListener('DOMContentLoaded', () => {

  /* -----------------------------------------------------------
     Mobile navigation — user control & freedom: menu can be
     opened and closed explicitly, and closes on link choice
     or Escape so the user is never stuck.
  ----------------------------------------------------------- */
  const navToggle = document.getElementById('nav-toggle');
  const mainNav = document.getElementById('main-nav');

  if (navToggle && mainNav) {
    const closeNav = () => {
      mainNav.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
      navToggle.setAttribute('aria-label', 'Open navigation menu');
    };

    const openNav = () => {
      mainNav.classList.add('is-open');
      navToggle.setAttribute('aria-expanded', 'true');
      navToggle.setAttribute('aria-label', 'Close navigation menu');
    };

    navToggle.addEventListener('click', () => {
      const isOpen = mainNav.classList.contains('is-open');
      isOpen ? closeNav() : openNav();
    });

    mainNav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', closeNav);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && mainNav.classList.contains('is-open')) {
        closeNav();
        navToggle.focus();
      }
    });
  }

  /* -----------------------------------------------------------
     Scan form — error prevention & recovery: validate before
     submit, explain exactly what's wrong, and give ongoing
     system-status feedback via an aria-live region so screen
     reader users get the same information as sighted users.
  ----------------------------------------------------------- */
  const form = document.getElementById('scan-form');
  const emailInput = document.getElementById('email-input');
  const emailError = document.getElementById('email-error');
  const submitBtn = document.getElementById('scan-submit');
  const statusEl = document.getElementById('scan-status');

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function showError(message) {
    emailInput.classList.add('is-invalid');
    emailInput.setAttribute('aria-invalid', 'true');
    emailError.textContent = message;
    emailError.hidden = false;
  }

  function clearError() {
    emailInput.classList.remove('is-invalid');
    emailInput.removeAttribute('aria-invalid');
    emailError.textContent = '';
    emailError.hidden = true;
  }

  if (form) {
    emailInput.addEventListener('input', clearError);

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      clearError();
      statusEl.classList.remove('is-success', 'is-error');

      const value = emailInput.value.trim();

      if (value === '') {
        showError('Enter your email address to run a scan.');
        emailInput.focus();
        return;
      }

      if (!emailPattern.test(value)) {
        showError('That doesn\'t look like a valid email — check for typos.');
        emailInput.focus();
        return;
      }

      // Visible + announced loading state (visibility of system status)
      submitBtn.disabled = true;
      submitBtn.querySelector('.btn__label').textContent = 'Scanning…';
      statusEl.textContent = 'Running your scan — this takes a few seconds.';

      // Simulated scan — replace with a real API call once the
      // backend is live (see README for the integration point).
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn__label').textContent = 'Scan now';
        statusEl.classList.add('is-success');
        statusEl.textContent = `Scan complete for ${value}. In the full version, your results would appear below.`;
        form.reset();
      }, 1400);
    });
  }

  /* -----------------------------------------------------------
     Back-to-top — only appears once there's somewhere to go
     back to, so it never clutters a short viewport.
  ----------------------------------------------------------- */
  const backToTop = document.getElementById('back-to-top');

  if (backToTop) {
    const toggleVisibility = () => {
      if (window.scrollY > 600) {
        backToTop.classList.add('is-visible');
      } else {
        backToTop.classList.remove('is-visible');
      }
    };

    window.addEventListener('scroll', toggleVisibility, { passive: true });
    toggleVisibility();

    backToTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

});
