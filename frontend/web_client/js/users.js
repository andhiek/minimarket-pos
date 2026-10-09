const API_URL = `${window.location.protocol}//${window.location.hostname}:8000`;
let allUsers = [];
let editingUserId = null; // Menyimpan ID user jika sedang dalam mode edit

async function fetchUsers() {
  try {
    const response = await fetch(`${API_URL}/api/users`);
    allUsers = await response.json();
    renderTable(allUsers);
  } catch (error) {
    console.error("Gagal memuat data pengguna:", error);
  }
}

function renderTable(dataToRender) {
  const tbody = document.getElementById("userTableBody");
  tbody.innerHTML = "";

  // Hitung statistik ringkasan
  let total = dataToRender.length;
  let adminCount = dataToRender.filter((u) => u.role === "ADMIN").length;
  let kasirCount = dataToRender.filter((u) => u.role === "KASIR").length;

  if (document.getElementById("stat-total")) document.getElementById("stat-total").innerText = total;
  if (document.getElementById("stat-admin")) document.getElementById("stat-admin").innerText = adminCount;
  if (document.getElementById("stat-kasir")) document.getElementById("stat-kasir").innerText = kasirCount;

  if (dataToRender.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 30px;">Tidak ada data karyawan ditemukan.</td></tr>`;
    return;
  }

  dataToRender.forEach((user, index) => {
    const roleBadge = user.role === "ADMIN" ? "badge-admin" : "badge-kasir";
    const statusBadge = user.is_active ? "badge-success" : "badge-danger";
    const statusText = user.is_active ? "Aktif" : "Nonaktif";
    const phoneText = user.phone || "-";
    const usernameText = user.username || "-";

    const row = document.createElement("tr");
    row.innerHTML = `
          <td style="text-align: center;">${index + 1}</td>
          <td><strong>${user.nik || "-"}</strong></td>
          <td>${user.full_name}</td>
          <td><code>${usernameText}</code></td>
          <td>${phoneText}</td>
          <td style="text-align: center;"><span class="badge ${roleBadge}">${user.role}</span></td>
          <td style="text-align: center;"><span class="badge ${statusBadge}">${statusText}</span></td>
          <td style="text-align: center; position: relative;">
              <button class="btn" style="padding: 6px 12px; font-size: 0.9rem; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; border-radius: 6px; cursor: pointer;" onclick="toggleActionDropdown(event, ${user.id})" title="Opsi Aksi">
                  ⋮
              </button>

              <div id="action-dropdown-${user.id}" class="action-dropdown-menu" style="display: none; position: absolute; right: 0; top: 35px; background: #1e1e2d; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px; width: 160px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 9999; text-align: left; padding: 4px;">
                  <button onclick='openModal(${JSON.stringify(user)})' style="width: 100%; text-align: left; background: none; border: none; color: #fff; padding: 8px 12px; font-size: 0.85rem; cursor: pointer; border-radius: 4px; display: flex; align-items: center; gap: 8px;" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='transparent'">
                      ✏️ Edit Data
                  </button>
                  <button onclick="toggleStatus(${user.id})" style="width: 100%; text-align: left; background: none; border: none; color: #fff; padding: 8px 12px; font-size: 0.85rem; cursor: pointer; border-radius: 4px; display: flex; align-items: center; gap: 8px;" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='transparent'">
                      ${user.is_active ? "🔒 Nonaktifkan" : "🔓 Aktifkan"}
                  </button>
                  <div style="height: 1px; background: rgba(255,255,255,0.08); margin: 4px 0;"></div>
                  <button onclick="deleteUser(${user.id})" style="width: 100%; text-align: left; background: none; border: none; color: #f87171; padding: 8px 12px; font-size: 0.85rem; cursor: pointer; border-radius: 4px; display: flex; align-items: center; gap: 8px;" onmouseover="this.style.background='rgba(239,68,68,0.1)'" onmouseout="this.style.background='transparent'">
                      🗑️ Hapus
                  </button>
              </div>
          </td>
        `;
    tbody.appendChild(row);
  });
}

