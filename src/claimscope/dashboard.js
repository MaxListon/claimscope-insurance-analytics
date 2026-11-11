"use strict";
const D = JSON.parse(document.getElementById("dataset").textContent),
  T = D.totals,
  M = D.model;
const $ = (s) => document.querySelector(s),
  N = (x, d = 0) =>
    Number(x).toLocaleString("en-US", {
      maximumFractionDigits: d,
      minimumFractionDigits: d,
    }),
  esc = (s) =>
    String(s).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
function cards(id, rows) {
  $(id).innerHTML = rows
    .map(
      ([l, n, c]) =>
        `<div class="card"><label>${l}</label><div class="number">${n}</div><div class="caption">${c}</div></div>`,
    )
    .join("");
}
function bars(id, rows) {
  const max = Math.max(...rows.map((r) => r.value), 1);
  $(id).innerHTML = rows
    .map(
      (r) =>
        `<div class="barrow"><span>${esc(r.label)}</span><div class="track"><div class="fill" style="width:${(100 * r.value) / max}%"></div></div><b>${N(r.value, r.digits ?? 1)}</b></div>`,
    )
    .join("");
}
function table(id, headers, rows) {
  $(id).innerHTML =
    "<thead><tr>" +
    headers.map((h) => `<th>${esc(h)}</th>`).join("") +
    "</tr></thead><tbody>" +
    rows
      .map(
        (row) =>
          "<tr>" +
          row
            .map((c, i) => `<td class="${i ? "num" : ""}">${esc(c)}</td>`)
            .join("") +
          "</tr>",
      )
      .join("") +
    "</tbody>";
}
const tabs = [...document.querySelectorAll("[data-tab]")];
function activate(b) {
  document.body.dataset.view = b.dataset.tab;
  tabs.forEach((x) => {
    x.setAttribute("aria-selected", String(x === b));
    x.tabIndex = x === b ? 0 : -1;
  });
  document
    .querySelectorAll(".panel")
    .forEach((p) => (p.hidden = p.id !== b.dataset.tab));
  $("#view-link").href = "#" + b.dataset.tab;
  if (location.hash !== "#" + b.dataset.tab)
    history.replaceState(null, "", "#" + b.dataset.tab);
}
tabs.forEach((b, i) => {
  b.tabIndex = i === 0 ? 0 : -1;
  b.addEventListener("click", () => activate(b));
  b.addEventListener("keydown", (e) => {
    let j;
    if (e.key === "ArrowRight") j = (i + 1) % tabs.length;
    else if (e.key === "ArrowLeft") j = (i + tabs.length - 1) % tabs.length;
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = tabs.length - 1;
    else return;
    e.preventDefault();
    activate(tabs[j]);
    tabs[j].focus();
  });
});
cards("#overview-cards", [
  ["Policies", N(T.policies), "Real anonymized source records"],
  ["Policy-years", N(T.exposure), "Earned exposure, not policy count"],
  [
    "Claims / 100 policy-years",
    N(T.frequency * 100, 2),
    "Reported count basis",
  ],
  [
    "Recorded cost / year",
    N(T.cost_per_year, 2),
    "Linked source monetary units",
  ],
]);
$("#overview-note").textContent =
  T.mismatch_policies === 0 && T.orphan_records === 0
    ? "Source reconciliation passed. Every policy claim count agrees with its linked amount records; no unmatched claim records."
    : `${N(T.mismatch_policies)} count exceptions and ${N(T.orphan_records)} unmatched records require review.`;
bars(
  "#sensitivity",
  D.sensitivity.map((r) => ({ label: r.basis, value: r.cost_per_year })),
);
$("#interval").textContent =
  `Policy bootstrap interval for the full linked cost rate: ${N(T.cost_bootstrap_interval[0], 2)}–${N(T.cost_bootstrap_interval[1], 2)}. The top 1% tail contributes ${N(100 * T.top_one_pct_amount_share, 1)}% of source recorded amount (strictly above the 99th percentile).`;
const dims = [...new Set(D.segments.map((r) => r.dimension))];
$("#dimension").innerHTML = dims
  .map((s) => `<option>${esc(s)}</option>`)
  .join("");
