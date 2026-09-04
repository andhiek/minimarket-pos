/**
 * APP.JS - MINIMARKET POS SYSTEM
 * Aplikasi Kasir Frontend yang terhubung dengan FastAPI / SQLModel Backend
 */

// Konfigurasi Endpoint Backend
const API_BASE_URL = "http://localhost:8000/api";

// -----------------------------------------------------------------------------
// STATE MANAGEMENT (Penyimpanan Status Sementara Aplikasi)
// -----------------------------------------------------------------------------
let cart = []; // Menampung daftar item belanjaan yang dimasukkan kasir
let selectedCartIndex = -1; // Menandai baris tabel keranjang yang sedang dipilih/diklik
let pendingTransactions = []; // Menampung transaksi yang ditahan (Hold/Pending)
let lastCompletedTransaction = null; // Menimpan data transaksi terakhir untuk fitur cetak ulang struk

// User Auth State
let currentUser = JSON.parse(localStorage.getItem("pos_current_user")) || null;
const currentCashier = { id: 1, name: "Administrator" };

// -----------------------------------------------------------------------------
// DOM ELEMENTS (Pengambilan Elemen HTML Utama)
// -----------------------------------------------------------------------------
const barcodeInput = document.getElementById("barcode-input");
const btnAdd = document.getElementById("btn-add");
const customerPhoneInput = document.getElementById("customer-phone");
const btnSearchMember = document.getElementById("btn-search-member");
const memberNameDisplay = document.getElementById("member-name-display");
const cartTableBody = document.getElementById("cart-table-body");
const grandTotalDisplay = document.getElementById("grand-total-display");
const discountInput = document.getElementById("discount-input");
const paidAmountInput = document.getElementById("paid-amount");
const changeDisplay = document.getElementById("change-display");
const btnPayMain = document.getElementById("btn-pay-main");
const btnDeleteItem = document.getElementById("btn-delete-item");
const themeToggleBtn = document.getElementById("theme-toggle");
const btnHold = document.getElementById("btn-hold");
const btnPending = document.getElementById("btn-pending");
const btnReprint = document.getElementById("btn-reprint");

// -----------------------------------------------------------------------------
// HELPER FUNCTIONS
// -----------------------------------------------------------------------------
/**
 * Memformat angka menjadi format mata uang Rupiah Indonesia (contoh: Rp 15.000)
 * @param {number} num - Angka nominal
 * @returns {string} String terformat Rupiah
 */
function formatRupiah(num) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(num || 0);
}

// -----------------------------------------------------------------------------
// 0. AUTHENTICATION & USER MANAGEMENT
// -----------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  checkAuthStatus();
});

/**
 * Memeriksa status login kasir dari localStorage. Jika tidak ada, alihkan ke login.html
 */
function checkAuthStatus() {
  if (!currentUser) {
    window.location.href = "login.html";
    return;
  }
  updateUserDisplay();
}

/**
 * Memperbarui tampilan nama dan role kasir di navbar/header aplikasi
 */
function updateUserDisplay() {
  const nameDisplay = document.getElementById("current-user-name");
  const roleDisplay = document.getElementById("current-user-role");

  if (currentUser) {
    if (nameDisplay) nameDisplay.innerText = currentUser.full_name || currentUser.username;
    if (roleDisplay) roleDisplay.innerText = (currentUser.role || "cashier").toUpperCase();

    // Sync data kasir aktif untuk payload checkout
    currentCashier.id = currentUser.id;
    currentCashier.name = currentUser.full_name || currentUser.username;
  }
}

// Event Listener tombol ganti akun / Logout
const btnSwitchUser = document.getElementById("btn-switch-user");
if (btnSwitchUser) {
  btnSwitchUser.addEventListener("click", () => {
    if (confirm("Apakah Anda yakin ingin mengganti akun kasir / logout?")) {
      currentUser = null;
      localStorage.removeItem("pos_current_user");
      window.location.href = "login.html";
    }
  });
}

// -----------------------------------------------------------------------------
// 1. THEME MANAGEMENT (Mode Gelap / Terang)
// -----------------------------------------------------------------------------
if (themeToggleBtn) {
  themeToggleBtn.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    if (currentTheme === "dark") {
      document.documentElement.setAttribute("data-theme", "light");
      themeToggleBtn.innerText = "☀️";
    } else {
      document.documentElement.setAttribute("data-theme", "dark");
      themeToggleBtn.innerText = "🌙";
    }
  });
}

