// ============ 图表初始化 ============

const chartColors = {
  cyan: 'rgba(6,182,212,1)', cyanA: 'rgba(6,182,212,0.2)',
  blue: 'rgba(59,130,246,1)', blueA: 'rgba(59,130,246,0.2)',
  green: 'rgba(16,185,129,1)', greenA: 'rgba(16,185,129,0.2)',
  purple: 'rgba(139,92,246,1)', purpleA: 'rgba(139,92,246,0.2)',
  amber: 'rgba(245,158,11,1)', amberA: 'rgba(245,158,11,0.2)',
};

function initCharts() {
  // 月度对话量
  const volumeEl = document.getElementById('chartVolume');
  if (volumeEl) {
    new Chart(volumeEl, {
      type: 'line',
      data: {
        labels: ['1月','2月','3月','4月','5月','6月'],
        datasets: [{
          label: 'AI 自动解决', data: [820,940,1050,1120,1180,1260],
          borderColor: chartColors.cyan, backgroundColor: chartColors.cyanA, fill: true, tension: 0.4
        },{
          label: '转人工', data: [380,360,320,290,270,250],
          borderColor: chartColors.amber, backgroundColor: chartColors.amberA, fill: true, tension: 0.4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { color: '#94a3b8' } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  }

  // 问题分类分布
  const catEl = document.getElementById('chartCategory');
  if (catEl) {
    new Chart(catEl, {
      type: 'doughnut',
      data: {
        labels: ['验号换绑','包赔售后','交易流程','防诈骗','平台规则','其他'],
        datasets: [{
          data: [32,22,18,12,9,7],
          backgroundColor: [chartColors.cyan,chartColors.blue,chartColors.green,chartColors.amber,chartColors.purple,'rgba(100,116,139,0.5)'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'right', labels: { color: '#94a3b8', padding: 12 } } }
      }
    });
  }
}
