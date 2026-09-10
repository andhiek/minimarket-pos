// Variable global untuk menyimpan data transaksi terakhir yang di-fetch
let currentReportTransactions = [];

// -------------------------------------------------------------
// GUARD ACCESS: Mencegah Kasir membuka laporan lewat URL langsung
// -------------------------------------------------------------
(function checkAdminAccess() {
  const currentUser = JSON.parse(localStorage.getItem("pos_current_user") || "{}");
  const role = (currentUser.role || "").toLowerCase();
  const isKasir = role === "kasir" || role === "cashier";

  if (!currentUser || !currentUser.role || isKasir) {
    alert("Akses Ditolak! Halaman Laporan Keuangan hanya dapat diakses oleh Admin.");
    window.location.href = "index.html";
  }
})();

document.addEventListener("DOMContentLoaded", () => {
  const reportTypeSelect = document.getElementById("report-type");
  const dailyFilter = document.getElementById("daily-filter");
  const monthlyFilter = document.getElementById("monthly-filter");
  const datePicker = document.getElementById("date-picker");
  const monthPicker = document.getElementById("month-picker");
  const btnLoadReport = document.getElementById("btn-load-report");

  // Inisialisasi tanggal & bulan default
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");

  if (datePicker) datePicker.value = `${yyyy}-${mm}-${dd}`;
  if (monthPicker) monthPicker.value = `${yyyy}-${mm}`;

  // Switch filter Harian / Bulanan
  if (reportTypeSelect) {
    reportTypeSelect.addEventListener("change", () => {
      if (reportTypeSelect.value === "daily") {
        if (dailyFilter) dailyFilter.style.display = "flex";
        if (monthlyFilter) monthlyFilter.style.display = "none";
      } else {
        if (dailyFilter) dailyFilter.style.display = "none";
        if (monthlyFilter) monthlyFilter.style.display = "flex";
      }
    });
  }

  if (btnLoadReport) {
    btnLoadReport.addEventListener("click", loadReportData);
  }

  // Listener tombol Export CSV
  const btnExportCSV = document.getElementById("btn-export-csv");
  if (btnExportCSV) {
    btnExportCSV.addEventListener("click", exportToCSV);
  }

  // Load data otomatis saat pertama kali dibuka
  loadReportData();
});

async function loadReportData() {
  const typeSelect = document.getElementById("report-type");
  const type = typeSelect ? typeSelect.value : "monthly";

  const dateVal = document.getElementById("date-picker")?.value;
  const monthVal = document.getElementById("month-picker")?.value;

  let endpoint = "";
  if (type === "daily") {
    endpoint = `/api/reports/daily?report_date=${dateVal}`;
  } else {
    endpoint = `/api/reports/monthly?report_month=${monthVal}`;
  }

  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`HTTP Error Status: ${response.status}`);
    }

    const data = await response.json();

    // Simpan data transaksi ke variabel global untuk keperluan export
    currentReportTransactions = data.transactions || [];

    // 1. Render Tabel Transaksi
    renderReportTable(currentReportTransactions);

    // 2. Render KPI Cards & Breakdown Pembayaran
    renderKPI(
      data.summary || {
        total_tx: currentReportTransactions.length,
        total_sales: 0,
        total_profit: 0,
        payment_breakdown: {},
      },
    );
  } catch (error) {
    console.error("Gagal mengambil laporan dari API Backend:", error);
    alert("Terjadi kesalahan saat memuat laporan dari server.");
  }
}

function renderKPI(summary) {
  const statTx = document.getElementById("stat-total-tx");
  const statSales = document.getElementById("stat-total-sales");
  const statProfit = document.getElementById("stat-total-profit");

  if (statTx) statTx.innerText = summary.total_tx || 0;
  if (statSales) statSales.innerText = `Rp ${(summary.total_sales || 0).toLocaleString("id-ID")}`;
  if (statProfit) statProfit.innerText = `Rp ${(summary.total_profit || 0).toLocaleString("id-ID")}`;

  // Render breakdown metode pembayaran
  renderPaymentBreakdown(summary.payment_breakdown || {});
}