// -----------------------------------------------------------------------------
// 2. MODAL MANAGEMENT (Manajer Jendela Pop-up)
// -----------------------------------------------------------------------------
/**
 * Membuka jendela modal berdasarkan ID elemen
 * @param {string} modalId - ID elemen modal HTML
 */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
    if (modalId === "modal-products") loadProductList();
    if (modalId === "modal-reports") loadReports();
    if (modalId === "modal-receipt-settings") loadReceiptSettingsToForm();
  }
}

/**
 * Menutup jendela modal berdasarkan ID elemen dan kembalikan fokus ke kolom input barcode
 * @param {string} modalId - ID elemen modal HTML
 */
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("active");
    if (barcodeInput) barcodeInput.focus();
  }
}

// Menghubungkan Tombol Top Navbar dengan Modal masing-masing
if (document.getElementById("btn-modal-products")) document.getElementById("btn-modal-products").onclick = () => openModal("modal-products");
if (document.getElementById("btn-modal-members")) document.getElementById("btn-modal-members").onclick = () => openModal("modal-members");
if (document.getElementById("btn-modal-reports")) document.getElementById("btn-modal-reports").onclick = () => openModal("modal-reports");
if (document.getElementById("btn-modal-receipt-settings")) document.getElementById("btn-modal-receipt-settings").onclick = () => openModal("modal-receipt-settings");

// -----------------------------------------------------------------------------
// 3. SCAN & CART OPERATIONS (Pencarian Produk & Operasi Keranjang)
// -----------------------------------------------------------------------------
/**
 * Fungsi utama untuk mencari produk berdasarkan barcode atau kata kunci nama produk
 */
async function handleAddProduct() {
  const query = barcodeInput.value.trim();
  if (!query) return;

  try {
    const res = await fetch(`${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`);

    if (res.ok) {
      const products = await res.json();

      if (products.length === 1) {
        // Jika hasil tepat 1 produk (biasanya scan barcode)
        addToCart(products[0]);
        barcodeInput.value = "";
        barcodeInput.focus();
      } else if (products.length > 1) {
        // Jika ditemukan beberapa produk dengan nama mirip (misal ketik "air")
        showProductSearchResults(products);
      } else {
        alert("Produk tidak ditemukan!");
      }
    } else {
      alert("Gagal mencari produk!");
    }
  } catch (err) {
    alert("Gagal terhubung ke server backend!");
  }
}

// Event Listener Enter pada kolom Barcode dan Tombol Tambah
if (barcodeInput) {
  barcodeInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleAddProduct();
  });
}
if (btnAdd) btnAdd.addEventListener("click", handleAddProduct);

/**
 * Menampilkan daftar pilihan produk ketika hasil pencarian lebih dari 1 item
 * @param {Array} products - Daftar array objek produk dari backend
 */
function showProductSearchResults(products) {
  let optionsText = "Beberapa produk ditemukan, pilih nomor produk:\n\n";
  products.forEach((p, index) => {
    const price = p.price ?? p.selling_price ?? 0;
    optionsText += `${index + 1}. [${p.barcode}] ${p.name} - ${formatRupiah(price)} (Stok: ${p.stock})\n`;
  });

  const choice = prompt(optionsText + "\nMasukkan nomor pilihan (1 - " + products.length + "):");
  const selectedIndex = parseInt(choice) - 1;

  if (!isNaN(selectedIndex) && selectedIndex >= 0 && selectedIndex < products.length) {
    addToCart(products[selectedIndex]);
    barcodeInput.value = "";
    barcodeInput.focus();
  } else if (choice !== null) {
    alert("Pilihan tidak valid!");
  }
}

// Pencarian Member berdasarkan Nomor Telepon
if (btnSearchMember) {
  btnSearchMember.addEventListener("click", async () => {
    const phone = customerPhoneInput.value.trim();
    if (!phone) return;

    try {
      const res = await fetch(`${API_BASE_URL}/customers/phone/${phone}`);
      if (res.ok) {
        const customer = await res.json();
        memberNameDisplay.innerText = `${customer.name} (${customer.points || 0} Pts)`;
      } else {
        alert("Member tidak ditemukan!");
        memberNameDisplay.innerText = "Non-Member";
      }
    } catch (err) {
      alert("Gagal mencari member!");
    }
  });
}

