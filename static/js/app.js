// Global JavaScript for Crypto Monitor

// Format large numbers
function formatNumber(num) {
  if (num >= 1e9) return (num / 1e9).toFixed(2) + "B";
  if (num >= 1e6) return (num / 1e6).toFixed(2) + "M";
  if (num >= 1e3) return (num / 1e3).toFixed(2) + "K";
  return num.toFixed(2);
}

// Format percentage
function formatPercent(percent) {
  const sign = percent >= 0 ? "+" : "";
  return sign + percent.toFixed(2) + "%";
}

// Show loading spinner
function showLoading(element) {
  element.innerHTML = '<span class="loading"></span>';
}

// Auto-refresh price data (optional)
function setupAutoRefresh(intervalMinutes = 5) {
  setInterval(() => {
    console.log("Auto-refreshing data...");
    location.reload();
  }, intervalMinutes * 60 * 1000);
}

// Initialize tooltips
document.addEventListener("DOMContentLoaded", function () {
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

// Copy to clipboard function
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert("[OK] Copie dans le presse-papiers !");
  });
}
