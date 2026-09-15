// js/auth.js - Session & Auto-Logout Guard

const INACTIVITY_LIMIT_MS = 15 * 60 * 1000; // Batas inactivity: 15 menit (sesuaikan sesuai kebutuhan)
let inactivityTimer = null;

// 1. Check Session saat Halaman Dibuka
function checkSession() {
  const currentUser = localStorage.getItem("pos_current_user");
  const loginTime = localStorage.getItem("pos_login_time");

  // Jika tidak ada session user, redirect ke halaman login
  if (!currentUser) {
    redirectToLogin();
    return;
  }

  // Check apakah session sudah kadaluarsa (safety check)
  if (loginTime) {
    const elapsed = Date.now() - parseInt(loginTime, 10);
    if (elapsed > INACTIVITY_LIMIT_MS) {
      logoutUser("Sesi Anda telah berakhir karena tidak ada aktivitas.");
      return;
    }
  }

  // Jalankan listener aktivitas jika user sudah login
  initInactivityTracker();
}

// 2. Event Listener Aktivitas User
function initInactivityTracker() {
  resetInactivityTimer();

  // Event yang dianggap sebagai aktivitas user
  const events = ["mousemove", "keydown", "click", "scroll", "touchstart"];
  events.forEach((event) => {
    window.addEventListener(event, resetInactivityTimer, { passive: true });
  });
}

// 3. Reset Timer Aktivitas
function resetInactivityTimer() {
  clearTimeout(inactivityTimer);
  // Update timestamp aktivitas terakhir
  localStorage.setItem("pos_login_time", Date.now().toString());

  inactivityTimer = setTimeout(() => {
    logoutUser("Sistem otomatis Logout karena tidak ada aktivitas selama 15 menit.");
  }, INACTIVITY_LIMIT_MS);
}

// 4. Fungsi Logout
function logoutUser(reasonMessage) {
  clearTimeout(inactivityTimer);
  localStorage.removeItem("pos_current_user");
  localStorage.removeItem("pos_login_time");

  if (reasonMessage) {
    alert(reasonMessage);
  }
  redirectToLogin();
}

// 5. Redirect ke Login
function redirectToLogin() {
  // Cegah redirect berulang jika sudah berada di halaman login.html
  if (!window.location.pathname.endsWith("login.html")) {
    window.location.href = "login.html";
  }
}

// Jalankan pemeriksaan session secara instan (sebelum DOM sepenuhnya dimuat)
checkSession();