/**
 * Menambahkan objek produk ke dalam array `cart`.
 * Jika item sudah ada di keranjang, jumlah kuantitas akan ditambah 1.
 * @param {Object} product - Data objek produk dari database
 */
function addToCart(product) {
  if (product.stock <= 0) {
    alert(`Stok '${product.name}' habis!`);
    return;
  }

  // Menggunakan atribut price (dengan fallback ke selling_price untuk kompatibilitas)
  const itemPrice = parseFloat(product.price ?? product.selling_price ?? 0);

  const existing = cart.find((item) => item.product_id === product.id);
  if (existing) {
    if (existing.quantity + 1 > product.stock) {
      alert(`Stok tidak mencukupi (Sisa stok: ${product.stock})`);
      return;
    }
    existing.quantity += 1;
  } else {
    cart.push({
      product_id: product.id,
      barcode: product.barcode,
      name: product.name,
      price: itemPrice,
      quantity: 1,
      max_stock: product.stock,
    });
  }
  renderCart();
}

/**
 * Merender ulang elemen HTML tabel keranjang belanja berdasarkan data dalam array `cart`
 */
function renderCart() {
  cartTableBody.innerHTML = "";
  let subtotal = 0;

  cart.forEach((item, idx) => {
    const itemSubtotal = item.price * item.quantity;
    subtotal += itemSubtotal;

    const tr = document.createElement("tr");
    if (idx === selectedCartIndex) tr.style.background = "rgba(59, 130, 246, 0.2)";

    // Pilih baris pada tabel saat diklik
    tr.onclick = () => {
      selectedCartIndex = idx;
      renderCart();
    };

    tr.innerHTML = `
      <td>${item.barcode}</td>
      <td><b>${item.name}</b></td>
      <td style="text-align: right;">${formatRupiah(item.price)}</td>
      <td style="text-align: center;">${item.quantity}</td>
      <td style="text-align: right;"><b>${formatRupiah(itemSubtotal)}</b></td>
    `;
    cartTableBody.appendChild(tr);
  });

  const discount = parseFloat(discountInput.value) || 0;
  const grandTotal = Math.max(0, subtotal - discount);

  grandTotalDisplay.innerText = formatRupiah(grandTotal);
  calculateChange();
}

// Event Listener hitung kembalian dan diskon secara instan
if (paidAmountInput) paidAmountInput.addEventListener("input", calculateChange);
if (discountInput) discountInput.addEventListener("input", renderCart);

/**
 * Menghitung selisih/kembalian dari jumlah bayar dikurangi total belanja
 */
function calculateChange() {
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const discount = parseFloat(discountInput.value) || 0;
  const grandTotal = Math.max(0, subtotal - discount);
  const paid = parseFloat(paidAmountInput.value) || 0;

  const change = paid - grandTotal;

  if (change >= 0) {
    changeDisplay.innerText = formatRupiah(change);
    changeDisplay.style.color = "var(--text-main)";
  } else {
    changeDisplay.innerText = "Uang Kurang";
    changeDisplay.style.color = "var(--accent-red)";
  }
}

// Hapus item dari keranjang yang dipilih
if (btnDeleteItem) {
  btnDeleteItem.addEventListener("click", () => {
    if (selectedCartIndex >= 0 && selectedCartIndex < cart.length) {
      cart.splice(selectedCartIndex, 1);
      selectedCartIndex = -1;
      renderCart();
    } else {
      alert("Pilih barang yang ingin dihapus terlebih dahulu!");
    }
  });
}

// -----------------------------------------------------------------------------
// 4. PENDING / HOLD TRANSACTIONS (Fungsi Menahan & Memulihkan Transaksi)
// -----------------------------------------------------------------------------
// Menahan transaksi saat ini
if (btnHold) {
  btnHold.addEventListener("click", () => {
    if (cart.length === 0) {
      alert("Keranjang kosong, tidak ada transaksi untuk ditahan!");
      return;
    }

    const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const discount = parseFloat(discountInput.value) || 0;

    const heldTransaction = {
      id: Date.now(),
      time: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
      customerPhone: customerPhoneInput.value.trim() || "Non-Member",
      memberName: memberNameDisplay.innerText,
      cart: [...cart],
      discount: discount,
      total: Math.max(0, subtotal - discount),
    };

    pendingTransactions.push(heldTransaction);

    resetPOSForm();
    updatePendingButtonLabel();
    alert("Transaksi berhasil ditahan (Hold)!");
  });
}

