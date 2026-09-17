#!/usr/bin/env python3
"""Check the cross-file 285/65 progression against Gravity's published EXP table.

Sources: https://ro.gnjoy.com/news/update/View.asp?seq=311
         https://ro.gnjoy.com/guide/ragstart/play3.asp
The source labels EXP by the level reached; rAthena labels it by the level left.
"""

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE_TO_REACH = {
    276: 437265708141,
    277: 443824693763,
    278: 450482064169,
    279: 457239295132,
    280: 464097884559,
    281: 468738863405,
    282: 473426252039,
    283: 478160514559,
    284: 482942119705,
    285: 487771540902,
}
JOB_TO_REACH = {
    61: 15898990559,
    62: 19158283624,
    63: 23085731766,
    64: 27818306778,
    65: 33521059668,
}
HOM_TO_REACH = {
    276: 43726570814,
    277: 44382469376,
    278: 45048206417,
    279: 45723929513,
    280: 46409788456,
    281: 46873886341,
    282: 47342625204,
    283: 47816051456,
    284: 48294211971,
    285: 48777154090,
}


def body(name: str) -> list[dict]:
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))["Body"]


def assert_setting(path: str, pattern: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    assert re.search(pattern, text, re.MULTILINE), f"{path}: missing {pattern}"


def main() -> None:
    groups = body("db/re/job_exp.yml")
    base = next(g for g in groups if g["Jobs"].get("Dragon_Knight") and "BaseExp" in g)
    job = next(g for g in groups if g["Jobs"].get("Dragon_Knight") and "JobExp" in g)
    assert base["MaxBaseLevel"] == 285 and job["MaxJobLevel"] == 65
    assert base["Jobs"] == job["Jobs"], "Base/Job caps must cover the same classes"
    assert [r["Level"] for r in base["BaseExp"]] == list(range(1, 286))
    assert [r["Level"] for r in job["JobExp"]] == list(range(1, 66))
    base_exp = {r["Level"]: r["Exp"] for r in base["BaseExp"]}
    job_exp = {r["Level"]: r["Exp"] for r in job["JobExp"]}
    for reached, exp in BASE_TO_REACH.items():
        assert base_exp[reached - 1] == exp, f"Base EXP to {reached}"
    for reached, exp in JOB_TO_REACH.items():
        assert job_exp[reached - 1] == exp, f"Job EXP to {reached}"
    assert base_exp[285] == 999999999999 and job_exp[65] == 99999999999

    hom_exp = {r["Level"]: r["Exp"] for r in body("db/re/exp_homun.yml")}
    assert max(hom_exp) == 284
    for reached, exp in HOM_TO_REACH.items():
        assert hom_exp[reached - 1] == exp, f"Homunculus EXP to {reached}"

    statpoints = {r["Level"]: r for r in body("db/re/statpoint.yml")}
    assert max(statpoints) == 285
    for level in range(276, 286):
        row = statpoints[level]
        assert row["Points"] == 4099
        # This is rAthena's existing trait point formula, extended to 285.
        assert row["TraitPoints"] == (level - 200) * 3 + ((level - 200) // 5) * 4

    ap = next(g for g in body("db/re/job_basepoints.yml") if g["Jobs"].get("Dragon_Knight"))
    ap_rows = {r["Level"]: r["Ap"] for r in ap["BaseAp"]}
    assert all(ap_rows[level] == 200 for level in range(200, 286))

    stats = body("db/re/job_stats.yml")
    for name in base["Jobs"]:
        matches = [g for g in stats if g["Jobs"].get(name)]
        assert len(matches) == 1, f"{name}: job stats group"
        assert any(r["Level"] >= 61 for r in matches[0].get("BonusStats", [])), (
            f"{name}: missing 61-65 job bonus"
        )

    assert_setting("src/map/map.hpp", r"^#define MAX_LEVEL 285$")
    assert_setting("conf/battle/player.conf", r"^max_trait_parameter: 120$")
    assert_setting("conf/battle/homunc.conf", r"^homunculus_S_max_level: 285$")
    print(f"285/65 progression: PASS ({len(base['Jobs'])} class keys)")


if __name__ == "__main__":
    main()