function filterUsers() {
  const keyword = document.getElementById("searchInput").value.toLowerCase();

  const filtered = allUsers.filter((user) => {
    return (user.full_name && user.full_name.toLowerCase().includes(keyword)) || (user.nik && user.nik.toLowerCase().includes(keyword)) || (user.username && user.username.toLowerCase().includes(keyword));
  });

  renderTable(filtered);
}

function toggleActionDropdown(event, userId) {
  event.stopPropagation();
  document.querySelectorAll(".action-dropdown-menu").forEach((menu) => {
    if (menu.id !== `action-dropdown-${userId}`) {
      menu.style.display = "none";
    }
  });
  const dropdown = document.getElementById(`action-dropdown-${userId}`);
  if (dropdown) {
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
  }
}

document.addEventListener("click", () => {
  document.querySelectorAll(".action-dropdown-menu").forEach((menu) => {
    menu.style.display = "none";
  });
});

function openModal(user = null) {
  const modal = document.getElementById("userModal");
  const form = document.getElementById("userForm");
  form.reset();

  if (user && user.id) {
    // Mode Edit
    editingUserId = user.id;
    document.getElementById("nik").value = user.nik || "";
    document.getElementById("full_name").value = user.full_name || "";
    document.getElementById("username").value = user.username || "";
    document.getElementById("password").value = ""; // Kosongkan password saat edit
    document.getElementById("phone").value = user.phone || "";
    document.getElementById("address").value = user.address || "";
    document.getElementById("role").value = user.role || "KASIR";
  } else {
    // Mode Tambah Baru
    editingUserId = null;
  }

  modal.style.display = "flex";
}

function closeModal() {
  document.getElementById("userModal").style.display = "none";
  document.getElementById("userForm").reset();
  editingUserId = null;
}

async function saveUser(event) {
  event.preventDefault();

  const data = {
    nik: document.getElementById("nik").value.trim(),
    full_name: document.getElementById("full_name").value.trim(),
    username: document.getElementById("username").value.trim(),
    password: document.getElementById("password").value.trim(),
    phone: document.getElementById("phone").value.trim(),
    address: document.getElementById("address").value.trim(),
    role: document.getElementById("role").value,
  };

  // Jika sedang mode edit dan password tidak diisi, hapus field password agar tidak menimpa hash lama
  if (editingUserId && !data.password) {
    delete data.password;
  }

  const url = editingUserId ? `${API_URL}/api/users/${editingUserId}` : `${API_URL}/api/users`;
  const method = editingUserId ? "PUT" : "POST";

  try {
    const response = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    if (response.ok) {
      alert(result.message || "Data karyawan berhasil disimpan!");
      closeModal();
      fetchUsers();
    } else {
      alert(result.detail || "Gagal menyimpan data karyawan.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Terjadi kesalahan koneksi ke server.");
  }
}

async function toggleStatus(userId) {
  if (!confirm("Apakah Anda yakin ingin mengubah status aktif karyawan ini?")) return;

  try {
    const response = await fetch(`${API_URL}/api/users/${userId}/toggle-status`, {
      method: "PATCH",
    });
    const result = await response.json();
    if (response.ok) {
      alert(result.message || "Status berhasil diubah.");
      fetchUsers();
    } else {
      alert(result.detail || "Gagal mengubah status.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Terjadi kesalahan koneksi ke server.");
  }
}

async function deleteUser(userId) {
  if (!confirm("Apakah Anda yakin ingin menghapus karyawan ini secara permanen?")) return;

  try {
    const response = await fetch(`${API_URL}/api/users/${userId}`, {
      method: "DELETE",
    });
    const result = await response.json();
    if (response.ok) {
      alert(result.message || "Karyawan berhasil dihapus.");
      fetchUsers();
    } else {
      alert(result.detail || "Gagal menghapus karyawan.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Terjadi kesalahan koneksi ke server.");
  }
}

// Tutup dropdown saat area luar diklik
document.addEventListener("click", () => {
  document.querySelectorAll(".action-dropdown-menu").forEach((menu) => {
    menu.style.display = "none";
  });
});

window.onload = fetchUsers;