/**
 * Memperbarui teks jumlah antrean transaksi pending pada tombol
 */
function updatePendingButtonLabel() {
  if (btnPending) btnPending.innerText = `Buka Pending (${pendingTransactions.length})`;
}

// Membuka modal daftar transaksi pending
if (btnPending) {
  btnPending.addEventListener("click", () => {
    renderPendingList();
    openModal("modal-pending");
  });
}

/**
 * Merender daftar antrean transaksi yang sedang ditahan ke dalam modal
 */
function renderPendingList() {
  const tbody = document.getElementById("pending-list-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (pendingTransactions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Tidak ada transaksi yang ditahan</td></tr>`;
    return;
  }

  pendingTransactions.forEach((tx, index) => {
    const totalQty = tx.cart.reduce((sum, item) => sum + item.quantity, 0);
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${tx.time}</td>
      <td><b>${tx.memberName}</b></td>
      <td style="text-align: center;">${totalQty} item</td>
      <td style="text-align: right;"><b>${formatRupiah(tx.total)}</b></td>
      <td style="text-align: center;">
        <button class="btn-action" style="padding: 4px 10px; font-size: 11px;" onclick="resumeTransaction(${index})">Pulihkan</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * Mengembalikan data transaksi dari pending ke keranjang belanja utama
 * @param {number} index - Indeks posisi array transaksi pending
 */
function resumeTransaction(index) {
  if (cart.length > 0) {
    if (!confirm("Keranjang saat ini masih terisi. Ingin menimpa keranjang dengan transaksi pending ini?")) {
      return;
    }
  }

  const tx = pendingTransactions[index];
  cart = [...tx.cart];
  discountInput.value = tx.discount;
  customerPhoneInput.value = tx.customerPhone !== "Non-Member" ? tx.customerPhone : "";
  memberNameDisplay.innerText = tx.memberName;

  pendingTransactions.splice(index, 1);
  updatePendingButtonLabel();
  closeModal("modal-pending");
  renderCart();
}

// -----------------------------------------------------------------------------
// 5. CHECKOUT PROCESS (Proses Pembayaran & Transaksi Selesai)
// -----------------------------------------------------------------------------
if (btnPayMain) {
  btnPayMain.onclick = async () => {
    if (!currentUser) {
      alert("Silakan login terlebih dahulu!");
      window.location.href = "login.html";
      return;
    }

    if (cart.length === 0) {
      alert("Keranjang belanja kosong!");
      return;
    }

    const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const discount = parseFloat(discountInput.value) || 0;
    const grandTotal = Math.max(0, subtotal - discount);
    const paidAmount = parseFloat(paidAmountInput.value) || 0;
    const paymentMethod = document.getElementById("payment-method").value;

    if (paidAmount < grandTotal) {
      alert("Uang Pembayaran Masih Kurang!");
      return;
    }

    // Payload request untuk API endpoint /pos/checkout
    const payload = {
      cashier_id: currentCashier.id,
      cashier_name: currentCashier.name,
      customer_phone: customerPhoneInput.value.trim() || null,
      cart_items: cart.map((item) => ({ product_id: item.product_id, quantity: item.quantity })),
      paid_amount: paidAmount,
      discount_amount: discount,
      payment_method: paymentMethod,
    };

    try {
      const res = await fetch(`${API_BASE_URL}/pos/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (res.ok) {
        lastCompletedTransaction = {
          invoiceNumber: data.invoice_number,
          items: [...cart],
          subtotal: subtotal,
          discount: discount,
          grandTotal: grandTotal,
          paidAmount: paidAmount,
          changeAmount: data.change_amount,
          paymentMethod: paymentMethod,
          memberName: memberNameDisplay.innerText,
          cashierName: currentCashier.name,
        };

        resetPOSForm();
        showReceiptModal(lastCompletedTransaction);
      } else {
        alert(`Gagal: ${data.detail}`);
      }
    } catch (err) {
      alert("Terjadi kesalahan koneksi saat checkout!");
    }
  };
}

/**
 * Mengosongkan formulir POS setelah transaksi berhasil diselesaikan
 */
function resetPOSForm() {
  cart = [];
  selectedCartIndex = -1;
  paidAmountInput.value = "";
  discountInput.value = "0";
  customerPhoneInput.value = "";
  memberNameDisplay.innerText = "Non-Member";
  renderCart();
  if (barcodeInput) barcodeInput.focus();
}

// -----------------------------------------------------------------------------
// 6. STRUK & LOCALSTORAGE SETTINGS (Pengaturan Struk & Fungsi Cetak)
// -----------------------------------------------------------------------------
/**
 * Menyimpan nama toko, alamat, dan pesan footer struk ke browser localStorage
 */
function saveReceiptSettings() {
  const settings = {
    storeName: document.getElementById("s-store-name").value.trim() || "MINIMARKET POS",
    storeAddress: document.getElementById("s-store-address").value.trim() || "Jl. Raya Minimarket No. 123",
    footerMsg: document.getElementById("s-footer-msg").value.trim() || "Terima Kasih Telah Berbelanja!",
  };
  localStorage.setItem("pos_receipt_settings", JSON.stringify(settings));
}

/**
 * Mengambil pengaturan profil toko dari localStorage (dengan fallback nilai default)
 * @returns {Object} Objek pengaturan profil toko
 */
function getReceiptSettings() {
  const saved = localStorage.getItem("pos_receipt_settings");
  if (saved) return JSON.parse(saved);
  return {
    storeName: "MINIMARKET POS",
    storeAddress: "Jl. Raya Minimarket No. 123",
    footerMsg: "Terima Kasih Telah Berbelanja!",
  };
}

/**
 * Memuat profil toko dari localStorage ke form edit pengaturan
 */
function loadReceiptSettingsToForm() {
  const settings = getReceiptSettings();
  if (document.getElementById("s-store-name")) document.getElementById("s-store-name").value = settings.storeName;
  if (document.getElementById("s-store-address")) document.getElementById("s-store-address").value = settings.storeAddress;
  if (document.getElementById("s-footer-msg")) document.getElementById("s-footer-msg").value = settings.footerMsg;
}

if (document.getElementById("btn-save-settings")) {
  document.getElementById("btn-save-settings").onclick = () => {
    saveReceiptSettings();
    alert("Pengaturan Struk Berhasil Disimpan!");
    closeModal("modal-receipt-settings");
  };
}

/**
 * Menampilkan struk belanja digital di modal pop-up siap cetak
 * @param {Object} txData - Data detail transaksi yang selesai
 */
function showReceiptModal(txData) {
  const settings = getReceiptSettings();

  document.getElementById("r-store-name").innerText = settings.storeName;
  document.getElementById("r-store-address").innerText = settings.storeAddress;
  document.getElementById("r-footer-msg").innerText = settings.footerMsg;

  document.getElementById("r-invoice").innerText = txData.invoiceNumber;
  document.getElementById("r-date").innerText = new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
  document.getElementById("r-cashier").innerText = txData.cashierName || currentCashier.name;
  document.getElementById("r-member").innerText = txData.memberName || "Non-Member";

  const itemsContainer = document.getElementById("r-items-list");
  itemsContainer.innerHTML = "";
  txData.items.forEach((item) => {
    const itemSubtotal = item.price * item.quantity;
    const row = document.createElement("div");
    row.style.margin = "2px 0";
    row.innerHTML = `
      <div>${item.name}</div>
      <div style="display: flex; justify-content: space-between; font-size: 11px;">
        <span>${item.quantity} x ${formatRupiah(item.price)}</span>
        <span>${formatRupiah(itemSubtotal)}</span>
      </div>
    `;
    itemsContainer.appendChild(row);
  });

  document.getElementById("r-subtotal").innerText = formatRupiah(txData.subtotal);
  document.getElementById("r-discount").innerText = formatRupiah(txData.discount);
  document.getElementById("r-grand-total").innerText = formatRupiah(txData.grandTotal);
  document.getElementById("r-method").innerText = txData.paymentMethod;
  document.getElementById("r-paid").innerText = formatRupiah(txData.paidAmount);
  document.getElementById("r-change").innerText = formatRupiah(txData.changeAmount);

  openModal("modal-receipt");
}

/**
 * Mencetak struk belanja menggunakan fitur browser print
 */
function printReceipt() {
  const printContents = document.getElementById("receipt-print-area").innerHTML;
  const originalContents = document.body.innerHTML;

  document.body.innerHTML = `<div style="width: 300px; margin: 0 auto; font-family: 'Courier New', monospace;">${printContents}</div>`;
  window.print();
  document.body.innerHTML = originalContents;
  window.location.reload();
}

// Tombol Cetak Ulang Struk Terakhir
if (btnReprint) {
  btnReprint.onclick = () => {
    if (!lastCompletedTransaction) {
      alert("Belum ada transaksi yang dapat dicetak ulang!");
      return;
    }
    showReceiptModal(lastCompletedTransaction);
  };
}

// -----------------------------------------------------------------------------
// 7. ADMIN MODALS API LOGIC (Fungsi Kelola Produk, Member, & Laporan)
// -----------------------------------------------------------------------------
// Tambah / Simpan Produk Baru dari Modal
if (document.getElementById("btn-save-product")) {
  document.getElementById("btn-save-product").onclick = async () => {
    const barcode = document.getElementById("p-barcode").value.trim();
    const name = document.getElementById("p-name").value.trim();
    const price = parseFloat(document.getElementById("p-price").value) || 0;
    const purchase_price = parseFloat(document.getElementById("p-cost").value) || 0;
    const stock = parseInt(document.getElementById("p-stock").value) || 0;

    if (!barcode || !name || price <= 0) {
      alert("Isi barcode, nama, dan harga dengan benar!");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/products`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          barcode: barcode,
          name: name,
          price: price,
          purchase_price: purchase_price,
          stock: stock,
        }),
      });

      if (res.ok) {
        alert("Produk berhasil disimpan!");
        document.getElementById("p-barcode").value = "";
        document.getElementById("p-name").value = "";
        document.getElementById("p-price").value = "";
        document.getElementById("p-cost").value = "";
        document.getElementById("p-stock").value = "";
        loadProductList();
      } else {
        const errData = await res.json();
        alert(`Gagal menyimpan produk: ${errData.detail || "Terjadi kesalahan"}`);
      }
    } catch (err) {
      alert("Koneksi gagal!");
    }
  };
}