$("#dimension").value = "Driver age";
let visible = [];
function update() {
  const metric = $("#metric").value;
  visible = D.segments
    .filter(
      (r) =>
        r.dimension === $("#dimension").value &&
        r.exposure >= Number($("#minimum").value),
    )
    .sort((a, b) => (b[metric] ?? -1) - (a[metric] ?? -1));
  bars(
    "#segment-chart",
    visible.map((r) => ({
      label: r.segment,
      value: (r[metric] ?? 0) * (metric === "frequency" ? 100 : 1),
      digits: 2,
    })),
  );
  table(
    "#segment-table",
    [
      "Segment",
      "Policies",
      "Policy-years",
      "Reported claims",
      "Claims / 100 years",
      "95% interval / 100",
      "Recorded cost / year",
      "Mean record",
      "Volume",
    ],
    visible.map((r) => [
      r.segment,
      N(r.policies),
      N(r.exposure, 1),
      N(r.reported_claims),
      N(r.frequency * 100, 2),
      `${N(r.frequency_lower * 100, 2)}–${N(r.frequency_upper * 100, 2)}`,
      N(r.recorded_cost_per_year, 2),
      r.mean_recorded_claim === null ? "—" : N(r.mean_recorded_claim, 2),
      r.small_segment ? "Small sample" : "Standard",
    ]),
  );
  if (!visible.length)
    $("#segment-chart").textContent =
      "No segments meet this exposure threshold.";
}
["dimension", "metric", "minimum"].forEach((id) =>
  $("#" + id).addEventListener("change", update),
);
update();
$("#download").addEventListener("click", () => {
  const keys = [
    "dimension",
    "segment",
    "policies",
    "exposure",
    "reported_claims",
    "recorded_claims",
    "recorded_amount",
    "frequency",
    "frequency_lower",
    "frequency_upper",
    "recorded_cost_per_year",
    "mean_recorded_claim",
  ];
  const quote = (v) => '"' + String(v ?? "").replace(/"/g, '""') + '"';
  const csv = [keys, ...visible.map((r) => keys.map((k) => r[k]))]
    .map((row) => row.map(quote).join(","))
    .join("\r\n");
  const url = URL.createObjectURL(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = "claimscope-segments.csv";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
cards("#quality-cards", [
  ["Contracts passed", N(D.quality.length), "Blocking data and SQL checks"],
  [
    "Count exceptions",
    N(T.mismatch_policies),
    "Policies retained and disclosed",
  ],
  [
    "Orphan records",
    N(T.orphan_records),
    N(T.orphan_amount, 2) + " unlinked amount",
  ],
  ["Exposure > 1 year", N(T.exposure_over_one), "Source values retained"],
]);
table(
  "#reconciliation-table",
  [
    "Policy reconciliation",
    "Policies",
    "Policy-years",
    "Reported claims",
    "Amount records",
    "Recorded amount",
  ],
  D.reconciliation.map((r) => [
    r.reconciliation_status,
    N(r.policies),
    N(r.exposure, 2),
    N(r.reported_claims),
    N(r.recorded_claims),
    N(r.recorded_amount, 2),
  ]),
);
$("#checks").innerHTML = D.quality
  .map(
    (r) => `<p><span class="pill">${esc(r.status)}</span> ${esc(r.check)}</p>`,
  )
  .join("");
$("#join-warning").textContent =
  `A direct raw join inflates exposure by ${N(T.naive_join_exposure_inflation_pct, 3)}% in this source. The build checks exposure, counts, and amounts independently.`;
cards("#model-cards", [
  [
    "Holdout policies",
    N(M.split_counts.test),
    "20% deterministic policy partition",
  ],
  [
    "Model deviance",
    N(M.test_deviance, 4),
    "Exposure-weighted; lower is better",
  ],
  [
    "Baseline deviance",
    N(M.baseline_test_deviance, 4),
    "Constant training frequency",
  ],
  [
    "Deviance improvement",
    N(M.deviance_improvement_pct, 2) + "%",
    "Relative to constant baseline",
  ],
]);
const maxcal = Math.max(
  ...D.calibration.flatMap((r) => [r.observed_rate, r.predicted_rate]),
);
$("#calibration").innerHTML = D.calibration
  .map(
    (r) =>
      `<div class="barrow"><span>Decile ${r.risk_decile}<br><small>${N(r.exposure)} years</small></span><div><div class="calbar"><div style="width:${(100 * r.observed_rate) / maxcal}%"></div></div><div class="calbar pred"><div style="width:${(100 * r.predicted_rate) / maxcal}%"></div></div></div><span>${N(r.observed_rate * 100, 1)} / ${N(r.predicted_rate * 100, 1)}</span></div>`,
  )
  .join("");
$("#model-details").innerHTML =
  `<p>Train: ${N(M.split_counts.train)} policies · Validation: ${N(M.split_counts.validation)} · Test: ${N(M.split_counts.test)}.</p><p>Three regularization strengths compared on validation deviance. Selected α = ${M.selected_alpha}; the model is not refit before final evaluation.</p><p>Holdout observed claims: ${N(M.test_observed_claims)}. Expected claims: ${N(M.test_expected_claims, 1)}.</p>`;
$("#source-version").textContent =
  "Pinned upstream commit: " +
  D.source.commit +
  ". SHA-256 checksums are recorded in data/sources.json.";

$("#hero-policies").textContent = N(T.policies);
$("#hero-coverage").textContent =
  N(T.source_claim_records) +
  " claim records · " +
  N(D.quality.length) +
  " reporting contracts";
$("#decision-findings").innerHTML = [
  [
    "01 / Concentration",
    N(100 * T.top_one_pct_amount_share, 1) +
      "% of recorded cost sits in the top 1% tail.",
    "Review large-claim influence alongside segment averages. Capped-cost scenarios are sensitivity checks, not realized savings.",
  ],
  [
    "02 / Comparison",
    D.standardization.supported_regions +
      " regions support the primary age adjustment.",
    "Compare each region against the same age mix and inspect unsupported populations before ranking.",
  ],
  [
    "03 / Benchmark",
    N(M.deviance_improvement_pct, 2) +
      "% lower held-out deviance than baseline.",
    "Check calibration and the no-bonus/malus sensitivity before drawing conclusions about usable predictors.",
  ],
]
  .map(
    ([i, h, p]) =>
      `<article class="finding"><span class="index">${esc(i)}</span><h3>${esc(h)}</h3><p>${esc(p)}</p></article>`,
  )
  .join("");
function regions() {
  const threshold = Number($("#region-support").value),
    metric = $("#region-sort").value;
  const rows = D.region_scenarios[String(threshold)];
  const supported = rows
    .filter((r) => r.supported)
    .sort((a, b) => b[metric] - a[metric]);
  const share = D.support_sensitivity.find(
    (r) => r.minimum_cell_exposure === threshold,
  );
  cards("#region-cards", [
    [
      "Supported regions",
      N(share.supported_regions) + " / " + N(share.total_regions),
      "Every reference age band meets threshold",
    ],
    [
      "Exposure covered",
      N(share.supported_exposure_share * 100, 1) + "%",
      "Coverage depends on support requirement",
    ],
    [
      "Reference age bands",
      N(Object.keys(share.reference_weights).length),
      "Full portfolio exposure weights",
    ],
    ["Minimum per age band", N(threshold), "Policy-years within each region"],
  ]);
  const max = Math.max(
    ...supported.flatMap((r) => [r.crude_rate, r.standardized_rate]),
    0.01,
  );
  $("#region-chart").innerHTML =
    supported
      .map(
        (r) =>
          `<div class="region-row"><span>${esc(r.region)}</span><div class="dual-track"><i style="width:${(100 * r.crude_rate) / max}%"></i><i class="adjusted" style="width:${(100 * r.standardized_rate) / max}%"></i></div><span>${N(r.crude_rate * 100, 2)} / ${N(r.standardized_rate * 100, 2)}</span></div>`,
      )
      .join("") || "<p>No regions meet this support requirement.</p>";
  const all = [...supported, ...rows.filter((r) => !r.supported)];
  table(
    "#region-table",
    [
      "Region",
      "Policy-years",
      "Crude / 100",
      "Adjusted / 100",
      "95% adjusted interval",
      "Crude rank",
      "Adjusted rank",
      "Support",
    ],
    all.map((r) => [
      r.region,
      N(r.exposure),
      N(r.crude_rate * 100, 2),
      r.supported ? N(r.standardized_rate * 100, 2) : "—",
      r.supported
        ? N(r.standardized_lower * 100, 2) +
          "–" +
          N(r.standardized_upper * 100, 2)
        : "—",
      r.supported ? N(r.crude_rank) : "—",
      r.supported ? N(r.standardized_rank) : "—",
      r.supported ? "Supported" : "Insufficient age-band exposure",
    ]),
  );
}
["region-sort", "region-support"].forEach((id) =>
  $("#" + id).addEventListener("change", regions),
);
regions();
table(
  "#ablation-table",
  ["Model", "Holdout deviance", "Improvement vs baseline", "Expected claims"],
  [
    [
      "Constant training rate",
      N(M.baseline_test_deviance, 4),
      "—",
      N(M.train_baseline_rate * M.test_exposure, 1),
    ],
    [
      "Original frequency model",
      N(M.test_deviance, 4),
      N(M.deviance_improvement_pct, 2) + "%",
      N(M.test_expected_claims, 1),
    ],
    [
      "Without bonus/malus",
      N(M.no_bonus_test_deviance, 4),
      N(M.no_bonus_improvement_pct, 2) + "%",
      N(M.no_bonus_test_expected_claims, 1),
    ],
  ],
);
$("#model-uncertainty").textContent =
  "Original model improvement: 95% paired policy bootstrap interval " +
  N(M.improvement_interval_pct[0], 2) +
  "%–" +
  N(M.improvement_interval_pct[1], 2) +
  "% (400 resamples). This conditions on the frozen fitted model; it excludes training and future-population uncertainty.";

// Segment bootstrap view: all values are generated from the audited policy mart.
$("#robust-dimension").innerHTML = dims
  .map((v) => `<option>${esc(v)}</option>`)
  .join("");
$("#robust-dimension").value = "Driver age";
function updateRobustness() {
  const dimension = $("#robust-dimension").value,
    frequency = $("#robust-metric").value === "frequency";
  const key = frequency ? "frequency" : "cost_per_year",
    scale = frequency ? 100 : 1;
  const lo = frequency ? "frequency_bootstrap_lower" : "cost_bootstrap_lower",
    hi = frequency ? "frequency_bootstrap_upper" : "cost_bootstrap_upper";
  const rows = D.segment_robustness
    .filter((r) => r.dimension === dimension)
    .sort((a, b) => b[key] - a[key]);
  const eligible = rows.filter((r) => r.ranking_eligible);
  const movers = eligible.filter(
    (r) => r.cost_rank !== r.capped_cost_rank,
  ).length;
  cards("#robust-cards", [
    [
      "Eligible for cost ranking",
      N(eligible.length) + " / " + N(rows.length),
      "Exposure and claim-count requirements",
    ],
    [
      "Ranks changed by cap",
      N(movers),
      "Within eligible segments; same exposure",
    ],
    [
      "Largest policy share",
      N(100 * Math.max(...rows.map((r) => r.largest_policy_amount_share)), 1) +
        "%",
      "Maximum among segments in this view",
    ],
    [
      "Policy resamples",
      N(D.robustness_protocol.repetitions),
      "Paired frequency, cost and exposure",
    ],
  ]);
  const max = Math.max(...rows.flatMap((r) => [r[hi] * scale, r[key] * scale]), 0.01);
  $("#robust-chart").innerHTML = rows
    .map(
      (r) =>
        `<div class="interval-row"><span>${esc(r.segment)}</span><div class="interval-track" aria-hidden="true"><span class="range" style="left:${(100 * r[lo] * scale) / max}%;width:${(100 * (r[hi] - r[lo]) * scale) / max}%"></span><span class="estimate" style="left:${(100 * r[key] * scale) / max}%"></span></div><b>${N(r[key] * scale, 2)}<br><small>${N(r[lo] * scale, 2)}–${N(r[hi] * scale, 2)}</small></b></div>`,
    )
    .join("");
  $("#robust-axis").innerHTML =
    `<span>0</span><span>${N(max / 2, 1)}</span><span>${N(max, 1)}</span>`;
  table(
    "#robust-table",
    [
      "Segment",
      "Policy-years",
      "Frequency / 100",
      "95% bootstrap / 100",
      "Recorded cost / year",
      "95% cost interval",
      "Original cost rank",
      "Capped cost rank",
      "Top-quartile resample share",
      "Largest policy share",
    ],
    rows.map((r) => [
      r.segment,
      N(r.exposure),
      N(r.frequency * 100, 2),
      N(r.frequency_bootstrap_lower * 100, 2) +
        "–" +
        N(r.frequency_bootstrap_upper * 100, 2),
      N(r.cost_per_year, 2),
      N(r.cost_bootstrap_lower, 2) + "–" + N(r.cost_bootstrap_upper, 2),
      r.ranking_eligible ? N(r.cost_rank) : "Not eligible",
      r.ranking_eligible ? N(r.capped_cost_rank) : "Not eligible",
      r.ranking_eligible
        ? N(r.cost_top_quartile_resample_share * 100, 1) + "%"
        : "—",
      N(r.largest_policy_amount_share * 100, 1) + "%",
    ]),
  );
}
["robust-dimension", "robust-metric"].forEach((id) =>
  $("#" + id).addEventListener("change", updateRobustness),
);
updateRobustness();
function restoreView() {
  const tab = tabs.find((b) => "#" + b.dataset.tab === location.hash);
  if (tab) activate(tab);
}
window.addEventListener("hashchange", restoreView);
restoreView();
