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

function renderTable(users) {
  const tbody = document.getElementById("userTableBody");
  tbody.innerHTML = "";

  if (users.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Tidak ada data karyawan ditemukan.</td></tr>`;
    return;
  }

  users.forEach((user, index) => {
    const row = document.createElement("tr");

    const roleBadge = user.role === "ADMIN" ? "badge-admin" : "badge-kasir";
    const statusBadge = user.is_active ? "badge-active" : "badge-inactive";
    const statusText = user.is_active ? "Aktif" : "Non-Aktif";
    const toggleBtnText = user.is_active ? "Nonaktifkan" : "Aktifkan";
    const toggleBtnClass = user.is_active ? "btn-danger" : "btn-success";
    const phoneText = user.phone || "-";

    // Di dalam fungsi renderTable(users), bagian pembentukan innerHTML baris tabel:
    row.innerHTML = `
      <td>${index + 1}</td>
      <td><strong>${user.nik || "-"}</strong></td>
      <td>${user.full_name}</td>
      <td>${phoneText}</td>
      <td><span class="badge ${roleBadge}">${user.role}</span></td>
      <td><span class="badge ${statusBadge}">${statusText}</span></td>
      <td style="text-align: center;">
          <button class="btn" style="padding: 6px 10px; font-size: 0.8rem; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; margin-right: 4px;" onclick='openModal(${JSON.stringify(user)})' title="Edit Karyawan">✏️</button>
          <button class="btn" style="padding: 6px 10px; font-size: 0.8rem; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; margin-right: 4px;" onclick="toggleStatus(${user.id})" title="${toggleBtnText}">
              ${user.is_active ? "🔒" : "🔓"}
          </button>
          <button class="btn" style="padding: 6px 10px; font-size: 0.8rem; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171;" onclick="deleteUser(${user.id})" title="Hapus Karyawan">🗑️</button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function filterUsers() {
  const keyword = document.getElementById("searchInput").value.toLowerCase();
  const filtered = allUsers.filter((user) => (user.nik && user.nik.toLowerCase().includes(keyword)) || (user.full_name && user.full_name.toLowerCase().includes(keyword)));
  renderTable(filtered);
}

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

window.onload = fetchUsers;