/**
 * Memuat seluruh daftar produk dari API backend dan menampilkan ke tabel modal produk
 */
async function loadProductList() {
  const tbody = document.getElementById("product-list-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  try {
    const res = await fetch(`${API_BASE_URL}/products`);
    if (res.ok) {
      const products = await res.json();
      products.forEach((p) => {
        const itemPrice = p.price ?? p.selling_price ?? 0;
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${p.barcode}</td>
          <td>${p.name}</td>
          <td style="text-align: right;">${formatRupiah(itemPrice)}</td>
          <td style="text-align: center;">${p.stock}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error("Gagal muat list produk", err);
  }
}

// Simpan Registrasi Member Baru
if (document.getElementById("btn-save-member")) {
  document.getElementById("btn-save-member").onclick = async () => {
    const name = document.getElementById("m-name").value.trim();
    const phone = document.getElementById("m-phone").value.trim();

    if (!name || !phone) {
      alert("Isi nama dan nomor HP member!");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/customers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, phone }),
      });

      if (res.ok) {
        alert("Member berhasil terdaftar!");
        document.getElementById("m-name").value = "";
        document.getElementById("m-phone").value = "";
        closeModal("modal-members");
      } else {
        alert("Gagal mendaftarkan member!");
      }
    } catch (err) {
      alert("Koneksi gagal!");
    }
  };
}

