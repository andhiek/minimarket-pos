/**
 * APP.JS - MINIMARKET POS SYSTEM
 * Aplikasi Kasir Frontend yang terhubung dengan FastAPI / SQLModel Backend
 */

// Konfigurasi Endpoint Backend
const API_BASE_URL = `http://${window.location.hostname}:8000/api`;
// -----------------------------------------------------------------------------
// STATE MANAGEMENT (Penyimpanan Status Sementara Aplikasi)
// -----------------------------------------------------------------------------
let cart = []; // Menampung daftar item belanjaan yang dimasukkan kasir
let selectedCartIndex = -1; // Menandai baris tabel keranjang yang sedang dipilih/diklik
let pendingTransactions = []; // Menampung transaksi yang ditahan (Hold/Pending)
let lastCompletedTransaction = null; // Menyimpan data transaksi terakhir untuk fitur cetak ulang struk

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

// Helper Toast Notification (Fallback ke alert jika pos-helpers.js tidak dimuat)
function notify(message, type = "info") {
  if (typeof showToast === "function") {
    showToast(message, type);
  } else {
    alert(message);
  }
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
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
    if (modalId === "modal-products") loadProductList();
    if (modalId === "modal-reports") loadReports();
    if (modalId === "modal-receipt-settings") loadReceiptSettingsToForm();
  }
}

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
async function handleAddProduct() {
  const query = barcodeInput.value.trim();
  if (!query) return;

  try {
    const res = await fetch(`${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`);

    if (res.ok) {
      const products = await res.json();

      if (products.length === 1) {
        const rawProduct = products[0];
        const itemPrice = Number(rawProduct.selling_price ?? rawProduct.price) || 0;

        const productData = {
          id: rawProduct.id,
          barcode: rawProduct.barcode,
          name: rawProduct.name,
          price: itemPrice,
          discount_percent: Number(rawProduct.discount_percent) || 0,
          stock: rawProduct.stock,
          purchase_price: rawProduct.purchase_price || 0,
        };

        addToCart(productData);
        barcodeInput.value = "";
        barcodeInput.focus();
      } else if (products.length > 1) {
        showProductSearchResults(products);
      } else {
        notify("Produk tidak ditemukan!", "error");
      }
    } else {
      notify("Gagal mencari produk!", "error");
    }
  } catch (err) {
    console.error("Error backend search:", err);
    notify("Gagal terhubung ke server backend!", "error");
  }
}

if (barcodeInput) {
  barcodeInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleAddProduct();
  });
}
if (btnAdd) btnAdd.addEventListener("click", handleAddProduct);

function showProductSearchResults(products) {
  let optionsText = "Beberapa produk ditemukan, pilih nomor produk:\n\n";
  products.forEach((p, index) => {
    const price = Number(p.selling_price ?? p.price) || 0;
    const discInfo = p.discount_percent ? ` [Diskon ${p.discount_percent}%]` : "";
    optionsText += `${index + 1}. [${p.barcode}] ${p.name}${discInfo} - ${formatRupiah(price)} (Stok: ${p.stock})\n`;
  });

  const choice = prompt(optionsText + "\nMasukkan nomor pilihan (1 - " + products.length + "):");
  const selectedIndex = parseInt(choice) - 1;

  if (!isNaN(selectedIndex) && selectedIndex >= 0 && selectedIndex < products.length) {
    const selected = products[selectedIndex];
    const selectedPrice = Number(selected.selling_price ?? selected.price) || 0;

    addToCart({
      id: selected.id,
      barcode: selected.barcode,
      name: selected.name,
      price: selectedPrice,
      discount_percent: Number(selected.discount_percent) || 0,
      stock: selected.stock,
      purchase_price: selected.purchase_price || 0,
    });

    barcodeInput.value = "";
    barcodeInput.focus();
  } else if (choice !== null) {
    notify("Pilihan tidak valid!", "warning");
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
        notify(`Member ditemukan: ${customer.name}`, "success");
      } else {
        notify("Member tidak ditemukan!", "warning");
        memberNameDisplay.innerText = "Non-Member";
      }
    } catch (err) {
      notify("Gagal mencari member!", "error");
    }
  });
}

/**
 * Menambahkan objek produk ke dalam keranjang
 */
