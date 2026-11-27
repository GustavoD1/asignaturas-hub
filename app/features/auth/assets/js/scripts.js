/**
 * Feature-level JavaScript for the authentication module (auto-loaded by splent_framework).
 *
 * Manages the client-side lockout countdown (`#rate-limit-alert` / `#lockout-countdown`)
 * and re-enables `[data-rate-limit-control]` form elements when a rate-limit window expires.
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