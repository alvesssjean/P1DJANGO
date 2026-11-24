(function () {
  function lerDados(id) {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : null;
  }

  const porMes = lerDados('dados-mes');
  const canvasMes = document.getElementById('graf-mes');
  if (porMes && porMes.length && canvasMes) {
    new Chart(canvasMes, {
      type: 'bar',
      data: {
        labels: porMes.map(d => d.mes),
        datasets: [{ label: 'Tarefas criadas', data: porMes.map(d => d.total) }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  const status = lerDados('dados-status');
  const canvasStatus = document.getElementById('graf-status');
  if (status && canvasStatus) {
    new Chart(canvasStatus, {
      type: 'doughnut',
      data: {
        labels: status.map(d => d.status),
        datasets: [{ data: status.map(d => d.total) }],
      },
    });
  }
})();