/**
 * Client-side lockout countdown and form control manager for auth rate limiting.
 *
 * Reads the remaining lockout seconds (`data-retry-after`) from `#rate-limit-alert`,
 * updates `#lockout-countdown` every second, and re-enables all `[data-rate-limit-control]`
 * inputs and submit buttons once the timer expires.
 *
 * Note: This is a UX convenience only; rate-limit enforcement is validated server-side.
 */

document.addEventListener("DOMContentLoaded", () => {
    const alertBox = document.getElementById("rate-limit-alert");
    const countdownEl = document.getElementById("lockout-countdown");
    if (!alertBox || !countdownEl) return;

    let remaining = parseInt(alertBox.dataset.retryAfter || "0", 10);
    const controls = document.querySelectorAll("[data-rate-limit-control]");

    const formatTime = (totalSeconds) => {
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        return mins > 0
            ? `${mins}m ${String(secs).padStart(2, "0")}s`
            : `${secs}s`;
    };

    countdownEl.textContent = formatTime(remaining);

    const timer = setInterval(() => {
        remaining -= 1;

        if (remaining <= 0) {
            clearInterval(timer);
            controls.forEach((el) => {
                el.disabled = false;
            });
            alertBox.classList.remove("alert-danger");
            alertBox.classList.add("alert-info");
            alertBox.textContent = "Lockout expired. You may try again now.";
            return;
        }

        countdownEl.textContent = formatTime(remaining);
    }, 1000);
});