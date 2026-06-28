document.querySelectorAll('.spark-bar').forEach((bar, i) => {
  const total = document.querySelectorAll('.spark-bar').length;
  const label = bar.classList.contains('ok') ? 'success' : 'failed';
  bar.title = `Run ${i + 1} of ${total}: ${label}`;
});
