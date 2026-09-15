// js/pos-helpers.js - Toast Notifications & Keyboard Shortcuts

// ==========================================
// 1. TOAST NOTIFICATION SYSTEM
// ==========================================
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");

  // Buat container jika belum ada di DOM
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  // Pilih ikon berdasarkan tipe toast
  let icon = "fa-circle-info";
  if (type === "success") icon = "fa-circle-check";
  if (type === "error") icon = "fa-circle-xmark";
  if (type === "warning") icon = "fa-triangle-exclamation";

  toast.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px;">
      <i class="fa-solid ${icon}"></i>
      <span>${message}</span>
    </div>
  `;

  container.appendChild(toast);

  // Otomatis hapus elemen dari DOM setelah 3 detik
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

// Override alert bawaan browser agar otomatis menggunakan Toast Error
window.alert = function (msg) {
  showToast(msg, "warning");
};

// ==========================================
// 2. POS KEYBOARD SHORTCUTS
// ==========================================
document.addEventListener("keydown", function (e) {
  // Hanya jalankan shortcut jika fokus TIDAK berada di dalam input teks biasa saat menekan tombol fungsi
  const activeEl = document.activeElement;
  const isInputFocused = activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "SELECT");

  // [F2] - Fokus ke Input Scan Barcode
  if (e.key === "F2") {
    e.preventDefault();
    const barcodeInput = document.getElementById("barcode-input") || document.querySelector('input[placeholder*="barcode"i]');
    if (barcodeInput) {
      barcodeInput.focus();
      barcodeInput.select();
      showToast("Fokus: Scan Barcode (F2)", "info");
    }
  }

  // [F4] - Fokus ke Input Uang Dibayar
  if (e.key === "F4") {
    e.preventDefault();
    const payInput = document.getElementById("pay-amount") || document.querySelector('input[placeholder*="bayar"i]');
    if (payInput) {
      payInput.focus();
      payInput.select();
      showToast("Fokus: Uang Dibayar (F4)", "info");
    }
  }

  // [Escape] - Kosongkan Form / Batalkan Transaksi
  if (e.key === "Escape") {
    const cancelBtn = document.getElementById("btn-cancel-trans") || document.querySelector(".btn-danger");
    if (cancelBtn) {
      cancelBtn.click();
      showToast("Transaksi dibatalkan (Esc)", "warning");
    } else {
      if (activeEl) activeEl.blur();
    }
  }

  // [Enter] - Eksekusi Bayar jika sedang fokus di Input Uang Dibayar
  if (e.key === "Enter" && activeEl && (activeEl.id === "pay-amount" || activeEl.getAttribute("placeholder")?.includes("bayar"))) {
    e.preventDefault();
    const processBtn = document.getElementById("btn-process-pay") || document.querySelector(".btn-success");
    if (processBtn) {
      processBtn.click();
    }
  }
});
