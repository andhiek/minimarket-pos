const API_BASE_URL = `http://${window.location.hostname}:8000/api`;
const CATEGORIES = ["Umum", "Makanan", "Minuman", "Sembako", "Perlengkapan Mandi", "Lainnya"];

let productsData = [];
let backupProductsData = [];
let filteredProducts = [];
let isKasir = false;

document.addEventListener("DOMContentLoaded", () => {
  // Check Hak Akses User
  const currentUser = JSON.parse(localStorage.getItem("pos_current_user") || "{}");
  const role = (currentUser.role || "").toLowerCase();
  isKasir = role === "kasir" || role === "cashier";

  setupRoleUI();
  setupEventListeners();
  fetchProducts();
  ensureMobileCameraAttributes();
});

// Memastikan input file kamera memiliki atribut capture="environment" untuk mobile
function ensureMobileCameraAttributes() {
  const cameraInput = document.getElementById("admin-camera-file");
  if (cameraInput && !cameraInput.hasAttribute("capture")) {
    cameraInput.setAttribute("capture", "environment");
  }
}

function setupRoleUI() {
  if (isKasir) {
    // Sembunyikan panel tombol manajemen (Import, Export, Tambah)
    const adminActions = document.getElementById("admin-actions");
    if (adminActions) adminActions.style.display = "none";

    // Sembunyikan header Checkbox All & Aksi
    const thSelect = document.getElementById("th-select");
    const thAksi = document.getElementById("th-aksi");
    if (thSelect) thSelect.style.display = "none";
    if (thAksi) thAksi.style.display = "none";
  }
}

function setupEventListeners() {
  const searchInput = document.getElementById("search-input");
  if (searchInput) searchInput.addEventListener("input", filterProducts);

  const selectAll = document.getElementById("select-all-checkbox");
  if (selectAll) {
    selectAll.addEventListener("change", (e) => toggleSelectAll(e.target.checked));
  }

  const btnBulkDelete = document.getElementById("btn-bulk-delete");
  if (btnBulkDelete) btnBulkDelete.addEventListener("click", deleteSelectedRows);

  const importFile = document.getElementById("import-file");
  if (importFile) importFile.addEventListener("change", handleImportCSV);

  const btnImport = document.getElementById("btn-import");
  if (btnImport) btnImport.addEventListener("click", () => importFile.click());

  const btnExport = document.getElementById("btn-export");
  if (btnExport) btnExport.addEventListener("click", exportToCSV);

  const btnAddRow = document.getElementById("btn-add-row");
  if (btnAddRow) {
    btnAddRow.addEventListener("click", () => {
      document.getElementById("search-input").value = "";
      productsData.unshift({
        barcode: "",
        name: "",
        category: "Umum",
        purchase_price: 0,
        price: 0,
        discount_percent: 0,
        stock: 0,
        isEditing: true,
        isSelected: false,
      });
      filterProducts();
    });
  }

  // Menambahkan atribut capture="environment" pada input file kamera di modal/dokumen jika ada
  const adminCameraInput = document.getElementById("admin-camera-input");
  if (adminCameraInput) {
    adminCameraInput.setAttribute("capture", "environment");
  }
}

function formatRupiah(val) {
  let num = parseFloat(val) || 0;
  if (num > 0 && num < 100) {
    num = num * 1000;
  }
  return Math.round(num).toLocaleString("id-ID");
}

async function fetchProducts() {
  try {
    const res = await fetch(`${API_BASE_URL}/products`);
    if (res.ok) {
      const rawData = await res.json();
      productsData = rawData.map((p) => ({ ...p, isEditing: false, isSelected: false }));
      backupProductsData = JSON.parse(JSON.stringify(productsData));
      filterProducts();
    }
  } catch (e) {
    console.error("Gagal koneksi backend:", e);
    filterProducts();
  }
}

