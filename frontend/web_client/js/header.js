document.addEventListener("DOMContentLoaded", function () {
  // Tentukan halaman aktif berdasarkan nama file URL
  const path = window.location.pathname;
  let activePage = "pos";
  let pageTitle = "MINIMARKET POS";

  if (path.includes("products.html")) {
    activePage = "products";
    pageTitle = "📊 Database Produk (Excel View)";
  } else if (path.includes("users.html")) {
    activePage = "users";
    pageTitle = "👥 Manajemen Karyawan & Kasir";
  } else if (path.includes("reports.html")) {
    activePage = "reports";
    pageTitle = "📈 Laporan Penjualan";
  } else if (path.includes("index.html") || path === "/") {
    activePage = "pos";
    pageTitle = "KASIR MINIMARKET";
  }

  // Buat atau cari container header-bar di bagian atas body
  let headerBar = document.querySelector(".header-bar");
  if (!headerBar) {
    headerBar = document.createElement("div");
    headerBar.className = "header-bar";
    document.body.insertBefore(headerBar, document.body.firstChild);
  }

  // Render struktur HTML header yang konsisten dengan Kelola Produk
  headerBar.innerHTML = `
    <h2>${pageTitle}</h2>
    <div class="nav-tabs">
      <a href="index.html" class="nav-tab-item ${activePage === "pos" ? "active" : ""}">Kasir</a>
      <a href="products.html" class="nav-tab-item ${activePage === "products" ? "active" : ""}">Kelola Produk</a>
      <a href="reports.html" class="nav-tab-item ${activePage === "reports" ? "active" : ""}" id="nav-reports">Laporan</a>
      <a href="users.html" class="nav-tab-item ${activePage === "users" ? "active" : ""}" id="nav-users">Karyawan</a>
    </div>
  `;
});
