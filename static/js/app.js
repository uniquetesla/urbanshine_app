document.addEventListener('DOMContentLoaded', () => {
  const shell = document.querySelector('.app-shell');
  const menuToggle = document.getElementById('menuToggle');

  if (!shell || !menuToggle) {
    return;
  }

  menuToggle.addEventListener('click', () => {
    const isOpen = shell.getAttribute('data-sidebar-open') === 'true';
    shell.setAttribute('data-sidebar-open', String(!isOpen));
  });

  if (window.innerWidth <= 1080) {
    shell.setAttribute('data-sidebar-open', 'false');
  }

  const orderForm = document.getElementById('order-form');
  if (!orderForm) {
    return;
  }

  const servicePrices = JSON.parse(document.getElementById('service-prices-data')?.textContent || '{}');
  const soilingMultipliers = JSON.parse(document.getElementById('soiling-multipliers-data')?.textContent || '{}');
  const surchargeValues = JSON.parse(document.getElementById('surcharge-values-data')?.textContent || '{}');
  const totalPriceElement = document.getElementById('order-total-price');

  const formatCurrency = (value) => `${Number(value).toFixed(2).replace('.', ',')} €`;

  const updatePrices = () => {
    let total = 0;
    const rows = orderForm.querySelectorAll('tbody tr');

    rows.forEach((row) => {
      const serviceField = row.querySelector('select[name$="-leistung"]');
      const soilingField = row.querySelector('select[name$="-verschmutzungsgrad"]');
      const surchargeField = row.querySelector('select[name$="-zuschlag"]');
      const deleteField = row.querySelector('input[name$="-DELETE"]');
      const rowPriceElement = row.querySelector('[data-role="row-price"]');

      if (!serviceField || !soilingField || !rowPriceElement || (deleteField && deleteField.checked)) {
        if (rowPriceElement) {
          rowPriceElement.textContent = formatCurrency(0);
        }
        return;
      }

      const basePrice = Number(servicePrices[serviceField.value] || 0);
      const multiplier = Number(soilingMultipliers[soilingField.value] || 0);

      if (!basePrice || !multiplier) {
        rowPriceElement.textContent = formatCurrency(0);
        return;
      }

      let rowTotal = basePrice * multiplier;
      const surchargeConfig = surchargeValues[surchargeField?.value];

      if (surchargeConfig) {
        const amount = Number(surchargeConfig.amount || 0);
        if (surchargeConfig.is_percentage) {
          rowTotal += (rowTotal * amount) / 100;
        } else {
          rowTotal += amount;
        }
      }

      rowPriceElement.textContent = formatCurrency(rowTotal);
      total += rowTotal;
    });

    if (totalPriceElement) {
      totalPriceElement.textContent = formatCurrency(total);
    }
  };

  orderForm.addEventListener('change', updatePrices);
  updatePrices();
});