/**
 * Memuat data ringkasan laporan penjualan harian dari backend
 */
async function loadReports() {
  try {
    const res = await fetch(`${API_BASE_URL}/reports/daily-summary`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("report-omset").innerText = formatRupiah(data.total_sales || 0);
      document.getElementById("report-profit").innerText = formatRupiah(data.total_profit || 0);
    }
  } catch (err) {
    console.error("Gagal muat laporan", err);
  }
}

// -----------------------------------------------------------------------------
// 8. SHORTCUTS KEYBOARD GLOBAL (Tombol Pintas Keyboard Kasir)
// -----------------------------------------------------------------------------
document.addEventListener("keydown", (e) => {
  // Tombol F5: Eksekusi Pembayaran / Bayar
  if (e.key === "F5") {
    e.preventDefault();
    if (btnPayMain) btnPayMain.click();
  }
  // Tombol Escape: Menutup semua modal yang sedang terbuka
  else if (e.key === "Escape") {
    ["modal-products", "modal-members", "modal-reports", "modal-receipt-settings", "modal-pending", "modal-receipt"].forEach(closeModal);
  }
  // Tombol Delete: Hapus baris item keranjang yang dipilih
  else if (e.key === "Delete") {
    if (btnDeleteItem) btnDeleteItem.click();
  }
});