function addToCart(product) {
  if (!product) return;

  if (product.stock <= 0) {
    notify(`Stok '${product.name}' habis!`, "error");
    return;
  }

  const rawPrice = product.price !== undefined && product.price !== null ? product.price : product.selling_price;
  const itemPrice = Number(rawPrice) || 0;

  const existing = cart.find((item) => item.product_id === product.id);
  if (existing) {
    if (existing.quantity + 1 > product.stock) {
      notify(`Stok tidak mencukupi (Sisa stok: ${product.stock})`, "warning");
      return;
    }
    existing.quantity += 1;
  } else {
    cart.push({
      product_id: product.id,
      barcode: product.barcode,
      name: product.name,
      price: itemPrice,
      discount_percent: product.discount_percent || 0,
      quantity: 1,
      max_stock: product.stock,
    });
  }

  selectedCartIndex = -1;
  renderCart();
}

/**
 * Menghitung Total Belanja dari subtotal produk
 */
function calculateCartTotals(subtotal) {
  const grandTotal = Math.max(0, subtotal);
  return { grandTotal };
}

/**
 * Merender ulang tabel keranjang (dengan perhitungan diskon per produk)
 */
function renderCart() {
  if (!cartTableBody) return;
  cartTableBody.innerHTML = "";
  let subtotal = 0;

  cart.forEach((item, idx) => {
    // Hitung harga setelah diskon produk
    const discPercent = item.discount_percent || 0;
    const finalUnitPrice = item.price * (1 - discPercent / 100);
    const itemSubtotal = finalUnitPrice * item.quantity;
    subtotal += itemSubtotal;

    // Tampilan harga (berikan badge jika produk ada diskon)
    let priceDisplay = formatRupiah(item.price);
    if (discPercent > 0) {
      priceDisplay = `<small style="text-decoration: line-through; color: #888;">${formatRupiah(item.price)}</small> 
                      <span style="color: #ef4444; font-size: 11px; font-weight: bold;">-${discPercent}%</span><br/>
                      <b>${formatRupiah(finalUnitPrice)}</b>`;
    }

    const tr = document.createElement("tr");
    if (idx === selectedCartIndex) tr.style.background = "rgba(59, 130, 246, 0.2)";

    tr.onclick = () => {
      selectedCartIndex = idx;
      renderCart();
    };

    tr.innerHTML = `
      <td>${item.barcode}</td>
      <td><b>${item.name}</b></td>
      <td style="text-align: right;">${priceDisplay}</td>
      <td style="text-align: center;">${item.quantity}</td>
      <td style="text-align: right;"><b>${formatRupiah(itemSubtotal)}</b></td>
    `;
    cartTableBody.appendChild(tr);
  });

  const totals = calculateCartTotals(subtotal);

  if (grandTotalDisplay) grandTotalDisplay.innerText = formatRupiah(totals.grandTotal);
  calculateChange();
}

// Event Listener hitung kembalian secara instan
if (paidAmountInput) paidAmountInput.addEventListener("input", calculateChange);

/**
 * Menghitung selisih/kembalian
 */
function calculateChange() {
  const subtotal = cart.reduce((sum, item) => {
    const finalPrice = item.price * (1 - (item.discount_percent || 0) / 100);
    return sum + finalPrice * item.quantity;
  }, 0);

  const totals = calculateCartTotals(subtotal);
  const paid = parseFloat(paidAmountInput.value) || 0;

  const change = paid - totals.grandTotal;

  if (change >= 0) {
    changeDisplay.innerText = formatRupiah(change);
    changeDisplay.style.color = "var(--text-main)";
  } else {
    changeDisplay.innerText = "Uang Kurang";
    changeDisplay.style.color = "var(--accent-red)";
  }
}

// Hapus item dari keranjang
if (btnDeleteItem) {
  btnDeleteItem.addEventListener("click", () => {
    if (selectedCartIndex >= 0 && selectedCartIndex < cart.length) {
      cart.splice(selectedCartIndex, 1);
      selectedCartIndex = -1;
      renderCart();
      notify("Item berhasil dihapus dari keranjang", "info");
    } else {
      notify("Pilih barang yang ingin dihapus terlebih dahulu!", "warning");
    }
  });
}