function filterProducts() {
  const query = document.getElementById("search-input").value.toLowerCase().trim();
  if (!query) {
    filteredProducts = [...productsData];
  } else {
    filteredProducts = productsData.filter((p) => (p.name || "").toLowerCase().includes(query) || (p.barcode || "").toLowerCase().includes(query));
  }
  renderExcelTable();
  if (!isKasir) updateBulkDeleteButton();
}

function renderExcelTable() {
  const tbody = document.getElementById("excel-tbody");
  tbody.innerHTML = "";

  // 10 kolom total (Admin) / 8 kolom (Kasir - tanpa Checkbox & Aksi)
  const colSpanCount = isKasir ? 8 : 10;

  if (filteredProducts.length === 0) {
    tbody.innerHTML = `<tr><td colspan="${colSpanCount}" style="text-align: center; color: #6c7086; padding: 20px;">Data produk tidak ditemukan.</td></tr>`;
    return;
  }

  filteredProducts.forEach((p, index) => {
    const originalIndex = productsData.indexOf(p);
    const tr = document.createElement("tr");

    // Hanya Admin yang bisa double click untuk mengedit
    if (!isKasir) {
      tr.ondblclick = (e) => {
        if (!p.isEditing && e.target.tagName !== "BUTTON" && e.target.tagName !== "SELECT" && e.target.tagName !== "INPUT") {
          enableEdit(originalIndex);
        }
      };
    }

    const checkboxTd = isKasir
      ? ""
      : `
      <td style="text-align: center;">
        <input type="checkbox" ${p.isSelected ? "checked" : ""} onchange="toggleRowSelect(${originalIndex}, this.checked)" />
      </td>
    `;

    if (p.isEditing && !isKasir) {
      const catOptions = CATEGORIES.map((c) => `<option value="${c}" ${(p.category || "Umum") === c ? "selected" : ""}>${c}</option>`).join("");

      tr.innerHTML = `
        ${checkboxTd}
        <td style="text-align: center; color: #89b4fa;">${index + 1}</td>
        <td><input class="excel-input" placeholder="Wajib isi..." value="${p.barcode || ""}" oninput="updateProductField(${originalIndex}, 'barcode', this.value)"/></td>
        <td><input class="excel-input" placeholder="Wajib isi..." value="${p.name || ""}" oninput="updateProductField(${originalIndex}, 'name', this.value)"/></td>
        <td>
          <select class="excel-select" onchange="updateProductField(${originalIndex}, 'category', this.value)">
            ${catOptions}
          </select>
        </td>
        <td><input class="excel-input" type="number" style="text-align: right;" value="${p.purchase_price || p.cost || 0}" oninput="updateProductField(${originalIndex}, 'purchase_price', this.value)"/></td>
        <td><input class="excel-input" type="number" style="text-align: right;" value="${p.price || p.selling_price || 0}" oninput="updateProductField(${originalIndex}, 'price', this.value)"/></td>
        <td><input class="excel-input" type="number" style="text-align: center;" min="0" max="100" value="${p.discount_percent ?? 0}" oninput="updateProductField(${originalIndex}, 'discount_percent', this.value)"/></td>
        <td><input class="excel-input" type="number" style="text-align: center;" value="${p.stock || 0}" oninput="updateProductField(${originalIndex}, 'stock', this.value)"/></td>
        <td style="text-align: center; white-space: nowrap;">
          <button class="btn-action" title="Simpan" onclick="saveRow(${originalIndex})">💾</button>
          <button class="btn-action" title="Batal Edit" onclick="cancelEdit(${originalIndex})">❌</button>
          <button class="btn-action" title="Hapus" onclick="deleteRow(${originalIndex})">🗑️</button>
        </td>
      `;
    } else {
      const actionTd = isKasir
        ? ""
        : `
        <td style="text-align: center;">
          <button class="btn-action" title="Edit Baris" onclick="enableEdit(${originalIndex})">✏️</button>
          <button class="btn-action" title="Hapus" onclick="deleteRow(${originalIndex})">🗑️</button>
        </td>
      `;

      tr.innerHTML = `
        ${checkboxTd}
        <td style="text-align: center; color: #89b4fa;">${index + 1}</td>
        <td><span class="cell-text">${p.barcode || "-"}</span></td>
        <td><span class="cell-text">${p.name || "-"}</span></td>
        <td><span class="cell-text">${p.category || "Umum"}</span></td>
        <td style="text-align: right;"><span class="cell-text">${formatRupiah(p.purchase_price || p.cost)}</span></td>
        <td style="text-align: right;"><span class="cell-text">${formatRupiah(p.price || p.selling_price)}</span></td>
        <td style="text-align: center;"><span class="cell-text">${p.discount_percent ?? 0}%</span></td>
        <td style="text-align: center;"><span class="cell-text">${p.stock || 0}</span></td>
        ${actionTd}
      `;
    }
    tbody.appendChild(tr);
  });
}

