import requests
import matplotlib.pyplot as plt
import numpy as np

PB_URL = "http://127.0.0.1:8090"
SUPERUSER_EMAIL = "Kelvin.Ziqi.Zhao@outlook.com"
SUPERUSER_PASSWORD = "tzr!tez4bwm*UWF7mpd"
COLLECTION = "measurements"

TEST_NUM_1 = 0
TEST_NUM_2 = 1


def auth_superuser() -> str:
    resp = requests.post(
        f"{PB_URL}/api/collections/_superusers/auth-with-password",
        json={
            "identity": SUPERUSER_EMAIL,
            "password": SUPERUSER_PASSWORD,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def fetch_records_by_test_num(token: str, test_num: int) -> list[dict]:
    records = []
    page = 1

    while True:
        resp = requests.get(
            f"{PB_URL}/api/collections/{COLLECTION}/records",
            headers={"Authorization": token},
            params={
                "page": page,
                "perPage": 200,
                "filter": f"test_num={test_num}",
            },
            timeout=10,
        )

        if not resp.ok:
            print("Status:", resp.status_code)
            print("Body:", resp.text)
            resp.raise_for_status()

        data = resp.json()
        records.extend(data.get("items", []))

        if page >= data.get("totalPages", 1):
            break
        page += 1

    return records


def build_sn_map(records: list[dict]) -> dict[str, dict]:
    result = {}
    for r in records:
        sn = r.get("sn")
        v = r.get("voltage_v")
        if sn is None or v is None:
            continue

        try:
            result[str(sn)] = {
                "sn": str(sn),
                "battery_cell_id": r.get("battery_cell_id"),
                "voltage_v": float(v),
            }
        except (TypeError, ValueError):
            pass

    return result


def build_delta_rows(records_1: list[dict], records_2: list[dict]) -> list[dict]:
    map1 = build_sn_map(records_1)
    map2 = build_sn_map(records_2)

    common_sns = sorted(set(map1.keys()) & set(map2.keys()))
    rows = []

    for sn in common_sns:
        r1 = map1[sn]
        r2 = map2[sn]

        v1 = r1["voltage_v"]
        v2 = r2["voltage_v"]
        delta_v = v2 - v1
        mean_v = (v1 + v2) / 2.0

        rows.append({
            "sn": sn,
            "battery_cell_id": r1.get("battery_cell_id") or r2.get("battery_cell_id"),
            "v1": v1,
            "v2": v2,
            "mean_v": mean_v,
            "delta_v": delta_v,
        })

    return rows


def print_summary(rows: list[dict]) -> None:
    if not rows:
        print("No matched rows.")
        return

    v1 = np.array([r["v1"] for r in rows], dtype=float)
    v2 = np.array([r["v2"] for r in rows], dtype=float)
    dv = np.array([r["delta_v"] for r in rows], dtype=float)
    mv = np.array([r["mean_v"] for r in rows], dtype=float)

    print(f"Matched cells: {len(rows)}")
    print(f"Test1 mean:    {np.mean(v1):.6f} V")
    print(f"Test2 mean:    {np.mean(v2):.6f} V")
    print(f"Delta mean:    {np.mean(dv):.6f} V")
    print(f"Delta std:     {np.std(dv):.6f} V")

    corr_v1_dv = np.corrcoef(v1, dv)[0, 1] if len(rows) > 1 else np.nan
    corr_mv_dv = np.corrcoef(mv, dv)[0, 1] if len(rows) > 1 else np.nan

    print(f"Corr(v1, delta_v):      {corr_v1_dv:.4f}")
    print(f"Corr(mean_v, delta_v):  {corr_mv_dv:.4f}")


def plot_voltage_vs_delta(rows: list[dict]) -> None:
    if not rows:
        print("No matched rows to plot.")
        return

    rows_by_cell = sorted(
        rows,
        key=lambda x: (
            x["battery_cell_id"] is None,
            x["battery_cell_id"] if x["battery_cell_id"] is not None else 10**9
        )
    )

    cell_ids = []
    v1 = []
    v2 = []
    mean_v = []
    delta_v = []

    for i, r in enumerate(rows_by_cell):
        cid = r["battery_cell_id"]
        if cid is None:
            cid = i + 1
        cell_ids.append(int(cid))
        v1.append(float(r["v1"]))
        v2.append(float(r["v2"]))
        mean_v.append(float(r["mean_v"]))
        delta_v.append(float(r["delta_v"]))

    v1_np = np.array(v1)
    v2_np = np.array(v2)
    mean_v_np = np.array(mean_v)
    delta_v_np = np.array(delta_v)

    corr_v1_dv = np.corrcoef(v1_np, delta_v_np)[0, 1] if len(v1_np) > 1 else np.nan
    corr_v2_dv = np.corrcoef(v2_np, delta_v_np)[0, 1] if len(v2_np) > 1 else np.nan
    corr_mv_dv = np.corrcoef(mean_v_np, delta_v_np)[0, 1] if len(mean_v_np) > 1 else np.nan

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    # 1. v1 vs delta_v
    axs[0, 0].scatter(v1_np, delta_v_np)
    axs[0, 0].axhline(0, linestyle="--")
    axs[0, 0].set_xlabel(f"Voltage at Test {TEST_NUM_1} (V)")
    axs[0, 0].set_ylabel(f"Delta Voltage (Test {TEST_NUM_2} - Test {TEST_NUM_1}) (V)")
    axs[0, 0].set_title(f"v1 vs delta_v   corr={corr_v1_dv:.3f}")
    axs[0, 0].grid(True)

    # 2. mean_v vs delta_v
    axs[0, 1].scatter(mean_v_np, delta_v_np)
    axs[0, 1].axhline(0, linestyle="--")
    axs[0, 1].set_xlabel("Mean Voltage of Two Tests (V)")
    axs[0, 1].set_ylabel("Delta Voltage (V)")
    axs[0, 1].set_title(f"mean_v vs delta_v   corr={corr_mv_dv:.3f}")
    axs[0, 1].grid(True)

    # 3. delta_v vs cell id
    axs[1, 0].plot(cell_ids, delta_v_np, marker="o")
    axs[1, 0].axhline(0, linestyle="--")
    axs[1, 0].set_xlabel("Battery Cell ID")
    axs[1, 0].set_ylabel("Delta Voltage (V)")
    axs[1, 0].set_title("delta_v vs cell id")
    axs[1, 0].grid(True)

    # 4. sort by v1 and plot delta_v
    pairs = sorted(zip(v1_np, delta_v_np), key=lambda x: x[0])
    sorted_v1 = [p[0] for p in pairs]
    sorted_dv = [p[1] for p in pairs]

    axs[1, 1].plot(sorted_v1, sorted_dv, marker="o")
    axs[1, 1].axhline(0, linestyle="--")
    axs[1, 1].set_xlabel(f"Sorted Voltage at Test {TEST_NUM_1} (V)")
    axs[1, 1].set_ylabel("Delta Voltage (V)")
    axs[1, 1].set_title("delta_v after sorting by v1")
    axs[1, 1].grid(True)

    fig.suptitle(
        f"Relationship Between Cell Voltage and Voltage Difference\n"
        f"delta_v = test {TEST_NUM_2} - test {TEST_NUM_1}",
        fontsize=14
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


def main():
    token = auth_superuser()

    records_1 = fetch_records_by_test_num(token, TEST_NUM_1)
    records_2 = fetch_records_by_test_num(token, TEST_NUM_2)

    print(f"Loaded test {TEST_NUM_1}: {len(records_1)} records")
    print(f"Loaded test {TEST_NUM_2}: {len(records_2)} records")

    rows = build_delta_rows(records_1, records_2)
    print_summary(rows)
    plot_voltage_vs_delta(rows)


if __name__ == "__main__":
    main()