// -----------------------------------------------------------------------------
// 4. PENDING / HOLD TRANSACTIONS
// -----------------------------------------------------------------------------
if (btnHold) {
  btnHold.addEventListener("click", () => {
    if (cart.length === 0) {
      notify("Keranjang kosong, tidak ada transaksi untuk ditahan!", "warning");
      return;
    }

    const subtotal = cart.reduce((sum, item) => {
      const finalPrice = item.price * (1 - (item.discount_percent || 0) / 100);
      return sum + finalPrice * item.quantity;
    }, 0);
    const totals = calculateCartTotals(subtotal);

    const heldTransaction = {
      id: Date.now(),
      time: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
      customerPhone: customerPhoneInput.value.trim() || "Non-Member",
      memberName: memberNameDisplay.innerText,
      cart: [...cart],
      total: totals.grandTotal,
    };

    pendingTransactions.push(heldTransaction);

    resetPOSForm();
    updatePendingButtonLabel();
    notify("Transaksi berhasil ditahan (Hold)!", "success");
  });
}

function updatePendingButtonLabel() {
  if (btnPending) btnPending.innerText = `Buka Pending (${pendingTransactions.length})`;
}

if (btnPending) {
  btnPending.addEventListener("click", () => {
    renderPendingList();
    openModal("modal-pending");
  });
}

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

function resumeTransaction(index) {
  if (cart.length > 0) {
    if (!confirm("Keranjang saat ini masih terisi. Ingin menimpa keranjang dengan transaksi pending ini?")) {
      return;
    }
  }

  const tx = pendingTransactions[index];
  cart = [...tx.cart];
  customerPhoneInput.value = tx.customerPhone !== "Non-Member" ? tx.customerPhone : "";
  memberNameDisplay.innerText = tx.memberName;

  pendingTransactions.splice(index, 1);
  updatePendingButtonLabel();
  closeModal("modal-pending");
  renderCart();
  notify("Transaksi pending dipulihkan!", "info");
}

// -----------------------------------------------------------------------------
// 5. CHECKOUT PROCESS
// -----------------------------------------------------------------------------
if (btnPayMain) {
  btnPayMain.onclick = async () => {
    if (!currentUser) {
      notify("Silakan login terlebih dahulu!", "warning");
      window.location.href = "login.html";
      return;
    }

    if (cart.length === 0) {
      notify("Keranjang belanja kosong!", "warning");
      return;
    }

    // Hitung total harga normal dan total potongan diskon produk
    let rawSubtotal = 0;
    let totalDiscountAmount = 0;

    cart.forEach((item) => {
      const itemRawTotal = item.price * item.quantity;
      const discPercent = item.discount_percent || 0;
      const itemDiscAmount = itemRawTotal * (discPercent / 100);

      rawSubtotal += itemRawTotal;
      totalDiscountAmount += itemDiscAmount;
    });

    const finalGrandTotal = rawSubtotal - totalDiscountAmount;

    const paymentMethodInput = document.getElementById("payment-method");
    const paymentMethod = paymentMethodInput ? paymentMethodInput.value : "CASH";
    const paidAmount = parseFloat(paidAmountInput.value) || 0;

    if (paidAmount < finalGrandTotal) {
      notify("Uang Pembayaran Masih Kurang!", "error");
      return;
    }

    const payload = {
      cashier_id: currentCashier.id,
      cashier_name: currentCashier.name,
      customer_phone: customerPhoneInput.value.trim() || null,
      cart_items: cart.map((item) => ({ product_id: item.product_id, quantity: item.quantity })),
      paid_amount: paidAmount,
      discount_amount: totalDiscountAmount,
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
          subtotal: rawSubtotal,
          discount: totalDiscountAmount,
          grandTotal: finalGrandTotal,
          paidAmount: paidAmount,
          changeAmount: data.change_amount,
          paymentMethod: paymentMethod,
          memberName: memberNameDisplay.innerText,
          cashierName: currentCashier.name,
        };

        resetPOSForm();
        showReceiptModal(lastCompletedTransaction);
        notify("Transaksi Berhasil!", "success");
      } else {
        notify(`Gagal: ${data.detail}`, "error");
      }
    } catch (err) {
      notify("Terjadi kesalahan koneksi saat checkout!", "error");
    }
  };
}

function resetPOSForm() {
  cart = [];
  selectedCartIndex = -1;
  paidAmountInput.value = "";
  customerPhoneInput.value = "";
  memberNameDisplay.innerText = "Non-Member";
  renderCart();
  if (barcodeInput) barcodeInput.focus();
}

// -----------------------------------------------------------------------------
// 6. STRUK & LOCALSTORAGE SETTINGS
// -----------------------------------------------------------------------------
function saveReceiptSettings() {
  const settings = {
    storeName: document.getElementById("s-store-name").value.trim() || "MINIMARKET POS",
    storeAddress: document.getElementById("s-store-address").value.trim() || "Jl. Raya Minimarket No. 123",
    footerMsg: document.getElementById("s-footer-msg").value.trim() || "Terima Kasih Telah Berbelanja!",
  };
  localStorage.setItem("pos_receipt_settings", JSON.stringify(settings));
}