function toggleRowSelect(index, isChecked) {
  productsData[index].isSelected = isChecked;
  updateBulkDeleteButton();
}

function toggleSelectAll(isChecked) {
  filteredProducts.forEach((p) => {
    const originalIndex = productsData.indexOf(p);
    if (originalIndex !== -1) {
      productsData[originalIndex].isSelected = isChecked;
    }
  });
  renderExcelTable();
  updateBulkDeleteButton();
}

function updateBulkDeleteButton() {
  if (isKasir) return;
  const selectedItems = productsData.filter((p) => p.isSelected);
  const countSpan = document.getElementById("selected-count");
  const bulkBtn = document.getElementById("btn-bulk-delete");

  if (countSpan) countSpan.textContent = selectedItems.length;
  if (bulkBtn) {
    bulkBtn.style.display = selectedItems.length > 0 ? "flex" : "none";
  }
}

async function deleteSelectedRows() {
  if (isKasir) return;
  const selectedItems = productsData.filter((p) => p.isSelected);
  if (selectedItems.length === 0) return;

  if (!confirm(`Yakin ingin menghapus ${selectedItems.length} produk yang dipilih secara serentak?`)) {
    return;
  }

  for (const item of selectedItems) {
    if (item.id) {
      try {
        await fetch(`${API_BASE_URL}/products/${item.id}`, { method: "DELETE" });
      } catch (e) {
        console.error(`Gagal menghapus produk ID ${item.id}:`, e);
      }
    }
  }

  productsData = productsData.filter((p) => !p.isSelected);
  backupProductsData = JSON.parse(JSON.stringify(productsData));
  document.getElementById("select-all-checkbox").checked = false;
  filterProducts();
}

function enableEdit(index) {
  if (isKasir) return;
  backupProductsData[index] = JSON.parse(JSON.stringify(productsData[index]));
  productsData[index].isEditing = true;
  filterProducts();
}

function cancelEdit(index) {
  const item = productsData[index];
  if (!item.id && !backupProductsData[index]) {
    productsData.splice(index, 1);
    backupProductsData.splice(index, 1);
  } else {
    productsData[index] = JSON.parse(JSON.stringify(backupProductsData[index]));
    productsData[index].isEditing = false;
  }
  filterProducts();
}

function updateProductField(index, field, value) {
  if (field === "discount_percent" || field === "purchase_price" || field === "price" || field === "stock") {
    productsData[index][field] = value === "" ? 0 : parseFloat(value) || 0;
  } else {
    productsData[index][field] = value;
  }
}

