"""
Where do Canadian K-12 students go to school? Public, private or home-school,
by province and territory, 2019/2020 (Statistics Canada, Table 37-10-0109-01).

Usage: python src/analysis.py Stats_Can_Dataset.csv reports
"""
import re, sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)

# The CSV is a formatted StatCan table: 3 header lines, data rows, then footnotes.
raw = pd.read_csv(SRC, skiprows=3, header=None, encoding="utf-8-sig",
                  names=["region", "public_n", "public_pct", "private_n", "private_pct", "home_n", "home_pct"])
raw = raw[pd.to_numeric(raw["public_n"], errors="coerce").notna()]  # keep data rows only
raw["region"] = raw["region"].str.replace(r"\{\d+\}", "", regex=True).str.strip()
num = lambda s: pd.to_numeric(s.replace({".": None, "...": None}), errors="coerce")
for c in raw.columns[1:]:
    raw[c] = num(raw[c])
df = raw.reset_index(drop=True)

canada = df[df.region == "Canada"].iloc[0]
prov = df[df.region != "Canada"].copy()
prov["total_n"] = prov[["public_n", "private_n", "home_n"]].sum(axis=1, min_count=1)
prov = prov.sort_values("public_pct")

summary = {
    "canada_students": int(canada[["public_n", "private_n", "home_n"]].sum()),
    "canada_public_pct": canada.public_pct, "canada_private_pct": canada.private_pct, "canada_home_pct": canada.home_pct,
    "highest_private": prov.loc[prov.private_pct.idxmax(), ["region", "private_pct"]].tolist(),
    "highest_home": prov.loc[prov.home_pct.idxmax(), ["region", "home_pct"]].tolist(),
    "ontario_share_of_private_students_pct": round(100 * prov.set_index("region").private_n["Ontario"] / canada.private_n, 1),
    "on_qc_bc_share_of_private_students_pct": round(100 * prov.set_index("region").private_n[["Ontario", "Quebec", "British Columbia"]].sum() / canada.private_n, 1),
}
prov.to_csv(OUT / "school_type_by_region.csv", index=False)
pd.Series(summary).to_json(OUT / "summary.json", indent=1)

# Chart: share of students outside public schools, by region
fig, ax = plt.subplots(figsize=(8, 5.5))
p = prov.sort_values("public_pct", ascending=False)
ax.barh(p.region, p.private_pct.fillna(0), color="#2a62f0", label="Private / independent")
ax.barh(p.region, p.home_pct.fillna(0), left=p.private_pct.fillna(0), color="#9db7f5", label="Home-schooling")
ax.axvline(100 - canada.public_pct, color="#16171a", ls="--", lw=1)
ax.text(100 - canada.public_pct + 0.2, len(p) - 0.45, f"Canada: {100 - canada.public_pct:.1f}%", fontsize=9)
ax.set_xlabel("% of K-12 students not in public schools, 2019/2020")
ax.set_title("Private and home-school enrolment by province and territory")
ax.legend(frameon=False, loc="lower right"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT / "non_public_share.png", dpi=150)
print(pd.Series(summary).to_string()); print(prov[["region", "public_pct", "private_pct", "home_pct"]].to_string(index=False))