function getReceiptSettings() {
  const saved = localStorage.getItem("pos_receipt_settings");
  if (saved) return JSON.parse(saved);
  return {
    storeName: "MINIMARKET POS",
    storeAddress: "Jl. Raya Minimarket No. 123",
    footerMsg: "Terima Kasih Telah Berbelanja!",
  };
}

function loadReceiptSettingsToForm() {
  const settings = getReceiptSettings();
  if (document.getElementById("s-store-name")) document.getElementById("s-store-name").value = settings.storeName;
  if (document.getElementById("s-store-address")) document.getElementById("s-store-address").value = settings.storeAddress;
  if (document.getElementById("s-footer-msg")) document.getElementById("s-footer-msg").value = settings.footerMsg;
}

if (document.getElementById("btn-save-settings")) {
  document.getElementById("btn-save-settings").onclick = () => {
    saveReceiptSettings();
    notify("Pengaturan Struk Berhasil Disimpan!", "success");
    closeModal("modal-receipt-settings");
  };
}

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
    const normalUnitPrice = Number(item.price) || 0;
    const discPercent = Number(item.discount_percent) || 0;

    // Hitung potongan harga per unit & total potongan
    const discountPerUnit = (normalUnitPrice * discPercent) / 100;
    const finalUnitPrice = normalUnitPrice - discountPerUnit;
    const itemSubtotal = finalUnitPrice * item.quantity;

    // Baris rincian diskon (hanya ditampilkan jika ada diskon > 0%)
    let discountRow = "";
    if (discPercent > 0) {
      const totalItemDiscount = discountPerUnit * item.quantity;
      discountRow = `
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #666; font-style: italic; padding-left: 8px;">
          <span>(Disc ${discPercent}% - ${formatRupiah(discountPerUnit)}/pcs)</span>
          <span>-${formatRupiah(totalItemDiscount)}</span>
        </div>
      `;
    }

    const row = document.createElement("div");
    row.style.margin = "4px 0";
    row.innerHTML = `
      <div><b>${item.name}</b></div>
      <div style="display: flex; justify-content: space-between; font-size: 11px;">
        <span>${item.quantity} x ${formatRupiah(normalUnitPrice)}</span>
        <span>${formatRupiah(normalUnitPrice * item.quantity)}</span>
      </div>
      ${discountRow}
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

function printReceipt() {
  const printContents = document.getElementById("receipt-print-area").innerHTML;

  const printFrame = document.createElement("iframe");
  printFrame.style.position = "absolute";
  printFrame.style.width = "0px";
  printFrame.style.height = "0px";
  printFrame.style.border = "none";

  document.body.appendChild(printFrame);

  const frameDoc = printFrame.contentWindow.document;
  frameDoc.open();
  frameDoc.write(`
    <html>
      <head>
        <title>Cetak Struk</title>
        <style>
          body { font-family: 'Courier New', monospace; width: 58mm; margin: 0; padding: 5px; font-size: 12px; }
          b { font-weight: bold; }
        </style>
      </head>
      <body>${printContents}</body>
    </html>
  `);
  frameDoc.close();

  setTimeout(() => {
    printFrame.contentWindow.focus();
    printFrame.contentWindow.print();
    document.body.removeChild(printFrame);
  }, 250);
}

// -----------------------------------------------------------------------------
// 7. ADMIN MODALS API LOGIC
// -----------------------------------------------------------------------------
if (document.getElementById("btn-save-product")) {
  document.getElementById("btn-save-product").onclick = async () => {
    const barcode = document.getElementById("p-barcode").value.trim();
    const name = document.getElementById("p-name").value.trim();
    const price = parseFloat(document.getElementById("p-price").value) || 0;
    const purchase_price = parseFloat(document.getElementById("p-cost").value) || 0;
    const stock = parseInt(document.getElementById("p-stock").value) || 0;
    const category = document.getElementById("p-category") ? document.getElementById("p-category").value : "Umum";

    if (!barcode || !name || price <= 0) {
      notify("Isi barcode, nama, dan harga dengan benar!", "warning");
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
          category: category,
        }),
      });

      if (res.ok) {
        notify("Produk berhasil disimpan!", "success");
        document.getElementById("p-barcode").value = "";
        document.getElementById("p-name").value = "";
        document.getElementById("p-price").value = "";
        document.getElementById("p-cost").value = "";
        document.getElementById("p-stock").value = "";
        if (document.getElementById("p-category")) document.getElementById("p-category").value = "Umum";
        loadProductList();
      } else {
        const errData = await res.json();
        notify(`Gagal menyimpan produk: ${errData.detail || "Terjadi kesalahan"}`, "error");
      }
    } catch (err) {
      notify("Koneksi gagal!", "error");
    }
  };
}

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
        const itemCategory = p.category || "Umum";
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${p.barcode}</td>
          <td>${p.name}</td>
          <td><span style="font-size: 11px; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;">${itemCategory}</span></td>
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

if (document.getElementById("btn-save-member")) {
  document.getElementById("btn-save-member").onclick = async () => {
    const name = document.getElementById("m-name").value.trim();
    const phone = document.getElementById("m-phone").value.trim();

    if (!name || !phone) {
      notify("Isi nama dan nomor HP member!", "warning");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/customers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, phone }),
      });

      if (res.ok) {
        notify("Member berhasil terdaftar!", "success");
        document.getElementById("m-name").value = "";
        document.getElementById("m-phone").value = "";
        closeModal("modal-members");
      } else {
        notify("Gagal mendaftarkan member!", "error");
      }
    } catch (err) {
      notify("Koneksi gagal!", "error");
    }
  };
}

async function loadReports() {
  try {
    const res = await fetch(`${API_BASE_URL}/reports/daily-summary`);
    if (res.ok) {
      const data = await res.json();
      const summary = data.summary || data;

      document.getElementById("report-omset").innerText = formatRupiah(summary.total_sales || 0);
      document.getElementById("report-profit").innerText = formatRupiah(summary.total_profit || 0);

      renderModalPaymentBreakdown(summary.payment_breakdown || {});
    }
  } catch (err) {
    console.error("Gagal muat laporan", err);
  }
}

function renderModalPaymentBreakdown(breakdown) {
  const container = document.getElementById("report-payment-breakdown");
  if (!container) return;

  const defaultMethods = ["CASH", "QRIS", "DEBIT", "TRANSFER"];
  const colors = {
    CASH: "#10b981",
    QRIS: "#3b82f6",
    DEBIT: "#f59e0b",
    TRANSFER: "#8b5cf6",
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

  container.innerHTML = Object.entries(allMethods)
    .map(([method, total]) => {
      const borderColor = colors[method] || "#6b7280";
      return `
        <div style="background: rgba(255, 255, 255, 0.05); border-left: 4px solid ${borderColor}; padding: 8px 12px; border-radius: 6px; flex: 1; min-width: 120px;">
          <small style="color: #aaa; text-transform: uppercase; font-size: 10px; font-weight: bold;">${method}</small>
          <div style="font-size: 14px; font-weight: bold; color: #fff; margin-top: 2px;">
            ${formatRupiah(total || 0)}
          </div>
        </div>
      `;
    })
    .join("");
}

// -----------------------------------------------------------------------------
// 8. SHORTCUTS KEYBOARD GLOBAL
// -----------------------------------------------------------------------------
document.addEventListener("keydown", (e) => {
  // Tombol F5: Eksekusi Pembayaran
  if (e.key === "F5") {
    e.preventDefault();
    if (btnPayMain) btnPayMain.click();
  }
  // Tombol Escape: Menutup semua modal yang sedang terbuka
  else if (e.key === "Escape") {
    ["modal-products", "modal-members", "modal-reports", "modal-receipt-settings", "modal-pending", "modal-receipt"].forEach(closeModal);
  }
  // Tombol Delete: Hapus baris item keranjang
  else if (e.key === "Delete") {
    const activeEl = document.activeElement;
    if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "SELECT")) return;
    if (btnDeleteItem) btnDeleteItem.click();
  }
});

// ==========================================
// FITUR BARCODE SCANNER VIA KAMERA HP
// ==========================================
let cameraStream = null;
let isScanningActive = false;

// Event listener untuk tombol buka kamera
document.getElementById("btn-scan-camera")?.addEventListener("click", () => {
  openCameraModal();
});

function openCameraModal() {
  const modal = document.getElementById("modal-camera-scanner");
  if (modal) modal.classList.add("active");
  startCameraStream();
}

function closeCameraModal() {
  const modal = document.getElementById("modal-camera-scanner");
  if (modal) modal.classList.remove("active");
  stopCameraStream();
}

async function startCameraStream() {
  const videoElement = document.getElementById("camera-video-preview");
  if (!videoElement) return;

  try {
    isScanningActive = true;
    // Meminta izin kamera belakang HP (environment)
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
    });
    videoElement.srcObject = cameraStream;
    videoElement.play();

    // Mulai proses pemindaian frame video
    requestAnimationFrame(scanVideoFrame);
  } catch (error) {
    console.error("Gagal mengakses kamera:", error);
    showToast("Tidak dapat mengakses kamera HP. Periksa izin browser.", "error");
    closeCameraModal();
  }
}

function stopCameraStream() {
  isScanningActive = false;
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
}

// Fungsi pembacaan frame secara berkala
async function scanVideoFrame() {
  if (!isScanningActive) return;

  const videoElement = document.getElementById("camera-video-preview");

  // Jika BarcodeDetector API didukung oleh browser HP
  if ("BarcodeDetector" in window && videoElement && videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
    try {
      const barcodeDetector = new BarcodeDetector({ formats: ["code_128", "ean_13", "ean_8", "upc_a", "qr_code"] });
      const barcodes = await barcodeDetector.detect(videoElement);

      if (barcodes.length > 0) {
        const detectedCode = barcodes[0].rawValue;
        console.log("Barcode terdeteksi via kamera:", detectedCode);

        // Masukkan hasil scan ke input barcode utama
        const barcodeInput = document.getElementById("barcode-input");
        if (barcodeInput) {
          barcodeInput.value = detectedCode;
          // Panggil fungsi tambah produk yang sudah ada di aplikasi Anda
          // Contoh: trigger pencarian atau tekan enter otomatis
          triggerAddProductByBarcode(detectedCode);
        }

        // Tutup modal kamera setelah berhasil mendeteksi
        closeCameraModal();
        showToast(`Berhasil scan: ${detectedCode}`, "success");
        return;
      }
    } catch (err) {
      console.error("Error saat deteksi barcode:", err);
    }
  }

  // Lanjutkan loop scan jika modal masih aktif
  if (isScanningActive) {
    requestAnimationFrame(scanVideoFrame);
  }
}

// Fungsi bantu opsional jika sistem Anda membutuhkan trigger otomatis saat barcode masuk
function triggerAddProductByBarcode(code) {
  const barcodeInput = document.getElementById("barcode-input");
  if (barcodeInput) {
    barcodeInput.value = code;
    // Simulasi tekan enter atau panggil fungsi add item yang ada di app.js Anda
    const enterEvent = new KeyboardEvent("keypress", { key: "Enter", keyCode: 13, bubbles: true });
    barcodeInput.dispatchEvent(enterEvent);
  }
}

// ==========================================
// OPSI ALTERNATIF: SCAN BARCODE VIA FOTO / FILE HP (MENGGUNAKAN ZXING)
// ==========================================
document.getElementById("barcode-file-input")?.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  showToast("Membaca barcode dari foto...", "info");

  try {
    const imageUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = async () => {
      try {
        // Gunakan ZXing BrowserCodeReader untuk mendeteksi barcode dari objek gambar/canvas
        const codeReader = new ZXing.BrowserBarcodeReader();

        // Buat elemen canvas sementara untuk memindai
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);

        // Proses decode gambar
        const result = await codeReader.decodeFromImageElement(img);

        if (result && result.text) {
          const detectedCode = result.text;
          console.log("Barcode berhasil dibaca via ZXing:", detectedCode);

          // Masukkan ke input barcode utama dan proses
          const barcodeInput = document.getElementById("barcode-input");
          if (barcodeInput) {
            barcodeInput.value = detectedCode;
            triggerAddProductByBarcode(detectedCode);
          }
          showToast(`Berhasil scan: ${detectedCode}`, "success");
        } else {
          showToast("Barcode tidak ditemukan dalam foto.", "warning");
        }
      } catch (err) {
        console.error("ZXing decode error:", err);
        showToast("Barcode gagal terbaca. Pastikan foto jelas & tidak buram.", "warning");
      } finally {
        URL.revokeObjectURL(imageUrl);
      }
    };

    img.onerror = () => {
      showToast("Gagal memuat file gambar.", "error");
      URL.revokeObjectURL(imageUrl);
    };

    img.src = imageUrl;
  } catch (err) {
    console.error("Error proses file:", err);
    showToast("Terjadi kesalahan saat memproses foto.", "error");
  } finally {
    e.target.value = "";
  }
});
