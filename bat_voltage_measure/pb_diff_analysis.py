import requests
import matplotlib.pyplot as plt
import numpy as np

PB_URL = "http://127.0.0.1:8090"
SUPERUSER_EMAIL = "Kelvin.Ziqi.Zhao@outlook.com"
SUPERUSER_PASSWORD = "tzr!tez4bwm*UWF7mpd"
COLLECTION = "measurements"

TEST_NUM_1 = 1
TEST_NUM_2 = 2


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
                "test_num": r.get("test_num"),
                "raw": r,
            }
        except (TypeError, ValueError):
            pass

    return result


def build_delta_table(records_1: list[dict], records_2: list[dict]) -> list[dict]:
    map1 = build_sn_map(records_1)
    map2 = build_sn_map(records_2)

    common_sns = sorted(set(map1.keys()) & set(map2.keys()))

    delta_rows = []
    for sn in common_sns:
        r1 = map1[sn]
        r2 = map2[sn]

        delta_rows.append({
            "sn": sn,
            "battery_cell_id": r1.get("battery_cell_id") or r2.get("battery_cell_id"),
            "v1": r1["voltage_v"],
            "v2": r2["voltage_v"],
            "delta_v": r2["voltage_v"] - r1["voltage_v"],  # test2 - test1
        })

    return delta_rows


def print_summary(delta_rows: list[dict]) -> None:
    if not delta_rows:
        print("No overlapping SN records found.")
        return

    deltas = np.array([row["delta_v"] for row in delta_rows], dtype=float)

    print(f"Matched cells: {len(delta_rows)}")
    print(f"Mean delta: {np.mean(deltas):.6f} V")
    print(f"Std delta : {np.std(deltas):.6f} V")
    print(f"Min delta : {np.min(deltas):.6f} V")
    print(f"Max delta : {np.max(deltas):.6f} V")

    abs_sorted = sorted(delta_rows, key=lambda x: abs(x["delta_v"]), reverse=True)

    print("\nTop 10 largest absolute delta_v:")
    for row in abs_sorted[:10]:
        print(
            f'{row["sn"]}  '
            f'cell_id={row["battery_cell_id"]}  '
            f'v1={row["v1"]:.6f}  '
            f'v2={row["v2"]:.6f}  '
            f'delta={row["delta_v"]:+.6f} V'
        )


def plot_delta_analysis(delta_rows: list[dict]) -> None:
    if not delta_rows:
        print("No delta data to plot.")
        return

    rows_sorted_by_cell = sorted(
        delta_rows,
        key=lambda x: (
            x["battery_cell_id"] is None,
            x["battery_cell_id"] if x["battery_cell_id"] is not None else 10**9
        )
    )

    cell_ids = []
    delta_vs = []
    for i, row in enumerate(rows_sorted_by_cell):
        cid = row["battery_cell_id"]
        if cid is None:
            cid = i + 1
        cell_ids.append(int(cid))
        delta_vs.append(float(row["delta_v"]))

    delta_vs_np = np.array(delta_vs)
    mean_delta = np.mean(delta_vs_np)
    std_delta = np.std(delta_vs_np)

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    # 1. delta_v vs cell id
    axs[0, 0].plot(cell_ids, delta_vs, marker="o")
    axs[0, 0].axhline(mean_delta, linestyle="--")
    axs[0, 0].set_xlabel("Battery Cell ID")
    axs[0, 0].set_ylabel("Delta Voltage (V)")
    axs[0, 0].set_title("Delta Voltage vs Cell ID")
    axs[0, 0].grid(True)

    # 2. histogram
    axs[0, 1].hist(delta_vs, bins=20, edgecolor="black")
    axs[0, 1].set_xlabel("Delta Voltage (V)")
    axs[0, 1].set_ylabel("Count")
    axs[0, 1].set_title("Delta Voltage Histogram")
    axs[0, 1].grid(True)

    # 3. boxplot
    axs[1, 0].boxplot(delta_vs)
    axs[1, 0].set_ylabel("Delta Voltage (V)")
    axs[1, 0].set_title("Delta Voltage Boxplot")
    axs[1, 0].grid(True)

    # 4. sorted abs delta
    sorted_abs = sorted(abs(x) for x in delta_vs)
    axs[1, 1].plot(sorted_abs, marker="o")
    axs[1, 1].set_xlabel("Rank")
    axs[1, 1].set_ylabel("|Delta Voltage| (V)")
    axs[1, 1].set_title("Sorted Absolute Delta Voltage")
    axs[1, 1].grid(True)

    fig.suptitle(
        f"Voltage Difference Analysis: test {TEST_NUM_2} - test {TEST_NUM_1}\n"
        f"mean={mean_delta:.6f} V, std={std_delta:.6f} V",
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

    delta_rows = build_delta_table(records_1, records_2)

    print_summary(delta_rows)
    plot_delta_analysis(delta_rows)


if __name__ == "__main__":
    main()