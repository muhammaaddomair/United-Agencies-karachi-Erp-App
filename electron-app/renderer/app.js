const state = {
  session: null,
  invoices: [],
  orders: [],
  payments: [],
  inventory: [],
  activeView: 'invoices',
  selectedInventoryId: null,
  invoiceFilters: {
    billNo: '',
    toText: '',
    dateFrom: '',
    dateTo: '',
  },
  orderFilters: {
    institutionName: '',
    dateFrom: '',
    dateTo: '',
  },
  paymentFilters: {
    billNo: '',
    invoiceDate: '',
    dateFrom: '',
    dateTo: '',
  },
  inventoryFilters: {
    regNo: '',
    batchNo: '',
    productName: '',
  },
  selectedProducts: new Map(),
  invoiceModalOpen: false,
  invoiceDraft: null,
  orderModal: null,
  productSelectorOpen: false,
  inventoryModal: null,
  productSelectorQty: '',
  productSelectorSelectedId: null,
};

const appRoot = document.getElementById('app');
const billYearSuffix = `/${new Date().getFullYear()}`;

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatSidebarDate() {
  return new Date().toLocaleString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
}

function formatCompactDate(value) {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
}

function formatCurrency(value) {
  return `Rs ${Number(value || 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function getInvoiceTotal(invoice) {
  return (invoice.products || []).reduce(
    (sum, item) => sum + Number(item.quantity || 0) * Number(item.unitPrice || 0),
    0
  );
}

function getInvoiceQuantity(invoice) {
  return (invoice.products || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0);
}

function getWeekStart(date) {
  const weekStart = new Date(date);
  weekStart.setHours(0, 0, 0, 0);
  const day = weekStart.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  weekStart.setDate(weekStart.getDate() + diff);
  return weekStart;
}

function renderLineChart(series, options = {}) {
  if (!series.length) {
    return '<div class="empty-state">Not enough dated sales activity yet.</div>';
  }

  const gradientKey = options.idPrefix || `analytics-line-${series.length}-${Math.round(series.reduce((sum, item) => sum + Number(item.value || 0), 0))}`;
  const width = options.width || 720;
  const height = options.height || 260;
  const paddingX = 24;
  const paddingTop = 20;
  const paddingBottom = 34;
  const plotHeight = height - paddingTop - paddingBottom;
  const values = series.map((item) => Number(item.value || 0));
  const maxValue = Math.max(...values, 1);
  const points = series.map((item, index) => {
    const x = series.length === 1
      ? width / 2
      : paddingX + (index * (width - paddingX * 2)) / (series.length - 1);
    const y = paddingTop + plotHeight - (Number(item.value || 0) / maxValue) * plotHeight;
    return { x, y, value: Number(item.value || 0), label: item.label, projected: Boolean(item.projected) };
  });
  const polylinePoints = points.map((point) => `${point.x},${point.y}`).join(' ');
  const areaPoints = `${paddingX},${height - paddingBottom} ${polylinePoints} ${width - paddingX},${height - paddingBottom}`;

  return `
    <div class="analytics-line-chart">
      <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" class="analytics-line-chart__svg">
        <defs>
          <linearGradient id="${gradientKey}-fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="${options.fillStart || '#3a7d93'}" stop-opacity="0.30"></stop>
            <stop offset="100%" stop-color="${options.fillEnd || '#3a7d93'}" stop-opacity="0.03"></stop>
          </linearGradient>
          <linearGradient id="${gradientKey}-stroke" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stop-color="${options.strokeStart || '#2f7a88'}"></stop>
            <stop offset="50%" stop-color="${options.strokeMid || '#d77a33'}"></stop>
            <stop offset="100%" stop-color="${options.strokeEnd || '#7c4dbe'}"></stop>
          </linearGradient>
        </defs>
        <line x1="${paddingX}" y1="${paddingTop}" x2="${width - paddingX}" y2="${paddingTop}" class="analytics-line-chart__grid"></line>
        <line x1="${paddingX}" y1="${paddingTop + plotHeight / 2}" x2="${width - paddingX}" y2="${paddingTop + plotHeight / 2}" class="analytics-line-chart__grid"></line>
        <line x1="${paddingX}" y1="${height - paddingBottom}" x2="${width - paddingX}" y2="${height - paddingBottom}" class="analytics-line-chart__grid"></line>
        <polygon points="${areaPoints}" fill="url(#${gradientKey}-fill)"></polygon>
        <polyline points="${polylinePoints}" fill="none" stroke="url(#${gradientKey}-stroke)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
        ${points.map((point) => `
          <g>
            <circle cx="${point.x}" cy="${point.y}" r="${point.projected ? 5 : 6}" class="analytics-line-chart__point${point.projected ? ' analytics-line-chart__point--projected' : ''}"></circle>
          </g>
        `).join('')}
      </svg>
      <div class="analytics-line-chart__labels">
        ${points.map((point) => `
          <div class="analytics-line-chart__label${point.projected ? ' analytics-line-chart__label--projected' : ''}">
            <span>${escapeHtml(point.label)}</span>
            <strong>${options.currency ? formatCurrency(point.value) : formatNumber(point.value)}</strong>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function getInvoiceEffectiveDate(invoice) {
  const raw = invoice.invoiceDate || invoice.createdAt || '';
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function getFilteredInventory() {
  const regNoQuery = state.inventoryFilters.regNo.trim().toLowerCase();
  const batchNoQuery = state.inventoryFilters.batchNo.trim().toLowerCase();
  const productQuery = state.inventoryFilters.productName.trim().toLowerCase();

  return state.inventory.filter((item) => {
    if (regNoQuery && !item.regNo.toLowerCase().includes(regNoQuery)) return false;
    if (batchNoQuery && !item.batchNo.toLowerCase().includes(batchNoQuery)) return false;
    if (productQuery && !item.productDescription.toLowerCase().includes(productQuery)) return false;
    return true;
  });
}

function getFilteredInvoices() {
  const billNoQuery = state.invoiceFilters.billNo.trim().toLowerCase();
  const toQuery = state.invoiceFilters.toText.trim().toLowerCase();
  const dateFrom = state.invoiceFilters.dateFrom;
  const dateTo = state.invoiceFilters.dateTo;

  return state.invoices.filter((invoice) => {
    const toFirstLine = (invoice.toText || '').split(/\r?\n/)[0].toLowerCase();
    if (billNoQuery && !String(invoice.billNo || '').toLowerCase().includes(billNoQuery)) return false;
    if (toQuery && !toFirstLine.includes(toQuery)) return false;

    const invoiceDate = invoice.invoiceDate || '';
    if (dateFrom && (!invoiceDate || invoiceDate < dateFrom)) return false;
    if (dateTo && (!invoiceDate || invoiceDate > dateTo)) return false;
    return true;
  });
}

function getFilteredOrders() {
  const institutionQuery = state.orderFilters.institutionName.trim().toLowerCase();
  const dateFrom = state.orderFilters.dateFrom;
  const dateTo = state.orderFilters.dateTo;

  return state.orders.filter((order) => {
    if (institutionQuery && !String(order.institutionName || '').toLowerCase().includes(institutionQuery)) return false;
    const orderDate = order.orderDate || '';
    if (dateFrom && (!orderDate || orderDate < dateFrom)) return false;
    if (dateTo && (!orderDate || orderDate > dateTo)) return false;
    return true;
  });
}

function getFilteredPayments() {
  const billNoQuery = state.paymentFilters.billNo.trim().toLowerCase();
  const invoiceDateQuery = state.paymentFilters.invoiceDate;
  const dateFrom = state.paymentFilters.dateFrom;
  const dateTo = state.paymentFilters.dateTo;

  return state.payments.filter((payment) => {
    if (billNoQuery && !String(payment.billNo || '').toLowerCase().includes(billNoQuery)) return false;
    const invoiceDate = payment.invoiceDate || '';
    if (invoiceDateQuery && invoiceDate !== invoiceDateQuery) return false;
    if (dateFrom && (!invoiceDate || invoiceDate < dateFrom)) return false;
    if (dateTo && (!invoiceDate || invoiceDate > dateTo)) return false;
    return true;
  });
}

function getSelectableProducts() {
  return state.inventory
    .filter((item) => item.quantity > 0)
    .map((item) => ({
      ...item,
      availableQty: item.quantity,
      unitPrice: Math.max(0, item.tradePrice * (1 - item.discountPercent / 100)),
    }));
}

function getInventoryAlerts() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const oneWeekFromNow = new Date(today);
  oneWeekFromNow.setDate(oneWeekFromNow.getDate() + 7);

  const alerts = [];

  for (const item of state.inventory) {
    const productName = item.productDescription || 'Unnamed product';

    if (Number(item.quantity || 0) < 10) {
      alerts.push({
        key: `stock-${item.id}`,
        severity: 'danger',
        productName,
        message: `Low stock: only ${formatNumber(item.quantity)} left in inventory.`,
      });
    }

    if (item.expDate) {
      const expiryDate = new Date(`${item.expDate}T00:00:00`);
      if (!Number.isNaN(expiryDate.getTime()) && expiryDate >= today && expiryDate <= oneWeekFromNow) {
        const daysLeft = Math.max(0, Math.ceil((expiryDate.getTime() - today.getTime()) / 86400000));
        alerts.push({
          key: `expiry-${item.id}`,
          severity: daysLeft <= 3 ? 'danger' : 'warning',
          productName,
          message: daysLeft === 0
            ? `Expires today (${item.expDate}).`
            : `Expires in ${daysLeft} day${daysLeft === 1 ? '' : 's'} (${item.expDate}).`,
        });
      }
    }
  }

  return alerts;
}

function renderInventoryAlerts() {
  const alerts = getInventoryAlerts();

  return `
    <div class="inventory-alert-stack">
      ${alerts
        .map(
          (alert) => `
            <div class="inventory-alert inventory-alert--${alert.severity}" data-alert-key="${escapeHtml(alert.key)}">
              <div class="inventory-alert__eyebrow">Inventory Alert</div>
              <div class="inventory-alert__title">${escapeHtml(alert.productName)}</div>
              <div class="inventory-alert__message">${escapeHtml(alert.message)}</div>
            </div>
          `
        )
        .join('')}
    </div>
  `;
}

function renderTable(columns, rows, emptyText) {
  if (!rows.length) {
    return `<div class="empty-state">${escapeHtml(emptyText)}</div>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            ${columns
              .map((column) => `<th class="${column.numeric ? 'numeric' : ''}">${escapeHtml(column.label)}</th>`)
              .join('')}
          </tr>
        </thead>
        <tbody>${rows.join('')}</tbody>
      </table>
    </div>
  `;
}

function renderLogin() {
  appRoot.innerHTML = `
    <div class="screen login-screen">
      <form class="login-card" id="login-form">
        <img class="login-logo" src="../assets/logo.png" alt="United Agencies karachi logo" />
        <p class="login-subtitle">Sign in to continue</p>
        <div class="field-stack">
          <label for="username">Username</label>
          <input id="username" name="username" value="admin" autocomplete="username" />
        </div>
        <div class="field-stack">
          <label for="password">Password</label>
          <input id="password" name="password" type="password" autocomplete="current-password" />
        </div>
        <div class="error-text" id="login-error"></div>
        <button class="btn primary" type="submit">Sign In</button>
      </form>
    </div>
  `;

  document.getElementById('login-form').addEventListener('submit', onLoginSubmit);
  document.getElementById('password').focus();
}

function renderInvoicesView() {
  const rows = getFilteredInvoices().map((invoice) => {
    const toFirstLine = invoice.toText.split(/\r?\n/)[0] || '';
    return `
      <tr>
        <td>${escapeHtml(invoice.fileNo)}</td>
        <td>${escapeHtml(invoice.billNo)}</td>
        <td>${escapeHtml(invoice.deliveryChallanNo)}</td>
        <td>${escapeHtml(invoice.orderContractNo)}</td>
        <td>${escapeHtml(toFirstLine)}</td>
        <td>${escapeHtml(invoice.orderDate)}</td>
        <td>${escapeHtml(invoice.inspectionNoteNo)}</td>
        <td><button class="btn secondary" data-action="generate-invoice-pdf" data-invoice-id="${invoice.id}">Generate Invoice</button></td>
      </tr>
    `;
  });

  return `
    <div class="panel">
      <div class="panel-head">
        <div class="button-row">
          <button class="btn primary" data-action="open-invoice-modal">Create Invoice</button>
        </div>
      </div>
      <div class="panel-body">
        <div class="filters">
          <div class="field">
            <label for="filter-invoice-bill-no">Bill No</label>
            <input id="filter-invoice-bill-no" value="${escapeHtml(state.invoiceFilters.billNo)}" />
          </div>
          <div class="field">
            <label for="filter-invoice-to">To</label>
            <input id="filter-invoice-to" value="${escapeHtml(state.invoiceFilters.toText)}" />
          </div>
          <div class="field">
            <label for="filter-invoice-date-from">Date From</label>
            <input id="filter-invoice-date-from" type="date" value="${escapeHtml(state.invoiceFilters.dateFrom)}" />
          </div>
          <div class="field">
            <label for="filter-invoice-date-to">Date To</label>
            <input id="filter-invoice-date-to" type="date" value="${escapeHtml(state.invoiceFilters.dateTo)}" />
          </div>
          <div class="button-row filter-actions">
            <button class="btn secondary" data-action="search-invoices">Search</button>
            <button class="btn secondary" data-action="clear-invoices">Clear</button>
          </div>
        </div>
        ${renderTable(
          [
            { label: 'File No' },
            { label: 'Bill No' },
            { label: 'Delivery Challan No' },
            { label: 'Your Order/Contract No' },
            { label: 'To' },
            { label: 'Your Order Date' },
            { label: 'Inspection Note No' },
            { label: 'Action' },
          ],
          rows,
          'No invoices found yet.'
        )}
      </div>
    </div>
  `;
}

function renderOrdersView() {
  const rows = getFilteredOrders().map((order) => `
    <tr>
      <td>${escapeHtml(order.institutionName)}</td>
      <td>${escapeHtml(order.orderNumber)}</td>
      <td>${escapeHtml(order.orderDate)}</td>
      <td>${escapeHtml(order.fileName)}</td>
      <td><button class="btn secondary" data-action="open-order-file" data-order-file-path="${escapeHtml(order.filePath)}">Open File</button></td>
    </tr>
  `);

  return `
    <div class="panel">
      <div class="panel-head">
        <div class="button-row">
          <button class="btn primary" data-action="open-order-modal">Add Order</button>
        </div>
      </div>
      <div class="panel-body">
        <div class="filters">
          <div class="field">
            <label for="filter-order-institution-name">Institution Name</label>
            <input id="filter-order-institution-name" value="${escapeHtml(state.orderFilters.institutionName)}" />
          </div>
          <div class="field">
            <label for="filter-order-date-from">Date From</label>
            <input id="filter-order-date-from" type="date" value="${escapeHtml(state.orderFilters.dateFrom)}" />
          </div>
          <div class="field">
            <label for="filter-order-date-to">Date To</label>
            <input id="filter-order-date-to" type="date" value="${escapeHtml(state.orderFilters.dateTo)}" />
          </div>
          <div class="button-row filter-actions">
            <button class="btn secondary" data-action="search-orders">Search</button>
            <button class="btn secondary" data-action="clear-orders">Clear</button>
          </div>
        </div>
        ${renderTable(
          [
            { label: 'Institution Name' },
            { label: 'Order Number' },
            { label: 'Order Date' },
            { label: 'File' },
            { label: 'Action' },
          ],
          rows,
          'No orders saved yet.'
        )}
      </div>
    </div>
  `;
}

function renderPaymentsView() {
  const rows = getFilteredPayments().map((payment) => `
    <tr>
      <td>${escapeHtml(payment.billNo)}</td>
      <td>${escapeHtml(payment.institutionName)}</td>
      <td>${escapeHtml(payment.invoiceDate)}</td>
      <td>
        <select
          class="payment-status payment-status--${escapeHtml(payment.status)}"
          data-payment-status-select="${payment.id}"
        >
          <option value="pending" ${payment.status === 'pending' ? 'selected' : ''}>Pending</option>
          <option value="received" ${payment.status === 'received' ? 'selected' : ''}>Received</option>
        </select>
      </td>
    </tr>
  `);

    return `
      <div class="panel">
        <div class="panel-head"></div>
        <div class="panel-body">
          <div class="filters">
            <div class="field">
              <label for="filter-payment-bill-no">Bill No</label>
              <input id="filter-payment-bill-no" value="${escapeHtml(state.paymentFilters.billNo)}" />
            </div>
            <div class="field">
              <label for="filter-payment-invoice-date">Invoice Date</label>
              <input id="filter-payment-invoice-date" type="date" value="${escapeHtml(state.paymentFilters.invoiceDate)}" />
            </div>
            <div class="field">
              <label for="filter-payment-date-from">From Date</label>
              <input id="filter-payment-date-from" type="date" value="${escapeHtml(state.paymentFilters.dateFrom)}" />
            </div>
            <div class="field">
              <label for="filter-payment-date-to">To Date</label>
              <input id="filter-payment-date-to" type="date" value="${escapeHtml(state.paymentFilters.dateTo)}" />
            </div>
            <div class="button-row filter-actions">
              <button class="btn secondary" data-action="search-payments">Search</button>
              <button class="btn secondary" data-action="clear-payments">Clear</button>
            </div>
          </div>
          ${renderTable(
            [
              { label: 'Bill No' },
            { label: 'Institution Name' },
            { label: 'Invoice Date' },
            { label: 'Status' },
          ],
          rows,
          'No payments available yet.'
        )}
      </div>
    </div>
  `;
}

function getSalesReportData() {
  const invoices = [...state.invoices]
    .map((invoice) => ({
      ...invoice,
      effectiveDate: getInvoiceEffectiveDate(invoice),
      customerName: (invoice.toText || '').split(/\r?\n/)[0] || 'Walk-in',
    }))
    .filter((invoice) => invoice.effectiveDate);

  const totalInvoices = invoices.length;
  const totalQty = invoices.reduce((sum, invoice) => sum + Number(invoice.totalQty || 0), 0);
  const averageQty = totalInvoices ? totalQty / totalInvoices : 0;

  const dailyMap = new Map();
  for (const invoice of invoices) {
    const key = invoice.effectiveDate.toISOString().slice(0, 10);
    if (!dailyMap.has(key)) {
      dailyMap.set(key, { key, label: formatCompactDate(key), qty: 0, count: 0 });
    }
    const current = dailyMap.get(key);
    current.qty += Number(invoice.totalQty || 0);
    current.count += 1;
  }
  const dailyTrend = [...dailyMap.values()].sort((a, b) => a.key.localeCompare(b.key)).slice(-7);

  const monthlyMap = new Map();
  for (const invoice of invoices) {
    const key = invoice.effectiveDate.toISOString().slice(0, 7);
    if (!monthlyMap.has(key)) {
      monthlyMap.set(key, { key, label: invoice.effectiveDate.toLocaleDateString(undefined, { month: 'short', year: '2-digit' }), qty: 0 });
    }
    monthlyMap.get(key).qty += Number(invoice.totalQty || 0);
  }
  const monthlyTrend = [...monthlyMap.values()].sort((a, b) => a.key.localeCompare(b.key)).slice(-6);

  const customerMap = new Map();
  for (const invoice of invoices) {
    if (!customerMap.has(invoice.customerName)) {
      customerMap.set(invoice.customerName, { name: invoice.customerName, qty: 0, count: 0 });
    }
    const current = customerMap.get(invoice.customerName);
    current.qty += Number(invoice.totalQty || 0);
    current.count += 1;
  }
  const topCustomers = [...customerMap.values()].sort((a, b) => b.qty - a.qty).slice(0, 5);

  const recentSales = invoices
    .sort((a, b) => b.effectiveDate.getTime() - a.effectiveDate.getTime())
    .slice(0, 6);

  return {
    totalInvoices,
    totalQty,
    averageQty,
    topDayQty: dailyTrend.reduce((max, item) => Math.max(max, item.qty), 0),
    topMonthQty: monthlyTrend.reduce((max, item) => Math.max(max, item.qty), 0),
    topCustomerQty: topCustomers.reduce((max, item) => Math.max(max, item.qty), 0),
    dailyTrend,
    monthlyTrend,
    topCustomers,
    recentSales,
  };
}

function getDataAnalytics() {
  const invoices = state.invoices.map((invoice) => ({
    ...invoice,
    effectiveDate: getInvoiceEffectiveDate(invoice),
    institutionName: (invoice.toText || '').split(/\r?\n/)[0] || 'Walk-in',
    totalAmount: getInvoiceTotal(invoice),
    totalQty: getInvoiceQuantity(invoice),
  }));
  const datedInvoices = invoices.filter((invoice) => invoice.effectiveDate);
  const payments = state.payments;
  const orders = state.orders;
  const inventory = state.inventory;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(today.getDate() - 30);
  const thirtyDaysAhead = new Date(today);
  thirtyDaysAhead.setDate(today.getDate() + 30);

  const pendingPayments = payments.filter((payment) => payment.status === 'pending');
  const receivedPayments = payments.filter((payment) => payment.status === 'received');
  const lowStockItems = inventory.filter((item) => Number(item.quantity || 0) < 10);
  const expiringSoonItems = inventory.filter((item) => {
    if (!item.expDate) return false;
    const exp = new Date(`${item.expDate}T00:00:00`);
    return !Number.isNaN(exp.getTime()) && exp >= today && exp <= thirtyDaysAhead;
  });
  const overduePayments = pendingPayments.filter((payment) => {
    if (!payment.invoiceDate) return false;
    const invoiceDate = new Date(`${payment.invoiceDate}T00:00:00`);
    return !Number.isNaN(invoiceDate.getTime()) && invoiceDate < thirtyDaysAgo;
  });
  const activeInstitutions = new Set(
    invoices
      .map((invoice) => invoice.institutionName)
      .filter(Boolean)
  );
  const orderInstitutions = new Set(
    orders
      .map((order) => order.institutionName)
      .filter(Boolean)
  );
  const coveredInstitutions = [...activeInstitutions].filter((name) => orderInstitutions.has(name));
  const recentInvoices = datedInvoices.filter((invoice) => invoice.effectiveDate >= thirtyDaysAgo);
  const totalSales = invoices.reduce((sum, invoice) => sum + invoice.totalAmount, 0);
  const salesLast30Days = recentInvoices.reduce((sum, invoice) => sum + invoice.totalAmount, 0);
  const quantityLast30Days = recentInvoices.reduce((sum, invoice) => sum + invoice.totalQty, 0);
  const invoiceTotalsByBill = new Map(invoices.map((invoice) => [String(invoice.billNo || ''), invoice.totalAmount]));
  const pendingReceivablesValue = pendingPayments.reduce(
    (sum, payment) => sum + Number(invoiceTotalsByBill.get(String(payment.billNo || '')) || 0),
    0
  );
  const receivedReceivablesValue = receivedPayments.reduce(
    (sum, payment) => sum + Number(invoiceTotalsByBill.get(String(payment.billNo || '')) || 0),
    0
  );
  const stockOnHandUnits = inventory.reduce((sum, item) => sum + Number(item.quantity || 0), 0);

  const invoiceDailyMap = new Map();
  for (const invoice of datedInvoices) {
    const key = invoice.effectiveDate.toISOString().slice(0, 10);
    if (!invoiceDailyMap.has(key)) {
      invoiceDailyMap.set(key, { key, label: formatCompactDate(key), count: 0 });
    }
    invoiceDailyMap.get(key).count += 1;
  }
  const invoiceTrend = [...invoiceDailyMap.values()].sort((a, b) => a.key.localeCompare(b.key)).slice(-7);

  const salesMomentum = [];
  for (let offset = 13; offset >= 0; offset -= 1) {
    const day = new Date(today);
    day.setDate(today.getDate() - offset);
    const key = day.toISOString().slice(0, 10);
    const dayInvoices = datedInvoices.filter((invoice) => invoice.effectiveDate.toISOString().slice(0, 10) === key);
    salesMomentum.push({
      key,
      label: day.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      value: dayInvoices.reduce((sum, invoice) => sum + invoice.totalAmount, 0),
    });
  }

  const productSalesMap = new Map();
  for (const invoice of invoices) {
    for (const product of invoice.products || []) {
      const key = product.productDescription || 'Unnamed product';
      if (!productSalesMap.has(key)) {
        productSalesMap.set(key, {
          name: key,
          qty: 0,
          revenue: 0,
        });
      }
      const entry = productSalesMap.get(key);
      entry.qty += Number(product.quantity || 0);
      entry.revenue += Number(product.quantity || 0) * Number(product.unitPrice || 0);
    }
  }
  const productSalesRows = [...productSalesMap.values()]
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 6);

  const weekMap = new Map();
  for (const invoice of datedInvoices) {
    const weekStart = getWeekStart(invoice.effectiveDate);
    const key = weekStart.toISOString().slice(0, 10);
    if (!weekMap.has(key)) {
      weekMap.set(key, { key, value: 0 });
    }
    weekMap.get(key).value += invoice.totalAmount;
  }

  const weeklySeries = [];
  for (let offset = 5; offset >= 0; offset -= 1) {
    const baseWeek = getWeekStart(today);
    baseWeek.setDate(baseWeek.getDate() - offset * 7);
    const key = baseWeek.toISOString().slice(0, 10);
    weeklySeries.push({
      key,
      label: baseWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      value: Number(weekMap.get(key)?.value || 0),
      projected: false,
    });
  }

  const recentWeeklyValues = weeklySeries.map((item) => item.value);
  const recentDiffs = [];
  for (let index = 1; index < recentWeeklyValues.length; index += 1) {
    recentDiffs.push(recentWeeklyValues[index] - recentWeeklyValues[index - 1]);
  }
  const averageWeeklyDelta = recentDiffs.length
    ? recentDiffs.reduce((sum, value) => sum + value, 0) / recentDiffs.length
    : 0;
  const rollingBase = recentWeeklyValues.slice(-3).reduce((sum, value) => sum + value, 0) / Math.max(1, recentWeeklyValues.slice(-3).length);
  const salesForecastSeries = [...weeklySeries];
  for (let step = 1; step <= 4; step += 1) {
    const projectedWeek = getWeekStart(today);
    projectedWeek.setDate(projectedWeek.getDate() + step * 7);
    salesForecastSeries.push({
      key: projectedWeek.toISOString().slice(0, 10),
      label: projectedWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      value: Math.max(0, rollingBase + averageWeeklyDelta * step),
      projected: true,
    });
  }

  const institutionMap = new Map();
  for (const invoice of invoices) {
    const name = invoice.institutionName || 'Walk-in';
    if (!institutionMap.has(name)) {
      institutionMap.set(name, { name, invoices: 0, orders: 0, sales: 0 });
    }
    const entry = institutionMap.get(name);
    entry.invoices += 1;
    entry.sales += invoice.totalAmount;
  }
  for (const order of orders) {
    const name = order.institutionName || 'Unknown';
    if (!institutionMap.has(name)) {
      institutionMap.set(name, { name, invoices: 0, orders: 0, sales: 0 });
    }
    institutionMap.get(name).orders += 1;
  }
  const topInstitutions = [...institutionMap.values()]
    .map((entry) => ({ ...entry, total: entry.sales || entry.invoices + entry.orders }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 5);

  const inventoryRows = inventory
    .slice()
    .sort((a, b) => {
      const aQty = Number(a.quantity || 0);
      const bQty = Number(b.quantity || 0);
      const aExp = a.expDate || '9999-99-99';
      const bExp = b.expDate || '9999-99-99';
      if (aQty !== bQty) return aQty - bQty;
      return aExp.localeCompare(bExp);
    })
    .slice(0, 6);

  const paymentAgingRows = pendingPayments
    .map((payment) => {
      const invoiceDate = payment.invoiceDate ? new Date(`${payment.invoiceDate}T00:00:00`) : null;
      const ageDays = invoiceDate && !Number.isNaN(invoiceDate.getTime())
        ? Math.max(0, Math.floor((today.getTime() - invoiceDate.getTime()) / 86400000))
        : 0;
      return {
        ...payment,
        ageDays,
      };
    })
    .sort((a, b) => b.ageDays - a.ageDays)
    .slice(0, 5);

  return {
    totalInvoices: invoices.length,
    totalOrders: orders.length,
    totalPayments: payments.length,
    pendingPayments: pendingPayments.length,
    receivedPayments: receivedPayments.length,
    lowStockCount: lowStockItems.length,
    expiringSoonCount: expiringSoonItems.length,
    overduePaymentsCount: overduePayments.length,
    activeInstitutionCount: activeInstitutions.size,
    orderCoverageRate: activeInstitutions.size ? (coveredInstitutions.length / activeInstitutions.size) * 100 : 0,
    paymentReceivedRate: payments.length ? (receivedPayments.length / payments.length) * 100 : 0,
    invoiceVelocity: recentInvoices.length / 30,
    totalSales,
    salesLast30Days,
    quantityLast30Days,
    averageInvoiceValue: invoices.length ? totalSales / invoices.length : 0,
    pendingReceivablesValue,
    receivedReceivablesValue,
    stockOnHandUnits,
    stockTurnRate: stockOnHandUnits ? (quantityLast30Days / stockOnHandUnits) * 100 : 0,
    invoiceTrend,
    topInvoiceDay: invoiceTrend.reduce((max, item) => Math.max(max, item.count), 0),
    salesMomentum,
    salesForecastSeries,
    productSalesRows,
    topProductRevenue: productSalesRows.reduce((max, item) => Math.max(max, item.revenue), 0),
    topInstitutions,
    topInstitutionTotal: topInstitutions.reduce((max, item) => Math.max(max, item.total), 0),
    inventoryRows,
    paymentAgingRows,
  };
}

function renderSalesReportsView() {
  const report = getSalesReportData();

  const dailyBars = report.dailyTrend.length
    ? report.dailyTrend.map((item) => `
        <div class="chart-bar-card">
          <div class="chart-bar-card__value">${formatNumber(item.qty)}</div>
          <div class="chart-bar-card__track">
            <div class="chart-bar-card__fill" style="height: ${report.topDayQty ? Math.max(10, (item.qty / report.topDayQty) * 100) : 10}%"></div>
          </div>
          <div class="chart-bar-card__label">${escapeHtml(item.label)}</div>
          <div class="chart-bar-card__meta">${item.count} invoice${item.count === 1 ? '' : 's'}</div>
        </div>
      `).join('')
    : '<div class="empty-state">No invoice data yet for daily sales.</div>';

  const monthlyBars = report.monthlyTrend.length
    ? report.monthlyTrend.map((item) => `
        <div class="mini-bar-row">
          <div class="mini-bar-row__label">${escapeHtml(item.label)}</div>
          <div class="mini-bar-row__track"><div class="mini-bar-row__fill" style="width: ${report.topMonthQty ? Math.max(8, (item.qty / report.topMonthQty) * 100) : 8}%"></div></div>
          <div class="mini-bar-row__value">${formatNumber(item.qty)}</div>
        </div>
      `).join('')
    : '<div class="empty-state">No monthly sales yet.</div>';

  const customerRows = report.topCustomers.length
    ? report.topCustomers.map((customer) => `
        <div class="mini-bar-row">
          <div class="mini-bar-row__label">${escapeHtml(customer.name)}</div>
          <div class="mini-bar-row__track mini-bar-row__track--customer"><div class="mini-bar-row__fill mini-bar-row__fill--customer" style="width: ${report.topCustomerQty ? Math.max(8, (customer.qty / report.topCustomerQty) * 100) : 8}%"></div></div>
          <div class="mini-bar-row__value">${formatNumber(customer.qty)}</div>
        </div>
      `).join('')
    : '<div class="empty-state">No customer sales yet.</div>';

  const recentRows = report.recentSales.map((sale) => `
    <tr>
      <td>${escapeHtml(sale.billNo)}</td>
      <td>${escapeHtml(sale.customerName)}</td>
      <td>${escapeHtml(sale.invoiceDate || formatCompactDate(sale.createdAt))}</td>
      <td class="numeric">${formatNumber(sale.totalQty)}</td>
    </tr>
  `);

  return `
    <div class="reports-layout">
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-card__label">Total Invoices</div>
          <div class="metric-card__value">${report.totalInvoices}</div>
        </div>
        <div class="metric-card">
          <div class="metric-card__label">Total Qty Sold</div>
          <div class="metric-card__value">${formatNumber(report.totalQty)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-card__label">Average Qty / Invoice</div>
          <div class="metric-card__value">${formatNumber(report.averageQty)}</div>
        </div>
      </div>

      <div class="reports-grid">
        <section class="panel report-panel">
          <div class="panel-head">
            <div class="report-panel__title">Last 7 Sales Days</div>
          </div>
          <div class="panel-body">
            <div class="chart-bar-grid">${dailyBars}</div>
          </div>
        </section>

        <section class="panel report-panel">
          <div class="panel-head">
            <div class="report-panel__title">Monthly Sales Qty</div>
          </div>
          <div class="panel-body">
            <div class="mini-bar-list">${monthlyBars}</div>
          </div>
        </section>

        <section class="panel report-panel">
          <div class="panel-head">
            <div class="report-panel__title">Top Customers</div>
          </div>
          <div class="panel-body">
            <div class="mini-bar-list">${customerRows}</div>
          </div>
        </section>

        <section class="panel report-panel">
          <div class="panel-head">
            <div class="report-panel__title">Recent Sales</div>
          </div>
          <div class="panel-body">
            ${renderTable(
              [
                { label: 'Bill No' },
                { label: 'Customer' },
                { label: 'Date' },
                { label: 'Qty', numeric: true },
              ],
              recentRows,
              'No sales available yet.'
            )}
          </div>
        </section>
      </div>
    </div>
  `;
}

function renderDataAnalyticsView() {
  const analytics = getDataAnalytics();

  const invoiceTrendCards = analytics.invoiceTrend.length
    ? analytics.invoiceTrend.map((item) => `
        <div class="analytics-day-card">
          <div class="analytics-day-card__value">${item.count}</div>
          <div class="analytics-day-card__track">
            <div class="analytics-day-card__fill" style="height: ${analytics.topInvoiceDay ? Math.max(10, (item.count / analytics.topInvoiceDay) * 100) : 10}%"></div>
          </div>
          <div class="analytics-day-card__label">${escapeHtml(item.label)}</div>
        </div>
      `).join('')
    : '<div class="empty-state">No dated invoice activity yet.</div>';

  const institutionRows = analytics.topInstitutions.length
    ? analytics.topInstitutions.map((institution) => `
        <div class="analytics-rank-row">
          <div class="analytics-rank-row__identity">
            <div class="analytics-rank-row__title">${escapeHtml(institution.name)}</div>
            <div class="analytics-rank-row__meta">${institution.invoices} invoices · ${institution.orders} orders</div>
          </div>
          <div class="analytics-rank-row__track">
            <div class="analytics-rank-row__fill" style="width: ${analytics.topInstitutionTotal ? Math.max(8, (institution.total / analytics.topInstitutionTotal) * 100) : 8}%"></div>
          </div>
          <div class="analytics-rank-row__value">${institution.total}</div>
        </div>
      `).join('')
    : '<div class="empty-state">No institution activity yet.</div>';

  const inventoryTableRows = analytics.inventoryRows.map((item) => `
    <tr>
      <td>${escapeHtml(item.productDescription)}</td>
      <td>${escapeHtml(item.regNo)}</td>
      <td class="numeric">${formatNumber(item.quantity)}</td>
      <td>${escapeHtml(item.expDate)}</td>
    </tr>
  `);

  const paymentAgingRows = analytics.paymentAgingRows.map((payment) => `
    <tr>
      <td>${escapeHtml(payment.billNo)}</td>
      <td>${escapeHtml(payment.institutionName)}</td>
      <td>${escapeHtml(payment.invoiceDate)}</td>
      <td class="numeric">${payment.ageDays}</td>
    </tr>
  `);

  return `
    <div class="analytics-dashboard">
      <section class="analytics-hero">
        <div class="analytics-hero__copy">
          <div class="analytics-hero__eyebrow">Portfolio Health</div>
          <h2 class="analytics-hero__title">Operational analytics for invoices, payments, orders, and inventory</h2>
          <p class="analytics-hero__summary">
            ${analytics.totalInvoices} invoices across ${analytics.activeInstitutionCount} institutions, with
            ${analytics.pendingPayments} pending payments and ${analytics.lowStockCount} low-stock items requiring attention.
          </p>
        </div>
        <div class="analytics-hero__scorecard">
          <div class="analytics-scorecard__label">Collection Efficiency</div>
          <div class="analytics-scorecard__value">${formatNumber(analytics.paymentReceivedRate)}%</div>
          <div class="analytics-scorecard__subtext">
            Order Coverage ${formatNumber(analytics.orderCoverageRate)}% · ${analytics.overduePaymentsCount} overdue pending payments
          </div>
        </div>
      </section>

      <div class="analytics-kpi-grid">
        <article class="analytics-kpi analytics-kpi--warm">
          <div class="analytics-kpi__label">Invoice Velocity</div>
          <div class="analytics-kpi__value">${formatNumber(analytics.invoiceVelocity)}</div>
          <div class="analytics-kpi__meta">avg invoices per day over last 30 days</div>
        </article>
        <article class="analytics-kpi analytics-kpi--cool">
          <div class="analytics-kpi__label">Pending Payments</div>
          <div class="analytics-kpi__value">${analytics.pendingPayments}</div>
          <div class="analytics-kpi__meta">${analytics.receivedPayments} received · ${analytics.totalPayments} total tracked</div>
        </article>
        <article class="analytics-kpi analytics-kpi--danger">
          <div class="analytics-kpi__label">Inventory Risk</div>
          <div class="analytics-kpi__value">${analytics.lowStockCount + analytics.expiringSoonCount}</div>
          <div class="analytics-kpi__meta">${analytics.lowStockCount} low stock · ${analytics.expiringSoonCount} expiring within 30 days</div>
        </article>
        <article class="analytics-kpi analytics-kpi--neutral">
          <div class="analytics-kpi__label">Institution Reach</div>
          <div class="analytics-kpi__value">${analytics.activeInstitutionCount}</div>
          <div class="analytics-kpi__meta">${analytics.totalOrders} orders logged · ${formatNumber(analytics.orderCoverageRate)}% covered</div>
        </article>
      </div>

      <div class="analytics-grid">
        <section class="analytics-panel analytics-panel--feature">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Momentum</div>
              <div class="analytics-panel__title">7-Day Invoice Activity</div>
            </div>
            <div class="analytics-panel__badge">${analytics.totalInvoices} total invoices</div>
          </div>
          <div class="analytics-panel__body">
            <div class="analytics-day-grid">${invoiceTrendCards}</div>
          </div>
        </section>

        <section class="analytics-panel analytics-panel--glass">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Cash Flow</div>
              <div class="analytics-panel__title">Payment Collection Snapshot</div>
            </div>
          </div>
          <div class="analytics-panel__body">
            <div class="analytics-split-metrics">
              <div class="analytics-split-metric">
                <div class="analytics-split-metric__label">Pending</div>
                <div class="analytics-split-metric__value">${analytics.pendingPayments}</div>
                <div class="analytics-split-metric__track">
                  <div class="analytics-split-metric__fill analytics-split-metric__fill--danger" style="width: ${analytics.totalPayments ? Math.max(8, (analytics.pendingPayments / analytics.totalPayments) * 100) : 8}%"></div>
                </div>
              </div>
              <div class="analytics-split-metric">
                <div class="analytics-split-metric__label">Received</div>
                <div class="analytics-split-metric__value">${analytics.receivedPayments}</div>
                <div class="analytics-split-metric__track">
                  <div class="analytics-split-metric__fill analytics-split-metric__fill--success" style="width: ${analytics.totalPayments ? Math.max(8, (analytics.receivedPayments / analytics.totalPayments) * 100) : 8}%"></div>
                </div>
              </div>
              <div class="analytics-callout-row">
                <div class="analytics-callout">
                  <div class="analytics-callout__label">Overdue Pending</div>
                  <div class="analytics-callout__value">${analytics.overduePaymentsCount}</div>
                </div>
                <div class="analytics-callout">
                  <div class="analytics-callout__label">Collection Rate</div>
                  <div class="analytics-callout__value">${formatNumber(analytics.paymentReceivedRate)}%</div>
                </div>
              </div>
            </div>
            ${renderTable(
              [
                { label: 'Bill No' },
                { label: 'Institution' },
                { label: 'Invoice Date' },
                { label: 'Age (Days)', numeric: true },
              ],
              paymentAgingRows,
              'No pending payments to age right now.'
            )}
          </div>
        </section>

        <section class="analytics-panel">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Institution Performance</div>
              <div class="analytics-panel__title">Top Institutions</div>
            </div>
            <div class="analytics-panel__badge">${analytics.activeInstitutionCount} active</div>
          </div>
          <div class="analytics-panel__body">
            <div class="analytics-rank-list">${institutionRows}</div>
          </div>
        </section>

        <section class="analytics-panel">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Inventory Control</div>
              <div class="analytics-panel__title">Inventory Watchlist</div>
            </div>
            <div class="analytics-panel__badge">${analytics.lowStockCount} low stock · ${analytics.expiringSoonCount} expiring soon</div>
          </div>
          <div class="analytics-panel__body">
            ${renderTable(
              [
                { label: 'Product' },
                { label: 'Reg No' },
                { label: 'Qty', numeric: true },
                { label: 'Expiry' },
              ],
              inventoryTableRows,
              'No inventory records available yet.'
            )}
          </div>
        </section>
      </div>
    </div>
  `;
}

function renderInventoryView() {
  const rows = getFilteredInventory().map((item) => `
    <tr class="${state.selectedInventoryId === item.id ? 'selected' : ''}" data-inventory-row="${item.id}">
      <td>${escapeHtml(item.regNo)}</td>
      <td>${escapeHtml(item.batchNo)}</td>
      <td>${escapeHtml(item.mfgDate)}</td>
      <td>${escapeHtml(item.expDate)}</td>
      <td class="numeric">${formatNumber(item.quantity)}</td>
      <td>${escapeHtml(item.productDescription)}</td>
      <td class="numeric">${formatNumber(item.tradePrice)}</td>
      <td class="numeric">${formatNumber(item.discountPercent)}</td>
    </tr>
  `);

  return `
    <div class="panel">
      <div class="panel-head">
        <div class="button-row">
          <button class="btn secondary" data-action="edit-product">Edit Product</button>
          <button class="btn primary" data-action="add-product">Add Product</button>
        </div>
      </div>
      <div class="panel-body">
        <div class="filters">
          <div class="field">
            <label for="filter-reg-no">Reg No</label>
            <input id="filter-reg-no" value="${escapeHtml(state.inventoryFilters.regNo)}" />
          </div>
          <div class="field">
            <label for="filter-batch-no">Batch No</label>
            <input id="filter-batch-no" value="${escapeHtml(state.inventoryFilters.batchNo)}" />
          </div>
          <div class="field">
            <label for="filter-product-name">Product Name</label>
            <input id="filter-product-name" value="${escapeHtml(state.inventoryFilters.productName)}" />
          </div>
          <div class="button-row">
            <button class="btn secondary" data-action="search-inventory">Search</button>
            <button class="btn secondary" data-action="clear-inventory">Clear</button>
          </div>
        </div>
        ${renderTable(
          [
            { label: 'Reg No' },
            { label: 'Batch No' },
            { label: 'Mfg Date' },
            { label: 'Exp Date' },
            { label: 'Qty', numeric: true },
            { label: 'Description' },
            { label: 'Trade Price', numeric: true },
            { label: 'Discount %', numeric: true },
          ],
          rows,
          'No inventory items match the current filters.'
        )}
      </div>
    </div>
  `;
}

function renderDataAnalyticsView() {
  const analytics = getDataAnalytics();

  const institutionRows = analytics.topInstitutions.length
    ? analytics.topInstitutions.map((institution) => `
        <div class="analytics-rank-row">
          <div class="analytics-rank-row__identity">
            <div class="analytics-rank-row__title">${escapeHtml(institution.name)}</div>
            <div class="analytics-rank-row__meta">${institution.invoices} invoices · ${institution.orders} orders</div>
          </div>
          <div class="analytics-rank-row__track">
            <div class="analytics-rank-row__fill" style="width: ${analytics.topInstitutionTotal ? Math.max(8, (institution.total / analytics.topInstitutionTotal) * 100) : 8}%"></div>
          </div>
          <div class="analytics-rank-row__value">${formatCurrency(institution.sales)}</div>
        </div>
      `).join('')
    : '<div class="empty-state">No institution activity yet.</div>';

  const paymentAgingRows = analytics.paymentAgingRows.map((payment) => `
    <tr>
      <td>${escapeHtml(payment.billNo)}</td>
      <td>${escapeHtml(payment.institutionName)}</td>
      <td>${escapeHtml(payment.invoiceDate)}</td>
      <td class="numeric">${payment.ageDays}</td>
    </tr>
  `);

  const inventoryPriorityRows = analytics.inventoryRows.map((item) => `
    <tr>
      <td>${escapeHtml(item.productDescription)}</td>
      <td class="numeric">${formatNumber(item.quantity)}</td>
      <td>${escapeHtml(item.expDate || '-')}</td>
      <td>${Number(item.quantity || 0) < 10 ? 'Low stock' : 'Monitor'}</td>
    </tr>
  `);

  const productSalesRows = analytics.productSalesRows.length
    ? analytics.productSalesRows.map((product, index) => `
        <div class="analytics-product-row">
          <div class="analytics-product-row__header">
            <div class="analytics-product-row__name">${escapeHtml(product.name)}</div>
            <div class="analytics-product-row__value">${formatCurrency(product.revenue)}</div>
          </div>
          <div class="analytics-product-row__track">
            <div class="analytics-product-row__fill analytics-product-row__fill--${index % 5}" style="width: ${analytics.topProductRevenue ? Math.max(10, (product.revenue / analytics.topProductRevenue) * 100) : 10}%"></div>
          </div>
          <div class="analytics-product-row__meta">${formatNumber(product.qty)} units billed</div>
        </div>
      `).join('')
    : '<div class="empty-state">No billed products yet.</div>';

  return `
    <div class="analytics-dashboard">
      <div class="analytics-priority-grid">
        <section class="analytics-panel analytics-panel--priority">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Inventory Control</div>
              <div class="analytics-panel__title">Stock Exceptions</div>
            </div>
            <div class="analytics-panel__badge">${analytics.lowStockCount} low stock · ${analytics.expiringSoonCount} expiring soon</div>
          </div>
          <div class="analytics-panel__body">
            <div class="analytics-callout-row">
              <div class="analytics-callout">
                <div class="analytics-callout__label">Units On Hand</div>
                <div class="analytics-callout__value">${formatNumber(analytics.stockOnHandUnits)}</div>
              </div>
              <div class="analytics-callout">
                <div class="analytics-callout__label">30-Day Stock Turn</div>
                <div class="analytics-callout__value">${formatNumber(analytics.stockTurnRate)}%</div>
              </div>
            </div>
            ${renderTable(
              [
                { label: 'Product' },
                { label: 'Qty', numeric: true },
                { label: 'Expiry' },
                { label: 'Priority' },
              ],
              inventoryPriorityRows,
              'No inventory records available yet.'
            )}
          </div>
        </section>

        <section class="analytics-hero">
          <div class="analytics-hero__copy">
            <div class="analytics-hero__eyebrow">Business Intelligence</div>
            <h2 class="analytics-hero__title">Commercial Performance Center</h2>
            <p class="analytics-hero__summary">A tighter view of sales, collections, institutional demand, and stock pressure.</p>
          </div>
          <div class="analytics-hero__scorecard">
            <div class="analytics-scorecard__label">30-Day Sales</div>
            <div class="analytics-scorecard__value">${formatCurrency(analytics.salesLast30Days)}</div>
            <div class="analytics-scorecard__subtext">
              Collection rate ${formatNumber(analytics.paymentReceivedRate)}% · overdue pending ${analytics.overduePaymentsCount}
            </div>
          </div>
        </section>
      </div>

      <div class="analytics-kpi-grid">
        <article class="analytics-kpi analytics-kpi--warm">
          <div class="analytics-kpi__label">Total Sales</div>
          <div class="analytics-kpi__value">${formatCurrency(analytics.totalSales)}</div>
          <div class="analytics-kpi__meta">${analytics.totalInvoices} invoices issued</div>
        </article>
        <article class="analytics-kpi analytics-kpi--cool">
          <div class="analytics-kpi__label">Avg Invoice Value</div>
          <div class="analytics-kpi__value">${formatCurrency(analytics.averageInvoiceValue)}</div>
          <div class="analytics-kpi__meta">${formatNumber(analytics.invoiceVelocity)} invoices per day over the last 30 days</div>
        </article>
        <article class="analytics-kpi analytics-kpi--danger">
          <div class="analytics-kpi__label">Pending Receivables</div>
          <div class="analytics-kpi__value">${formatCurrency(analytics.pendingReceivablesValue)}</div>
          <div class="analytics-kpi__meta">${analytics.pendingPayments} pending · ${analytics.overduePaymentsCount} overdue</div>
        </article>
        <article class="analytics-kpi analytics-kpi--neutral">
          <div class="analytics-kpi__label">Institution Reach</div>
          <div class="analytics-kpi__value">${analytics.activeInstitutionCount}</div>
          <div class="analytics-kpi__meta">${analytics.totalOrders} orders logged · ${formatNumber(analytics.orderCoverageRate)}% order coverage</div>
        </article>
      </div>

      <div class="analytics-grid">
        <section class="analytics-panel analytics-panel--feature">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Momentum</div>
              <div class="analytics-panel__title">14-Day Sales Momentum</div>
            </div>
            <div class="analytics-panel__badge">${formatCurrency(analytics.salesLast30Days)} in the last 30 days</div>
          </div>
          <div class="analytics-panel__body">
            ${renderLineChart(analytics.salesMomentum, {
              idPrefix: 'sales-momentum',
              currency: true,
              strokeStart: '#1f7a8c',
              strokeMid: '#d46e31',
              strokeEnd: '#6f52c8',
              fillStart: '#1f7a8c',
              fillEnd: '#6f52c8',
            })}
          </div>
        </section>

        <section class="analytics-panel analytics-panel--glass">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Cash Flow</div>
              <div class="analytics-panel__title">Collection Snapshot</div>
            </div>
          </div>
          <div class="analytics-panel__body">
            <div class="analytics-split-metrics">
              <div class="analytics-split-metric">
                <div class="analytics-split-metric__label">Pending</div>
                <div class="analytics-split-metric__value">${formatCurrency(analytics.pendingReceivablesValue)}</div>
                <div class="analytics-split-metric__track">
                  <div class="analytics-split-metric__fill analytics-split-metric__fill--danger" style="width: ${analytics.totalPayments ? Math.max(8, (analytics.pendingPayments / analytics.totalPayments) * 100) : 8}%"></div>
                </div>
              </div>
              <div class="analytics-split-metric">
                <div class="analytics-split-metric__label">Received</div>
                <div class="analytics-split-metric__value">${formatCurrency(analytics.receivedReceivablesValue)}</div>
                <div class="analytics-split-metric__track">
                  <div class="analytics-split-metric__fill analytics-split-metric__fill--success" style="width: ${analytics.totalPayments ? Math.max(8, (analytics.receivedPayments / analytics.totalPayments) * 100) : 8}%"></div>
                </div>
              </div>
              <div class="analytics-callout-row">
                <div class="analytics-callout">
                  <div class="analytics-callout__label">Overdue Pending</div>
                  <div class="analytics-callout__value">${analytics.overduePaymentsCount}</div>
                </div>
                <div class="analytics-callout">
                  <div class="analytics-callout__label">Collection Rate</div>
                  <div class="analytics-callout__value">${formatNumber(analytics.paymentReceivedRate)}%</div>
                </div>
              </div>
            </div>
            ${renderTable(
              [
                { label: 'Bill No' },
                { label: 'Institution' },
                { label: 'Invoice Date' },
                { label: 'Age (Days)', numeric: true },
              ],
              paymentAgingRows,
              'No pending payments to age right now.'
            )}
          </div>
        </section>

        <section class="analytics-panel">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Product Mix</div>
              <div class="analytics-panel__title">Top Product Sales</div>
            </div>
            <div class="analytics-panel__badge">${formatNumber(analytics.quantityLast30Days)} units sold in 30 days</div>
          </div>
          <div class="analytics-panel__body">
            <div class="analytics-product-list">${productSalesRows}</div>
          </div>
        </section>

        <section class="analytics-panel">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Forecasting</div>
              <div class="analytics-panel__title">6-Week Sales Outlook</div>
            </div>
            <div class="analytics-panel__badge">Projected from recent weekly run rate</div>
          </div>
          <div class="analytics-panel__body">
            ${renderLineChart(analytics.salesForecastSeries, {
              idPrefix: 'sales-forecast',
              currency: true,
              strokeStart: '#0f766e',
              strokeMid: '#eab308',
              strokeEnd: '#7c3aed',
              fillStart: '#0f766e',
              fillEnd: '#7c3aed',
            })}
          </div>
        </section>

        <section class="analytics-panel">
          <div class="analytics-panel__head">
            <div>
              <div class="analytics-panel__eyebrow">Institution Performance</div>
              <div class="analytics-panel__title">Top Institutions</div>
            </div>
            <div class="analytics-panel__badge">${analytics.activeInstitutionCount} active</div>
          </div>
          <div class="analytics-panel__body">
            <div class="analytics-rank-list">${institutionRows}</div>
          </div>
        </section>
      </div>
    </div>
  `;
}

function renderInventoryModal() {
  const modal = state.inventoryModal;
  if (!modal) return '';

  const title = modal.mode === 'edit' ? 'Edit Product' : 'Create Product';
  const button = modal.mode === 'edit' ? 'Update Product' : 'Save Product';
  const data = modal.data;

  return `
    <div class="modal-backdrop" data-action="close-inventory-modal">
      <div class="modal narrow" onclick="event.stopPropagation()">
        <div class="modal-head"><h2>${title}</h2></div>
        <div class="modal-body">
          <form id="inventory-form" class="field-grid">
            <div class="field">
              <label for="reg-no">Reg No</label>
              <input id="reg-no" name="regNo" value="${escapeHtml(data.regNo)}" required />
            </div>
            <div class="field">
              <label for="batch-no">Batch No</label>
              <input id="batch-no" name="batchNo" value="${escapeHtml(data.batchNo)}" required />
            </div>
            <div class="field">
              <label for="mfg-date">Mfg Date</label>
              <input id="mfg-date" name="mfgDate" type="date" value="${escapeHtml(data.mfgDate)}" required />
            </div>
            <div class="field">
              <label for="exp-date">Exp Date</label>
              <input id="exp-date" name="expDate" type="date" value="${escapeHtml(data.expDate)}" required />
            </div>
            <div class="field">
              <label for="quantity">Quantity</label>
              <input id="quantity" name="quantity" type="number" min="0.01" step="0.01" value="${escapeHtml(data.quantity)}" required />
            </div>
            <div class="field">
              <label for="description">Product Description</label>
              <input id="description" name="productDescription" value="${escapeHtml(data.productDescription)}" required />
            </div>
            <div class="field">
              <label for="trade-price">Trading Price</label>
              <input id="trade-price" name="tradePrice" type="number" min="0" step="0.01" value="${escapeHtml(data.tradePrice)}" />
            </div>
            <div class="field">
              <label for="discount">Discount (%)</label>
              <input id="discount" name="discountPercent" type="number" min="0" step="0.01" value="${escapeHtml(data.discountPercent)}" />
            </div>
            <div class="field full">
              <div class="button-row">
                <button class="btn secondary" type="button" data-action="close-inventory-modal">Cancel</button>
                <button class="btn primary" type="submit">${button}</button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;
}

function renderOrderModal() {
  const modal = state.orderModal;
  if (!modal) return '';

  return `
    <div class="modal-backdrop" data-action="close-order-modal">
      <div class="modal narrow" onclick="event.stopPropagation()">
        <div class="modal-head"><h2>Add Order</h2></div>
        <div class="modal-body">
          <form id="order-form" class="field-grid">
            <div class="field full">
              <label for="order-institution-name">Institution Name</label>
              <input id="order-institution-name" name="institutionName" value="${escapeHtml(modal.institutionName || '')}" required />
            </div>
            <div class="field full">
              <label for="order-number">Order Number</label>
              <input id="order-number" name="orderNumber" value="${escapeHtml(modal.orderNumber || '')}" required />
            </div>
            <div class="field full">
              <label for="order-date">Order Date</label>
              <input id="order-date" name="orderDate" type="date" value="${escapeHtml(modal.orderDate || '')}" required />
            </div>
            <div class="field full">
              <label for="order-file-name">Order File</label>
              <div class="field-inline">
                <input id="order-file-name" value="${escapeHtml(modal.fileName || '')}" readonly placeholder="Choose a PDF or image" />
                <button class="btn secondary" type="button" data-action="pick-order-file">Choose File</button>
              </div>
            </div>
            <div class="field full">
              <div class="button-row">
                <button class="btn secondary" type="button" data-action="close-order-modal">Cancel</button>
                <button class="btn primary" type="submit">Save Order</button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;
}

function renderProductSelectorModal() {
  if (!state.productSelectorOpen) return '';

  const rows = getSelectableProducts().map((item) => `
    <tr class="${state.productSelectorSelectedId === item.id ? 'selected' : ''}" data-product-select-row="${item.id}">
      <td>${escapeHtml(item.regNo)}</td>
      <td>${escapeHtml(item.batchNo)}</td>
      <td>${escapeHtml(item.productDescription)}</td>
      <td class="numeric">${formatNumber(item.availableQty)}</td>
    </tr>
  `);

  return `
    <div class="modal-backdrop" data-action="close-product-selector">
      <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-head"><h2>Select Product</h2></div>
        <div class="modal-body">
          ${renderTable(
            [
              { label: 'Reg No' },
              { label: 'Batch No' },
              { label: 'Product' },
              { label: 'Available Qty', numeric: true },
            ],
            rows,
            'No products with available stock found.'
          )}
          <div class="button-row between" style="margin-top:16px;">
            <div class="field-inline">
              <label for="selector-qty">Quantity</label>
              <input id="selector-qty" type="number" min="0.01" step="0.01" value="${escapeHtml(state.productSelectorQty)}" style="width:140px;" />
            </div>
            <div class="button-row">
              <button class="btn secondary" type="button" data-action="close-product-selector">Cancel</button>
              <button class="btn primary" type="button" data-action="confirm-product-selector">Add Product</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderInvoiceModal() {
  if (!state.invoiceModalOpen) return '';
  const draft = state.invoiceDraft || {
    fileNo: '',
    billPrefix: '',
    deliveryChallanNo: '',
    orderContractNo: '',
    orderDate: '',
    inspectionNoteNo: '',
    toText: '',
  };

  const selectedRows = Array.from(state.selectedProducts.values()).map((product) => `
    <tr data-selected-product-row="${product.inventoryItemId}">
      <td>${escapeHtml(product.regNo)}</td>
      <td>${escapeHtml(product.batchNo)}</td>
      <td>${escapeHtml(product.mfgDate)}</td>
      <td>${escapeHtml(product.expDate)}</td>
      <td class="numeric">${formatNumber(product.selectedQty)}</td>
      <td>${escapeHtml(product.productDescription)}</td>
      <td class="numeric">${formatNumber(product.unitPrice)}</td>
      <td class="numeric">${formatNumber(product.selectedQty * product.unitPrice)}</td>
    </tr>
  `);

  return `
    <div class="modal-backdrop" data-action="close-invoice-modal">
      <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-head"><h2>Create Invoice</h2></div>
        <div class="modal-body">
          <form id="invoice-form">
            <div class="field-grid">
              <div class="field">
                <label for="file-no">File No.</label>
                <input id="file-no" name="fileNo" data-invoice-field="fileNo" value="${escapeHtml(draft.fileNo)}" required />
              </div>
              <div class="field">
                <label for="bill-prefix">Bill No</label>
                <div class="field-inline">
                  <input id="bill-prefix" name="billPrefix" data-invoice-field="billPrefix" pattern="[A-Za-z0-9-]*" value="${escapeHtml(draft.billPrefix)}" required />
                  <span class="suffix">${escapeHtml(billYearSuffix)}</span>
                </div>
              </div>
              <div class="field">
                <label for="delivery-challan">Delivery Challan No</label>
                <input id="delivery-challan" name="deliveryChallanNo" data-invoice-field="deliveryChallanNo" value="${escapeHtml(draft.deliveryChallanNo)}" />
              </div>
              <div class="field">
                <label for="order-contract">Your Order/Contract Number</label>
                <input id="order-contract" name="orderContractNo" data-invoice-field="orderContractNo" value="${escapeHtml(draft.orderContractNo)}" />
              </div>
              <div class="field">
                <label for="order-date">Your Order Date</label>
                <input id="order-date" name="orderDate" data-invoice-field="orderDate" type="date" value="${escapeHtml(draft.orderDate)}" />
              </div>
              <div class="field">
                <label for="inspection-note">Inspection Note No</label>
                <input id="inspection-note" name="inspectionNoteNo" data-invoice-field="inspectionNoteNo" value="${escapeHtml(draft.inspectionNoteNo)}" />
              </div>
              <div class="field full">
                <label for="to-text">To</label>
                <textarea id="to-text" name="toText" data-invoice-field="toText" required>${escapeHtml(draft.toText)}</textarea>
              </div>
            </div>

            <div style="margin-top:26px;">
              <div class="product-actions">
                <div>
                  <strong>Selected Products</strong>
                  <div class="selected-count">${state.selectedProducts.size} item(s) selected</div>
                </div>
                <div class="button-row">
                  <button class="btn secondary" type="button" data-action="remove-selected-product">Remove Selected</button>
                  <button class="btn secondary" type="button" data-action="open-product-selector">Add Product</button>
                </div>
              </div>
              ${renderTable(
                [
                  { label: 'Reg No' },
                  { label: 'Batch No' },
                  { label: 'Mfg-Date' },
                  { label: 'Exp.date' },
                  { label: 'Quantity', numeric: true },
                  { label: 'Product Description' },
                  { label: 'Price/Unit', numeric: true },
                  { label: 'Amount Rs', numeric: true },
                ],
                selectedRows,
                'No products selected yet.'
              )}
            </div>

            <div class="button-row" style="margin-top:22px;">
              <button class="btn secondary" type="button" data-action="close-invoice-modal">Cancel</button>
              <button class="btn primary" type="submit">Save Invoice</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;
}

function renderAppShell() {
  const viewTitle =
    state.activeView === 'inventory'
      ? 'Inventory'
      : state.activeView === 'analytics'
        ? 'Business Intelligence'
      : state.activeView === 'payments'
        ? 'Payments'
      : state.activeView === 'orders'
        ? 'Orders'
      : state.activeView === 'reports'
        ? 'Sales Reports'
        : 'Invoices';

  const mainView =
    state.activeView === 'inventory'
      ? renderInventoryView()
      : state.activeView === 'analytics'
        ? renderDataAnalyticsView()
      : state.activeView === 'payments'
        ? renderPaymentsView()
      : state.activeView === 'orders'
        ? renderOrdersView()
      : state.activeView === 'reports'
        ? renderSalesReportsView()
        : renderInvoicesView();

  appRoot.innerHTML = `
    <div class="screen app-shell">
      ${state.activeView === 'inventory' ? renderInventoryAlerts() : ''}
      <aside class="sidebar">
        <img class="sidebar-logo" src="../assets/logo.png" alt="United Agencies karachi logo" />
        <div class="sidebar-divider"></div>
        <div class="nav-list">
          <button class="nav-btn ${state.activeView === 'invoices' ? 'active' : ''}" data-action="nav-invoices">Invoices</button>
          <button class="nav-btn ${state.activeView === 'analytics' ? 'active' : ''}" data-action="nav-analytics">Business Intelligence</button>
          <button class="nav-btn ${state.activeView === 'payments' ? 'active' : ''}" data-action="nav-payments">Payments</button>
          <button class="nav-btn ${state.activeView === 'orders' ? 'active' : ''}" data-action="nav-orders">Orders</button>
          <button class="nav-btn ${state.activeView === 'reports' ? 'active' : ''}" data-action="nav-reports">Sales Reports</button>
          <button class="nav-btn ${state.activeView === 'inventory' ? 'active' : ''}" data-action="nav-inventory">Inventory</button>
        </div>
        <div class="sidebar-footer">
          <button class="nav-btn" data-action="logout">Logout</button>
          <div class="datetime" id="sidebar-datetime">${escapeHtml(formatSidebarDate())}</div>
        </div>
      </aside>
      <main class="main-area">
        <header class="header"><h1>${escapeHtml(viewTitle)}</h1></header>
        <section class="content">${mainView}</section>
      </main>
      ${renderInventoryModal()}
      ${renderOrderModal()}
      ${renderInvoiceModal()}
      ${renderProductSelectorModal()}
    </div>
  `;

  bindAppEvents();
}

function render() {
  if (!state.session) {
    renderLogin();
    return;
  }
  renderAppShell();
}

async function refreshData() {
  const [invoices, orders, payments, inventory] = await Promise.all([
    window.unitedApp.listInvoices(),
    window.unitedApp.listOrders(),
    window.unitedApp.listPayments(),
    window.unitedApp.listInventory(),
  ]);
  state.invoices = invoices;
  state.orders = orders;
  state.payments = payments;
  state.inventory = inventory;
}

async function onLoginSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const username = form.username.value.trim();
  const password = form.password.value;
  const errorNode = document.getElementById('login-error');

  if (!username || !password) {
    errorNode.textContent = 'Please enter both username and password';
    return;
  }

  try {
    const result = await window.unitedApp.login({ username, password });
    if (!result.ok) {
      errorNode.textContent = 'Invalid username or password';
      return;
    }

    state.session = { username, role: result.role || 'user' };
    await refreshData();
    render();
  } catch (error) {
    errorNode.textContent = error.message;
  }
}

function bindAppEvents() {
  document.querySelectorAll('[data-action]').forEach((node) => {
    node.addEventListener('click', onActionClick);
  });

  document.querySelectorAll('[data-inventory-row]').forEach((row) => {
    row.addEventListener('click', () => {
      state.selectedInventoryId = Number(row.dataset.inventoryRow);
      render();
    });
  });

  document.querySelectorAll('[data-product-select-row]').forEach((row) => {
    row.addEventListener('click', () => {
      state.productSelectorSelectedId = Number(row.dataset.productSelectRow);
      render();
    });
  });

  document.querySelectorAll('[data-selected-product-row]').forEach((row) => {
    row.addEventListener('click', () => {
      document.querySelectorAll('[data-selected-product-row]').forEach((item) => item.classList.remove('selected'));
      row.classList.add('selected');
    });
  });

  const inventoryForm = document.getElementById('inventory-form');
  if (inventoryForm) {
    inventoryForm.addEventListener('submit', onInventorySubmit);
  }

  const orderForm = document.getElementById('order-form');
  if (orderForm) {
    orderForm.addEventListener('submit', onOrderSubmit);
  }

  const invoiceForm = document.getElementById('invoice-form');
  if (invoiceForm) {
    invoiceForm.addEventListener('submit', onInvoiceSubmit);
  }

  document.querySelectorAll('[data-invoice-field]').forEach((field) => {
    field.addEventListener('input', (event) => {
      if (!state.invoiceDraft) state.invoiceDraft = {};
      state.invoiceDraft[event.target.dataset.invoiceField] = event.target.value;
    });
  });

  const selectorQty = document.getElementById('selector-qty');
  if (selectorQty) {
    selectorQty.addEventListener('input', (event) => {
      state.productSelectorQty = event.target.value;
    });
  }

  document.querySelectorAll('[data-payment-status-select]').forEach((field) => {
    field.addEventListener('change', onPaymentStatusChange);
  });

  clearInterval(window.__sidebarTimer);
  window.__sidebarTimer = setInterval(() => {
    const current = document.getElementById('sidebar-datetime');
    if (current) current.textContent = formatSidebarDate();
  }, 1000);
}

async function onActionClick(event) {
  const action = event.currentTarget.dataset.action;

  if (action === 'nav-invoices') {
    state.activeView = 'invoices';
    render();
    return;
  }

  if (action === 'nav-orders') {
    state.activeView = 'orders';
    render();
    return;
  }

  if (action === 'nav-analytics') {
    state.activeView = 'analytics';
    render();
    return;
  }

  if (action === 'nav-payments') {
    state.activeView = 'payments';
    render();
    return;
  }

  if (action === 'generate-invoice-pdf') {
    const invoiceId = Number(event.currentTarget.dataset.invoiceId);
    if (!invoiceId) {
      await window.unitedApp.showError('Invoice Error', 'Unable to determine which invoice to generate.');
      return;
    }

    try {
      const result = await window.unitedApp.generateInvoicePdf(invoiceId);
      if (result?.pdfPath) {
        await window.unitedApp.openPath(result.pdfPath);
      }
      await window.unitedApp.showInfo(
        'Invoice Generated',
        result?.pdfPath
          ? `Template PDF created at:\n${result.pdfPath}`
          : 'Invoice PDF was generated.'
      );
    } catch (error) {
      await window.unitedApp.showError('Generate Failed', error.message);
    }
    return;
  }

  if (action === 'nav-inventory') {
    state.activeView = 'inventory';
    render();
    return;
  }

  if (action === 'nav-reports') {
    state.activeView = 'reports';
    render();
    return;
  }

  if (action === 'logout') {
    state.session = null;
    state.selectedInventoryId = null;
    state.invoiceModalOpen = false;
    state.invoiceDraft = null;
    state.orderModal = null;
    state.inventoryModal = null;
    state.productSelectorOpen = false;
    state.selectedProducts = new Map();
    render();
    return;
  }

  if (action === 'open-order-modal') {
    state.orderModal = {
      institutionName: '',
      orderNumber: '',
      orderDate: '',
      fileName: '',
      filePath: '',
    };
    render();
    return;
  }

  if (action === 'close-order-modal') {
    state.orderModal = null;
    render();
    return;
  }

  if (action === 'pick-order-file') {
    try {
      const result = await window.unitedApp.pickOrderFile();
      if (!result?.canceled && state.orderModal) {
        state.orderModal.fileName = result.fileName || '';
        state.orderModal.filePath = result.filePath || '';
        render();
      }
    } catch (error) {
      await window.unitedApp.showError('File Picker Error', error.message);
    }
    return;
  }

  if (action === 'open-order-file') {
    const targetPath = event.currentTarget.dataset.orderFilePath || '';
    if (!targetPath) {
      await window.unitedApp.showError('Open Failed', 'Order file path is missing.');
      return;
    }
    await window.unitedApp.openPath(targetPath);
    return;
  }

  if (action === 'open-invoice-modal') {
    state.invoiceModalOpen = true;
    state.invoiceDraft = {
      fileNo: '',
      billPrefix: '',
      deliveryChallanNo: '',
      orderContractNo: '',
      orderDate: '',
      inspectionNoteNo: '',
      toText: '',
    };
    state.selectedProducts = new Map();
    state.productSelectorSelectedId = null;
    render();
    return;
  }

  if (action === 'close-invoice-modal') {
    state.invoiceModalOpen = false;
    state.invoiceDraft = null;
    state.productSelectorOpen = false;
    render();
    return;
  }

  if (action === 'open-product-selector') {
    state.productSelectorOpen = true;
    state.productSelectorQty = '';
    state.productSelectorSelectedId = null;
    render();
    return;
  }

  if (action === 'close-product-selector') {
    state.productSelectorOpen = false;
    state.productSelectorQty = '';
    state.productSelectorSelectedId = null;
    render();
    return;
  }

  if (action === 'confirm-product-selector') {
    const selected = getSelectableProducts().find((item) => item.id === state.productSelectorSelectedId);
    const qty = Number(state.productSelectorQty);

    if (!selected) {
      await window.unitedApp.showError('Selection Required', 'Please select a product.');
      return;
    }
    if (!Number.isFinite(qty)) {
      await window.unitedApp.showError('Validation', 'Quantity must be numeric.');
      return;
    }
    if (qty <= 0) {
      await window.unitedApp.showError('Validation', 'Quantity must be greater than 0.');
      return;
    }
    if (qty > selected.availableQty) {
      await window.unitedApp.showError('Validation', `Only ${formatNumber(selected.availableQty)} available in inventory.`);
      return;
    }

    const existing = state.selectedProducts.get(selected.id);
    if (existing) {
      const totalQty = existing.selectedQty + qty;
      if (totalQty > selected.availableQty) {
        await window.unitedApp.showError('Validation', `Selected quantity exceeds available stock (${formatNumber(selected.availableQty)}).`);
        return;
      }
      existing.selectedQty = totalQty;
      state.selectedProducts.set(selected.id, existing);
    } else {
      state.selectedProducts.set(selected.id, {
        inventoryItemId: selected.id,
        regNo: selected.regNo,
        batchNo: selected.batchNo,
        mfgDate: selected.mfgDate,
        expDate: selected.expDate,
        productDescription: selected.productDescription,
        availableQty: selected.availableQty,
        unitPrice: selected.unitPrice,
        selectedQty: qty,
      });
    }

    state.productSelectorOpen = false;
    state.productSelectorQty = '';
    state.productSelectorSelectedId = null;
    render();
    return;
  }

  if (action === 'add-product') {
    state.inventoryModal = {
      mode: 'create',
      data: {
        regNo: '',
        batchNo: '',
        mfgDate: '',
        expDate: '',
        quantity: '',
        productDescription: '',
        tradePrice: '',
        discountPercent: '',
      },
    };
    render();
    return;
  }

  if (action === 'edit-product') {
    const item = state.inventory.find((entry) => entry.id === state.selectedInventoryId);
    if (!item) {
      await window.unitedApp.showError('Selection Required', 'Please select a product to edit.');
      return;
    }

    state.inventoryModal = {
      mode: 'edit',
      data: {
        id: item.id,
        regNo: item.regNo,
        batchNo: item.batchNo,
        mfgDate: item.mfgDate,
        expDate: item.expDate,
        quantity: String(item.quantity),
        productDescription: item.productDescription,
        tradePrice: String(item.tradePrice),
        discountPercent: String(item.discountPercent),
      },
    };
    render();
    return;
  }

  if (action === 'close-inventory-modal') {
    state.inventoryModal = null;
    render();
    return;
  }

  if (action === 'remove-selected-product') {
    const selectedRow = document.querySelector('[data-selected-product-row].selected');
    if (!selectedRow) return;
    state.selectedProducts.delete(Number(selectedRow.dataset.selectedProductRow));
    render();
    return;
  }

  if (action === 'search-inventory') {
    state.inventoryFilters = {
      regNo: document.getElementById('filter-reg-no').value,
      batchNo: document.getElementById('filter-batch-no').value,
      productName: document.getElementById('filter-product-name').value,
    };
    render();
    return;
  }

  if (action === 'clear-inventory') {
    state.inventoryFilters = { regNo: '', batchNo: '', productName: '' };
    render();
    return;
  }

  if (action === 'search-invoices') {
    state.invoiceFilters = {
      billNo: document.getElementById('filter-invoice-bill-no').value,
      toText: document.getElementById('filter-invoice-to').value,
      dateFrom: document.getElementById('filter-invoice-date-from').value,
      dateTo: document.getElementById('filter-invoice-date-to').value,
    };
    render();
    return;
  }

  if (action === 'clear-invoices') {
    state.invoiceFilters = { billNo: '', toText: '', dateFrom: '', dateTo: '' };
    render();
    return;
  }

  if (action === 'search-orders') {
    state.orderFilters = {
      institutionName: document.getElementById('filter-order-institution-name').value,
      dateFrom: document.getElementById('filter-order-date-from').value,
      dateTo: document.getElementById('filter-order-date-to').value,
    };
    render();
    return;
  }

  if (action === 'clear-orders') {
    state.orderFilters = { institutionName: '', dateFrom: '', dateTo: '' };
    render();
    return;
  }

  if (action === 'search-payments') {
    state.paymentFilters = {
      billNo: document.getElementById('filter-payment-bill-no').value,
      invoiceDate: document.getElementById('filter-payment-invoice-date').value,
      dateFrom: document.getElementById('filter-payment-date-from').value,
      dateTo: document.getElementById('filter-payment-date-to').value,
    };
    render();
    return;
  }

  if (action === 'clear-payments') {
    state.paymentFilters = { billNo: '', invoiceDate: '', dateFrom: '', dateTo: '' };
    render();
    return;
  }
}

async function onInventorySubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    regNo: form.regNo.value.trim(),
    batchNo: form.batchNo.value.trim(),
    mfgDate: form.mfgDate.value.trim(),
    expDate: form.expDate.value.trim(),
    quantity: Number(form.quantity.value),
    productDescription: form.productDescription.value.trim(),
    tradePrice: Number(form.tradePrice.value || 0),
    discountPercent: Number(form.discountPercent.value || 0),
  };

  if (!payload.regNo || !payload.batchNo || !payload.mfgDate || !payload.expDate || !payload.productDescription) {
    await window.unitedApp.showError('Validation', 'Please fill all required product fields.');
    return;
  }

  if (!(payload.quantity > 0)) {
    await window.unitedApp.showError('Validation', 'Quantity must be greater than 0.');
    return;
  }

  try {
    if (state.inventoryModal.mode === 'edit') {
      await window.unitedApp.updateInventory({ ...payload, id: state.inventoryModal.data.id });
      await window.unitedApp.showInfo('Success', 'Product updated successfully.');
    } else {
      await window.unitedApp.saveInventory(payload);
      await window.unitedApp.showInfo('Success', 'Product saved successfully.');
    }

    await refreshData();
    state.inventoryModal = null;
    render();
  } catch (error) {
    await window.unitedApp.showError('Save Failed', error.message);
  }
}

async function onOrderSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    institutionName: form.institutionName.value.trim(),
    orderNumber: form.orderNumber.value.trim(),
    orderDate: form.orderDate.value.trim(),
    sourceFilePath: state.orderModal?.filePath || '',
  };

  if (!payload.institutionName || !payload.orderNumber || !payload.orderDate || !payload.sourceFilePath) {
    await window.unitedApp.showError('Validation', 'Please fill institution name, order number, order date, and choose a file.');
    return;
  }

  try {
    await window.unitedApp.saveOrder(payload);
    await window.unitedApp.showInfo('Success', 'Order saved successfully.');
    await refreshData();
    state.orderModal = null;
    state.activeView = 'orders';
    render();
  } catch (error) {
    await window.unitedApp.showError('Save Failed', error.message);
  }
}

async function onPaymentStatusChange(event) {
  const paymentId = Number(event.currentTarget.dataset.paymentStatusSelect);
  const status = event.currentTarget.value;

  try {
    await window.unitedApp.updatePaymentStatus({ paymentId, status });
    await refreshData();
    render();
  } catch (error) {
    await window.unitedApp.showError('Update Failed', error.message);
  }
}

async function onInvoiceSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const fileNo = form.fileNo.value.trim();
  const billPrefix = form.billPrefix.value.trim();
  const billNo = billPrefix ? `${billPrefix}${billYearSuffix}` : '';
  const toText = form.toText.value.trim();

  if (!fileNo || !billNo || !toText) {
    await window.unitedApp.showError('Validation', 'Please fill required fields: File No, Bill No, and To.');
    return;
  }

  if (!/^[A-Za-z0-9-]+$/.test(billPrefix)) {
    await window.unitedApp.showError('Validation', 'Bill No prefix allows only letters, numbers, and hyphen.');
    return;
  }

  if (state.selectedProducts.size === 0) {
    await window.unitedApp.showError('Validation', 'Please select at least one product.');
    return;
  }

  const payload = {
    fileNo,
    billNo,
    deliveryChallanNo: form.deliveryChallanNo.value.trim(),
    orderContractNo: form.orderContractNo.value.trim(),
    orderDate: form.orderDate.value.trim(),
    inspectionNoteNo: form.inspectionNoteNo.value.trim(),
    toText,
    products: Array.from(state.selectedProducts.values()).map((product) => ({
      inventoryItemId: product.inventoryItemId,
      productDescription: product.productDescription,
      quantity: product.selectedQty,
      unitPrice: product.unitPrice,
    })),
  };

  try {
    const result = await window.unitedApp.saveInvoice(payload);
    const messages = ['Invoice saved and inventory updated successfully.'];

    if (result?.pdfPath) {
      messages.push(`Template PDF created at:\n${result.pdfPath}`);
      await window.unitedApp.openPath(result.pdfPath);
    } else if (result?.pdfError) {
      messages.push(`Invoice data was saved, but PDF generation failed:\n${result.pdfError}`);
    }

    await window.unitedApp.showInfo('Success', messages.join('\n\n'));
    await refreshData();
    state.invoiceModalOpen = false;
    state.invoiceDraft = null;
    state.productSelectorOpen = false;
    state.selectedProducts = new Map();
    render();
  } catch (error) {
    await window.unitedApp.showError('Save Failed', error.message);
  }
}

async function init() {
  try {
    await window.unitedApp.bootstrap();
  } catch (error) {
    appRoot.innerHTML = `<div class="screen login-screen"><div class="login-card"><h2>Startup failed</h2><p>${escapeHtml(error.message)}</p></div></div>`;
    return;
  }

  render();
}

init();
