// ─── Sidebar Toggle ───
document.addEventListener("DOMContentLoaded", () => {
    const hamburger = document.getElementById("hamburger");
    const sidebar = document.getElementById("sidebar");
    if (hamburger && sidebar) {
        hamburger.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
        document.addEventListener("click", (e) => {
            if (
                window.innerWidth <= 768 &&
                sidebar.classList.contains("open") &&
                !sidebar.contains(e.target) &&
                !hamburger.contains(e.target)
            ) {
                sidebar.classList.remove("open");
            }
        });
    }
});

// ─── Bill Form ───
let rowIndex = 0;
let productCache = typeof products !== "undefined" ? products : [];
let customerCache = typeof customers !== "undefined" ? customers : [];

function addRow(data) {
    rowIndex++;
    const tbody = document.getElementById("itemsBody");
    const tr = document.createElement("tr");
    tr.id = `row-${rowIndex}`;
    tr.innerHTML = `
        <td class="row-num">${rowIndex}</td>
        <td>
            <select class="form-control product-select" data-row="${rowIndex}" onchange="onProductChange(${rowIndex})" style="font-size:12px;">
                <option value="">-- Select --</option>
                ${productCache.map(p => `<option value="${p.id}" ${data && data.product_id == p.id ? 'selected' : ''}>${p.name}</option>`).join("")}
            </select>
            <input type="hidden" class="product-name" value="${data ? data.product_name : ''}">
            <input type="hidden" class="hsn-code" value="${data ? data.hsn_code : ''}">
        </td>
        <td><span class="hsn-display">${data ? data.hsn_code : ''}</span></td>
        <td><input type="number" class="form-control item-qty" value="${data ? data.quantity : 1}" min="0.5" step="0.5" oninput="calcRow(${rowIndex})" style="width:70px;"></td>
        <td><input type="number" class="form-control item-price" value="${data ? data.price : ''}" step="0.01" oninput="calcRow(${rowIndex})" style="width:100px;"></td>
        <td><input type="number" class="form-control item-gst" value="${data ? data.gst_rate : 0}" step="0.1" oninput="calcRow(${rowIndex})" style="width:70px;" ${data && data.gst_rate !== undefined ? 'readonly' : ''}></td>
        <td class="gst-amt">₹0.00</td>
        <td class="row-total">₹0.00</td>
        <td><button type="button" class="btn btn-xs btn-danger" onclick="removeRow(${rowIndex})" title="Remove">&times;</button></td>
    `;
    tbody.appendChild(tr);
    if (data) calcRow(rowIndex);
    recalcSummary();
}

function removeRow(index) {
    const row = document.getElementById(`row-${index}`);
    if (row) { row.remove(); recalcSummary(); }
}

function onProductChange(index) {
    const sel = document.querySelector(`.product-select[data-row="${index}"]`);
    const pid = parseInt(sel.value);
    const prod = productCache.find(p => p.id === pid);
    const row = document.getElementById(`row-${index}`);
    if (!row) return;

    const nameInput = row.querySelector(".product-name");
    const hsnInput = row.querySelector(".hsn-code");
    const hsnDisplay = row.querySelector(".hsn-display");
    const priceInput = row.querySelector(".item-price");
    const gstInput = row.querySelector(".item-gst");

    if (prod) {
        nameInput.value = prod.name;
        hsnInput.value = prod.hsn_code || "";
        hsnDisplay.textContent = prod.hsn_code || "";
        priceInput.value = prod.price;
        gstInput.value = prod.gst_rate;
    } else {
        nameInput.value = "";
        hsnInput.value = "";
        hsnDisplay.textContent = "";
        priceInput.value = "";
        gstInput.value = 0;
    }
    calcRow(index);
}

function calcRow(index) {
    const row = document.getElementById(`row-${index}`);
    if (!row) return;
    const qty = parseFloat(row.querySelector(".item-qty").value) || 0;
    const price = parseFloat(row.querySelector(".item-price").value) || 0;
    const gstRate = parseFloat(row.querySelector(".item-gst").value) || 0;
    const isGst = document.getElementById("isGst").checked;

    const subtotal = qty * price;
    const gstAmt = isGst ? (subtotal * gstRate / 100) : 0;
    const total = subtotal + gstAmt;

    row.querySelector(".gst-amt").textContent = `₹${gstAmt.toFixed(2)}`;
    row.querySelector(".row-total").textContent = `₹${total.toFixed(2)}`;
    recalcSummary();
}

function recalcSummary() {
    const rows = document.querySelectorAll("#itemsBody tr");
    let subtotal = 0;
    let gstTotal = 0;
    let grandTotal = 0;

    rows.forEach(row => {
        const qty = parseFloat(row.querySelector(".item-qty").value) || 0;
        const price = parseFloat(row.querySelector(".item-price").value) || 0;
        subtotal += qty * price;

        const gstAmtText = row.querySelector(".gst-amt").textContent;
        gstTotal += parseFloat(gstAmtText.replace("₹", "")) || 0;
    });

    grandTotal = subtotal + gstTotal;

    document.getElementById("subtotalDisplay").textContent = `₹${subtotal.toFixed(2)}`;
    document.getElementById("gstTotalDisplay").textContent = `₹${gstTotal.toFixed(2)}`;
    document.getElementById("grandTotalDisplay").textContent = `₹${grandTotal.toFixed(2)}`;
}

// ─── GST Toggle ───
document.addEventListener("DOMContentLoaded", () => {
    const gstToggle = document.getElementById("isGst");
    if (gstToggle) {
        gstToggle.addEventListener("change", () => {
            const rows = document.querySelectorAll("#itemsBody tr");
            rows.forEach((_, i) => {
                const rowId = i + 1;
                const el = document.getElementById(`row-${rowId}`);
                if (el) calcRow(rowId);
            });
            recalcSummary();
        });
    }
});

