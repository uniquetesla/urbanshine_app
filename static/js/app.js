document.addEventListener('DOMContentLoaded', () => {
  const shell = document.querySelector('.app-shell');
  const menuToggle = document.getElementById('menuToggle');

  if (shell && menuToggle) {
    menuToggle.addEventListener('click', () => {
      const isOpen = shell.getAttribute('data-sidebar-open') === 'true';
      shell.setAttribute('data-sidebar-open', String(!isOpen));
    });

    if (window.innerWidth <= 1080) {
      shell.setAttribute('data-sidebar-open', 'false');
    }
  }

  const orderForm = document.getElementById('order-form');
  if (!orderForm) {
    return;
  }

  const servicePrices = JSON.parse(document.getElementById('service-prices-data')?.textContent || '{}');
  const serviceDurations = JSON.parse(document.getElementById('service-durations-data')?.textContent || '{}');
  const soilingMultipliers = JSON.parse(document.getElementById('soiling-multipliers-data')?.textContent || '{}');
  const surchargeValues = JSON.parse(document.getElementById('surcharge-values-data')?.textContent || '{}');
  const totalPriceElement = document.getElementById('order-total-price');
  const totalDurationElement = document.getElementById('order-total-duration');

  const formatCurrency = (value) => `${Number(value).toFixed(2).replace('.', ',')} €`;

  const updatePrices = () => {
    let totalPrice = 0;
    let totalDuration = 0;
    const rows = orderForm.querySelectorAll('tbody tr');

    rows.forEach((row) => {
      const serviceField = row.querySelector('select[name$="-leistung"]');
      const soilingField = row.querySelector('select[name$="-verschmutzungsgrad"]');
      const surchargeField = row.querySelector('select[name$="-zuschlag"]');
      const deleteField = row.querySelector('input[name$="-DELETE"]');
      const rowPriceElement = row.querySelector('[data-role="row-price"]');
      const rowDurationElement = row.querySelector('[data-role="row-duration"]');

      if (!serviceField || !soilingField || !rowPriceElement || !rowDurationElement || (deleteField && deleteField.checked)) {
        if (rowPriceElement) {
          rowPriceElement.textContent = formatCurrency(0);
        }
        if (rowDurationElement) {
          rowDurationElement.textContent = '0 Min.';
        }
        return;
      }

      const basePrice = Number(servicePrices[serviceField.value] || 0);
      const baseDuration = Number(serviceDurations[serviceField.value] || 0);
      const multiplier = Number(soilingMultipliers[soilingField.value] || 0);

      if (!basePrice || !multiplier) {
        rowPriceElement.textContent = formatCurrency(0);
        rowDurationElement.textContent = baseDuration ? `${Math.round(baseDuration)} Min.` : '0 Min.';
        totalDuration += baseDuration;
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
      rowDurationElement.textContent = `${Math.round(baseDuration)} Min.`;
      totalPrice += rowTotal;
      totalDuration += baseDuration;
    });

    if (totalPriceElement) {
      totalPriceElement.textContent = formatCurrency(totalPrice);
    }

    if (totalDurationElement) {
      totalDurationElement.textContent = `${Math.round(totalDuration)} Min.`;
    }
  };

  orderForm.addEventListener('change', updatePrices);
  orderForm.addEventListener('input', updatePrices);
  updatePrices();
});
