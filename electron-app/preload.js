const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('unitedApp', {
  bootstrap: () => ipcRenderer.invoke('app:bootstrap'),
  login: (credentials) => ipcRenderer.invoke('auth:login', credentials),
  listInvoices: () => ipcRenderer.invoke('invoices:list'),
  listOrders: () => ipcRenderer.invoke('orders:list'),
  listPayments: () => ipcRenderer.invoke('payments:list'),
  saveInvoice: (payload) => ipcRenderer.invoke('invoices:save', payload),
  generateInvoicePdf: (invoiceId) => ipcRenderer.invoke('invoices:generatePdf', invoiceId),
  saveOrder: (payload) => ipcRenderer.invoke('orders:save', payload),
  updatePaymentStatus: (payload) => ipcRenderer.invoke('payments:updateStatus', payload),
  listInventory: () => ipcRenderer.invoke('inventory:list'),
  saveInventory: (payload) => ipcRenderer.invoke('inventory:save', payload),
  updateInventory: (payload) => ipcRenderer.invoke('inventory:update', payload),
  openPath: (targetPath) => ipcRenderer.invoke('shell:openPath', targetPath),
  pickOrderFile: () => ipcRenderer.invoke('dialog:pickOrderFile'),
  showError: (title, message) => ipcRenderer.invoke('dialog:error', { title, message }),
  showInfo: (title, message) => ipcRenderer.invoke('dialog:info', { title, message }),
});