async function saveRow(index) {
  if (isKasir) return;
  const item = productsData[index];

  const barcode = (item.barcode || "").trim();
  const name = (item.name || "").trim();

  let price = parseFloat(item.price || item.selling_price) || 0;
  let purchasePrice = parseFloat(item.purchase_price || item.cost) || 0;
  let discountPercent = parseFloat(item.discount_percent) || 0;

  if (price > 0 && price < 100) price = price * 1000;
  if (purchasePrice > 0 && purchasePrice < 100) purchasePrice = purchasePrice * 1000;

  if (!barcode) {
    alert("Gagal Simpan: Barcode tidak boleh kosong!");
    return;
  }
  if (!name) {
    alert("Gagal Simpan: Nama Produk tidak boleh kosong!");
    return;
  }
  if (price <= 0) {
    alert("Gagal Simpan: Harga Jual harus lebih besar dari 0!");
    return;
  }

  const isUpdate = Boolean(item.id);
  const method = isUpdate ? "PUT" : "POST";
  const url = isUpdate ? `${API_BASE_URL}/products/${item.id}` : `${API_BASE_URL}/products`;

  const payload = {
    barcode: barcode,
    name: name,
    price: price,
    purchase_price: purchasePrice,
    discount_percent: discountPercent,
    stock: parseInt(item.stock) || 0,
    category: item.category || "Umum",
  };

  try {
    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      const savedProduct = await res.json();

      productsData[index] = {
        ...savedProduct,
        isEditing: false,
        isSelected: item.isSelected || false,
      };
      backupProductsData[index] = JSON.parse(JSON.stringify(productsData[index]));

      filterProducts();
    } else {
      const errData = await res.json();
      alert(`Gagal menyimpan: ${errData.detail || "Terjadi kesalahan di server"}`);
    }
  } catch (e) {
    console.error("Error saveRow:", e);
    alert("Terjadi kesalahan koneksi ke backend.");
  }
}

async function deleteRow(index) {
  if (isKasir) return;
  const item = productsData[index];
  if (item.id) {
    if (!confirm(`Yakin ingin menghapus barang "${item.name || "Baris ini"}"?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/products/${item.id}`, { method: "DELETE" });
      if (!res.ok) {
        alert("Gagal menghapus produk di backend.");
        return;
      }
    } catch (e) {
      alert("Error koneksi saat menghapus.");
      return;
    }
  }
  productsData.splice(index, 1);
  backupProductsData.splice(index, 1);
  filterProducts();
}

function exportToCSV() {
  if (isKasir || productsData.length === 0) {
    alert("Tidak ada data produk untuk diexport!");
    return;
  }
  let csvContent = "data:text/csv;charset=utf-8,Barcode,Nama Produk,Kategori,Harga Beli,Harga Jual,Diskon (%),Stok\n";

  productsData.forEach((p) => {
    const row = [`"${p.barcode || ""}"`, `"${p.name || ""}"`, `"${p.category || "Umum"}"`, p.purchase_price || p.cost || 0, p.price || p.selling_price || 0, p.discount_percent || 0, p.stock || 0].join(",");
    csvContent += row + "\n";
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `database_produk_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

async function handleImportCSV(event) {
  if (isKasir) return;
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE_URL}/products/import-csv`, {
      method: "POST",
      body: formData,
    });

    if (res.ok) {
      const result = await res.json();
      alert(result.message || "Import CSV Berhasil!");
      await fetchProducts();
    } else {
      const err = await res.json();
      alert(`Gagal Import CSV: ${err.detail || "Format CSV tidak sesuai."}`);
    }
  } catch (e) {
    console.error("Gagal Import CSV:", e);
    alert("Terjadi kesalahan koneksi saat mengunggah file CSV.");
  } finally {
    event.target.value = "";
  }
}

// ==========================================
// FITUR SCAN BARCODE KAMERA UNTUK ADMIN GUDANG
// ==========================================
async function handleProductCameraScan(index, event) {
  const file = event.target.files[0];
  if (!file) return;

  alert("Memproses foto barcode...");

  try {
    const imageUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = async () => {
      try {
        const codeReader = new ZXing.BrowserBarcodeReader();
        const result = await codeReader.decodeFromImageElement(img);

        if (result && result.text) {
          const detectedCode = result.text;
          console.log("Barcode produk terdeteksi:", detectedCode);

          // Update data produk di baris tersebut
          productsData[index].barcode = detectedCode;
          filterProducts(); // Render ulang tabel agar nilai input terisi otomatis
          alert(`Berhasil scan barcode: ${detectedCode}`);
        } else {
          alert("Barcode tidak ditemukan dalam foto. Coba ambil ulang lebih jelas.");
        }
      } catch (err) {
        console.error("ZXing decode error:", err);
        alert("Gagal membaca barcode dari foto. Pastikan tidak buram.");
      } finally {
        URL.revokeObjectURL(imageUrl);
      }
    };

    img.onerror = () => {
      alert("Gagal memuat file foto.");
      URL.revokeObjectURL(imageUrl);
    };

    img.src = imageUrl;
  } catch (err) {
    console.error("Error proses file foto:", err);
    alert("Terjadi kesalahan saat memproses foto.");
  } finally {
    event.target.value = "";
  }
}