// ─── Customer Select ───
document.addEventListener("DOMContentLoaded", () => {
    const sel = document.getElementById("customerSelect");
    const phoneInput = document.getElementById("customerPhone");
    const gstinInput = document.getElementById("customerGstin");
    if (sel && phoneInput && gstinInput) {
        sel.addEventListener("change", () => {
            const cid = parseInt(sel.value);
            const cust = customerCache.find(c => c.id === cid);
            if (cust) {
                phoneInput.value = cust.phone || "";
                gstinInput.value = cust.gstin || "";
            } else {
                phoneInput.value = "";
                gstinInput.value = "";
            }
        });
    }
});

// ─── Submit Bill ───
function submitBill() {
    const rows = document.querySelectorAll("#itemsBody tr");
    if (rows.length === 0) return alert("Add at least one item.");

    const items = [];
    let valid = true;

    rows.forEach(row => {
        const nameInput = row.querySelector(".product-name");
        const hsnInput = row.querySelector(".hsn-code");
        const qty = parseFloat(row.querySelector(".item-qty").value) || 0;
        const price = parseFloat(row.querySelector(".item-price").value) || 0;
        const gstRate = parseFloat(row.querySelector(".item-gst").value) || 0;

        if (!nameInput.value) { valid = false; return; }
        if (qty <= 0 || price <= 0) { valid = false; return; }

        items.push({
            product_name: nameInput.value,
            hsn_code: hsnInput.value,
            quantity: qty,
            price: price,
            gst_rate: gstRate,
        });
    });

    if (!valid) return alert("Please fill all item fields correctly.");

    const custSelect = document.getElementById("customerSelect");
    const customerId = parseInt(custSelect.value) || null;

    const payload = {
        customer_id: customerId,
        customer_name: customerId
            ? (customerCache.find(c => c.id === customerId)?.name || "")
            : "Walk-in Customer",
        customer_phone: document.getElementById("customerPhone").value || "",
        customer_gstin: document.getElementById("customerGstin").value || "",
        is_gst: document.getElementById("isGst").checked,
        items: items,
    };

    fetch("/api/bills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
        .then(r => {
            if (!r.ok) throw new Error("Server error");
            return r.json();
        })
        .then(bill => {
            window.location.href = `/bills/${bill.id}`;
        })
        .catch(err => {
            alert("Error saving bill: " + err.message);
        });
}

function resetForm() {
    if (!confirm("Reset the form?")) return;
    document.getElementById("itemsBody").innerHTML = "";
    rowIndex = 0;
    recalcSummary();
}

// ─── Customer Modal (from create bill) ───
function openCustomerModal() {
    const el = document.getElementById("customerModal");
    if (el) {
        document.getElementById("newCustName").value = "";
        document.getElementById("newCustPhone").value = "";
        document.getElementById("newCustEmail").value = "";
        document.getElementById("newCustAddress").value = "";
        document.getElementById("newCustGstin").value = "";
        el.classList.add("show");
    }
}

function closeCustomerModal() {
    const el = document.getElementById("customerModal");
    if (el) el.classList.remove("show");
}

function saveCustomer() {
    const data = {
        name: document.getElementById("newCustName").value.trim(),
        phone: document.getElementById("newCustPhone").value.trim(),
        email: document.getElementById("newCustEmail").value.trim(),
        address: document.getElementById("newCustAddress").value.trim(),
        gstin: document.getElementById("newCustGstin").value.trim(),
    };
    if (!data.name) return alert("Name is required");

    fetch("/api/customers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    })
        .then(r => r.json())
        .then(cust => {
            customerCache.push(cust);
            const sel = document.getElementById("customerSelect");
            const opt = document.createElement("option");
            opt.value = cust.id;
            opt.textContent = `${cust.name} ${cust.phone ? "— " + cust.phone : ""}`;
            sel.appendChild(opt);
            sel.value = cust.id;
            sel.dispatchEvent(new Event("change"));
            closeCustomerModal();
        })
        .catch(() => alert("Error saving customer"));
}

// ─── Product Modal (from create bill) ───
function openProductModal() {
    const el = document.getElementById("productModal");
    if (el) {
        document.getElementById("newProdName").value = "";
        document.getElementById("newProdHsn").value = "";
        document.getElementById("newProdPrice").value = "";
        document.getElementById("newProdGst").value = "0";
        el.classList.add("show");
    }
}

function closeProductModal() {
    const el = document.getElementById("productModal");
    if (el) el.classList.remove("show");
}

function saveProduct() {
    const data = {
        name: document.getElementById("newProdName").value.trim(),
        hsn_code: document.getElementById("newProdHsn").value.trim(),
        price: parseFloat(document.getElementById("newProdPrice").value) || 0,
        gst_rate: parseFloat(document.getElementById("newProdGst").value) || 0,
    };
    if (!data.name) return alert("Name is required");
    if (data.price <= 0) return alert("Price must be > 0");

    fetch("/api/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    })
        .then(r => r.json())
        .then(prod => {
            productCache.push(prod);
            // Add option to all product selects
            document.querySelectorAll(".product-select").forEach(sel => {
                const opt = document.createElement("option");
                opt.value = prod.id;
                opt.textContent = prod.name;
                sel.appendChild(opt);
            });
            closeProductModal();
        })
        .catch(() => alert("Error saving product"));
}

// ─── Auto-add first row on create bill page ───
document.addEventListener("DOMContentLoaded", () => {
    const tbody = document.getElementById("itemsBody");
    if (tbody && tbody.children.length === 0 && window.location.pathname.includes("/bills/new")) {
        addRow();
    }
});