function renderPaymentBreakdown(breakdown) {
  const container = document.getElementById("payment-breakdown-container");
  if (!container) return;

  const defaultMethods = ["CASH", "QRIS", "DEBIT", "TRANSFER"];
  const colors = {
    CASH: "#10b981", // Hijau
    QRIS: "#3b82f6", // Biru
    DEBIT: "#f59e0b", // Oranye/Kuning
    TRANSFER: "#8b5cf6", // Ungu
  };

  const allMethods = {};
  defaultMethods.forEach((method) => {
    allMethods[method] = breakdown[method] || 0;
  });

  Object.keys(breakdown).forEach((method) => {
    if (!allMethods.hasOwnProperty(method)) {
      allMethods[method] = breakdown[method];
    }
  });

  // Inline style flex-direction row
  container.setAttribute("style", "display: flex !important; flex-direction: row !important; gap: 12px; margin-bottom: 20px; width: 100%;");

  container.innerHTML = Object.entries(allMethods)
    .map(([method, total]) => {
      const borderColor = colors[method] || "#6b7280";
      return `
        <div style="background: var(--bg-panel, #1f2937); border: 1px solid var(--border-color, #374151); border-left: 4px solid ${borderColor}; padding: 10px 14px; border-radius: 6px; flex: 1; min-width: 0;">
          <small style="color: var(--text-muted, #9ca3af); text-transform: uppercase; font-size: 11px; font-weight: bold; display: block;">METODE: ${method}</small>
          <div style="font-size: 15px; font-weight: bold; color: var(--text-main, #fff); margin-top: 3px; white-space: nowrap;">
            Rp ${(total || 0).toLocaleString("id-ID")}
          </div>
        </div>
      `;
    })
    .join("");
}

function renderReportTable(list) {
  const tbody = document.getElementById("report-table-body");
  if (!tbody) return;

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="padding: 30px; color: #888;">Tidak ada data transaksi.</td></tr>`;
    return;
  }

  tbody.innerHTML = list
    .map((item, index) => {
      const invoice = item.invoice_no || `INV-${item.id}`;
      const cashier = item.cashier || "Administrator";
      const total = item.grand_total || 0;
      const dateDisplay = item.date || "-";
      const timeDisplay = item.time || "-";

      return `
            <tr>
                <td class="text-center">${index + 1}</td>
                <td><strong>${invoice}</strong></td>
                <td class="text-center">${dateDisplay}</td>
                <td class="text-center">${timeDisplay}</td>
                <td>${cashier}</td>
                <td class="text-center"><span class="badge-payment">${item.payment_method || "CASH"}</span></td>
                <td class="text-right"><strong>Rp ${total.toLocaleString("id-ID")}</strong></td>
                <td class="text-center">
                    <button class="btn-detail" onclick="openDetailModal(${item.id})">Detail</button>
                </td>
            </tr>
        `;
    })
    .join("");
}

// Buka Modal & Ambil Detail Transaksi
async function openDetailModal(txId) {
  try {
    const response = await fetch(`/api/reports/transaction/${txId}`);
    if (!response.ok) throw new Error("Gagal mengambil detail transaksi");

    const data = await response.json();

    document.getElementById("modal-invoice-no").innerText = data.invoice_no;
    document.getElementById("modal-date-time").innerText = data.date_time;
    document.getElementById("modal-cashier").innerText = data.cashier;
    document.getElementById("modal-payment-method").innerText = data.payment_method;
    document.getElementById("modal-grand-total").innerText = `Rp ${data.grand_total.toLocaleString("id-ID")}`;

    const itemsBody = document.getElementById("modal-items-body");
    itemsBody.innerHTML = data.items
      .map(
        (it) => `
            <tr>
                <td>${it.product_name}</td>
                <td class="text-center">${it.quantity}</td>
                <td class="text-right">Rp ${it.price.toLocaleString("id-ID")}</td>
                <td class="text-right">Rp ${it.subtotal.toLocaleString("id-ID")}</td>
            </tr>
        `,
      )
      .join("");

    document.getElementById("modal-detail").style.display = "flex";
  } catch (err) {
    console.error(err);
    alert("Gagal memuat detail nota.");
  }
}

function closeDetailModal() {
  document.getElementById("modal-detail").style.display = "none";
}

// Export Data Laporan ke File CSV
function exportToCSV() {
  if (!currentReportTransactions || currentReportTransactions.length === 0) {
    alert("Tidak ada data transaksi untuk diexport.");
    return;
  }

  const headers = ["No", "No Invoice", "Tanggal", "Jam", "Kasir", "Metode Pembayaran", "Total Transaksi"];

  const rows = currentReportTransactions.map((item, index) => {
    const invoice = `"${item.invoice_no || `INV-${item.id}`}"`;
    const date = `"${item.date || "-"}"`;
    const time = `"${item.time || "-"}"`;
    const cashier = `"${item.cashier || "Administrator"}"`;
    const payment = `"${item.payment_method || "CASH"}"`;
    const total = item.grand_total || 0;

    return [index + 1, invoice, date, time, cashier, payment, total];
  });

  let csvContent = "\uFEFF"; // Byte Order Mark (BOM) UTF-8
  csvContent += headers.join(",") + "\n";

  rows.forEach((row) => {
    csvContent += row.join(",") + "\n";
  });

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const typeSelect = document.getElementById("report-type");
  const reportType = typeSelect ? typeSelect.value : "report";
  const dateVal = document.getElementById("date-picker")?.value;
  const monthVal = document.getElementById("month-picker")?.value;
  const period = reportType === "daily" ? dateVal : monthVal;

  const fileName = `Laporan_Penjualan_${period}.csv`;

  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", fileName);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