// ==========================================
// FITUR SCAN KAMERA LANGSUNG (TANPA MODAL BERAT)
// ==========================================

// Fungsi yang dipicu saat tombol "Scan Kamera" diketuk
function triggerDirectCamera() {
  const fileInput = document.getElementById("direct-camera-input");
  if (fileInput) {
    // Reset value agar event 'onchange' tetap terbaca meskipun file yang sama dipilih dua kali
    fileInput.value = "";
    fileInput.click();
  } else {
    alert("Elemen input kamera tidak ditemukan di halaman!");
  }
}

// Proses Foto Menggunakan ZXing dengan Indikator Loading Otomatis
async function processAdminCameraScan(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Buat elemen indikator loading sederhana secara dinamis jika belum ada
  let loadingIndicator = document.getElementById("scan-loading-indicator");
  if (!loadingIndicator) {
    loadingIndicator = document.createElement("div");
    loadingIndicator.id = "scan-loading-indicator";
    loadingIndicator.style.cssText =
      "position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #1e1e2e; color: #f9e2af; padding: 12px 24px; border-radius: 8px; z-index: 99999; box-shadow: 0 4px 12px rgba(0,0,0,0.5); font-weight: 600;";
    loadingIndicator.innerHTML = "⏳ Sedang memproses dan membaca piksel barcode...";
    document.body.appendChild(loadingIndicator);
  } else {
    loadingIndicator.style.display = "block";
  }

  try {
    const imageUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = async () => {
      try {
        const codeReader = new ZXing.BrowserBarcodeReader();
        const result = await codeReader.decodeFromImageElement(img);

        if (result && result.text) {
          const detectedCode = result.text;
          console.log("Admin Scan Berhasil:", detectedCode);

          // Cek apakah ada baris yang sedang aktif diedit atau buat baris baru otomatis
          let targetIndex = productsData.findIndex((p) => p.isEditing);

          if (targetIndex === -1) {
            // Jika belum ada baris aktif diedit, buat baris baru otomatis dengan barcode ini
            productsData.unshift({
              barcode: detectedCode,
              name: "",
              category: "Umum",
              purchase_price: 0,
              price: 0,
              discount_percent: 0,
              stock: 0,
              isEditing: true,
              isSelected: false,
            });
          } else {
            // Masukkan ke baris yang sedang diedit
            productsData[targetIndex].barcode = detectedCode;
          }

          filterProducts();
          alert(`✨ Berhasil memindai barcode: ${detectedCode}`);
        } else {
          alert("⚠️ Barcode tidak ditemukan dalam foto. Pastikan pencahayaan cukup & tidak buram.");
        }
      } catch (err) {
        console.error("ZXing decode error:", err);
        alert("⚠️ Gagal membaca barcode dari foto. Coba ambil dari sudut lain.");
      } finally {
        URL.revokeObjectURL(imageUrl);
        if (loadingIndicator) loadingIndicator.style.display = "none";
      }
    };

    img.onerror = () => {
      alert("Gagal memuat file gambar.");
      if (loadingIndicator) loadingIndicator.style.display = "none";
      URL.revokeObjectURL(imageUrl);
    };

    img.src = imageUrl;
  } catch (err) {
    console.error("Error file process:", err);
    alert("Terjadi kesalahan sistem saat memproses foto.");
    if (loadingIndicator) loadingIndicator.style.display = "none";
  } finally {
    event.target.value = "";
  }
}

