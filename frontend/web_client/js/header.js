document.addEventListener("DOMContentLoaded", function () {
  // Ambil data user yang sedang login dari localStorage (jika ada)
  const currentUser = JSON.parse(localStorage.getItem("currentUser")) || {
    full_name: "Administrator",
    role: "ADMIN",
  };

  // Cari atau buat container header universal di halaman
  let headerContainer = document.querySelector(".app-header");
  if (!headerContainer) {
    headerContainer = document.createElement("header");
    headerContainer.className = "app-header";
    document.body.insertBefore(headerContainer, document.body.firstChild);
  }

  // Tentukan Judul Berdasarkan Nama File HTML yang Aktif
  const path = window.location.pathname;
  let pageTitle = "MINIMARKET POS";
  if (path.includes("users.html")) {
    pageTitle = "MANAJEMEN KARYAWAN";
  } else if (path.includes("index.html") || path === "/") {
    pageTitle = "KASIR MINIMARKET";
  }

  // HTML Template Header yang Serupa dengan Halaman Utama
  headerContainer.innerHTML = `
    <div class="header-left">
      <h2 class="header-logo">🌙 ${pageTitle}</h2>
    </div>
    <div class="header-right">
      <div class="user-profile-badge">
        <div class="user-avatar">${currentUser.full_name ? currentUser.full_name.charAt(0).toUpperCase() : "A"}</div>
        <div class="user-info">
          <span class="user-name">${currentUser.full_name}</span>
          <span class="user-role">${currentUser.role}</span>
        </div>
      </div>
      <button class="btn-logout" onclick="handleLogout()" title="Keluar Akun">🚪 Logout</button>
    </div>
  `;
});

function handleLogout() {
  if (confirm("Apakah Anda yakin ingin keluar dari aplikasi?")) {
    localStorage.removeItem("currentUser");
    window.location.href = "login.html"; // Sesuaikan halaman login Anda
  }
}