// ==========================================
// PUSAT FITUR SCAN KAMERA DENGAN KOMPRESI OTOMATIS
// ==========================================
function triggerProductCamera() {
  let dynamicInput = document.getElementById("dynamic-camera-scanner");
  if (!dynamicInput) {
    dynamicInput = document.createElement("input");
    dynamicInput.type = "file";
    dynamicInput.id = "dynamic-camera-scanner";
    dynamicInput.accept = "image/*";
    dynamicInput.capture = "environment";
    dynamicInput.style.display = "none";
    document.body.appendChild(dynamicInput);

    dynamicInput.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const showMsg = typeof notify === "function" ? notify : (msg) => alert(msg);
      showMsg("⏳ Mengoptimalkan & membaca foto barcode...", "info");

      try {
        let detectedCode = "";

        // Kompresi gambar agar tidak "Kesalahan Sistem" akibat memori/resolusi terlalu besar
        const compressedBlob = await resizeImageToMax(file, 1200);

        // 1. Coba deteksi via BarcodeDetector bawaan HP
        if ("BarcodeDetector" in window) {
          try {
            const barcodeDetector = new BarcodeDetector({
              formats: ["ean_13", "ean_8", "code_128", "code_39", "upc_a", "upc_e", "qr_code"],
            });
            const bitmap = await createImageBitmap(compressedBlob);
            const results = await barcodeDetector.detect(bitmap);
            if (results && results.length > 0) {
              detectedCode = results[0].rawValue;
            }
          } catch (err) {
            console.log("BarcodeDetector native gagal, beralih ke ZXing:", err);
          }
        }

        // 2. Jika belum ketemu, gunakan ZXing
        if (!detectedCode) {
          const zxingLib = window.ZXing || (typeof ZXing !== "undefined" ? ZXing : null);
          if (zxingLib && zxingLib.BrowserBarcodeReader) {
            const imageUrl = URL.createObjectURL(compressedBlob);
            const img = new Image();

            await new Promise((resolve, reject) => {
              img.onload = resolve;
              img.onerror = reject;
              img.src = imageUrl;
            });

            const codeReader = new zxingLib.BrowserBarcodeReader();
            const result = await codeReader.decodeFromImageElement(img);
            if (result && result.text) {
              detectedCode = result.text;
            }
            URL.revokeObjectURL(imageUrl);
          } else {
            throw new Error("Library ZXing tidak tersedia.");
          }
        }

        // 3. Masukkan hasil scan ke tabel
        if (detectedCode) {
          showMsg(`✨ SUKSES! Barcode: ${detectedCode}`, "success");

          const searchInput = document.getElementById("search-input");
          if (searchInput) searchInput.value = "";

          let targetIndex = productsData.findIndex((p) => p.isEditing);

          if (targetIndex === -1) {
            productsData.unshift({
              barcode: detectedCode,
              name: "",
              category: "Umum",
              purchase_price: 0,
              price: 0,
              discount_percent: 0,
              stock: 1,
              isEditing: true,
              isSelected: false,
            });
          } else {
            productsData[targetIndex].barcode = detectedCode;
          }

          filterProducts();
        } else {
          showMsg("⚠️ Barcode tidak terbaca. Pastikan posisi tegak, terang, dan tidak buram.", "warning");
        }
      } catch (err) {
        console.error("Error proses scan:", err);
        showMsg("Gagal membaca barcode: Pastikan kamera stabil saat mengambil foto.", "error");
      } finally {
        dynamicInput.value = "";
      }
    });
  }

  dynamicInput.click();
}

// Fungsi pembantu untuk memperkecil ukuran resolusi gambar secara otomatis
function resizeImageToMax(file, maxDimension) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > maxDimension) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          }
        } else {
          if (height > maxDimension) {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (blob) resolve(blob);
            else reject(new Error("Gagal kompresi gambar"));
          },
          "image/jpeg",
          0.85,
        );
      };
      img.onerror = reject;
      img.src = e.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
