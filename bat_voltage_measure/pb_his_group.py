import requests
import matplotlib.pyplot as plt

PB_URL = "http://127.0.0.1:8090"
SUPERUSER_EMAIL = "Kelvin.Ziqi.Zhao@outlook.com"
SUPERUSER_PASSWORD = "tzr!tez4bwm*UWF7mpd"

COLLECTION = "measurements"
TEST_NUM = 2
GROUP_SIZE = 20


def auth_superuser() -> str:
    url = f"{PB_URL}/api/collections/_superusers/auth-with-password"
    resp = requests.post(
        url,
        json={
            "identity": SUPERUSER_EMAIL,
            "password": SUPERUSER_PASSWORD,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def fetch_all_records(token: str) -> list[dict]:
    url = f"{PB_URL}/api/collections/{COLLECTION}/records"
    headers = {
        "Authorization": token,
    }

    page = 1
    per_page = 200
    all_items = []

    while True:
        resp = requests.get(
            url,
            headers=headers,
            params={
                "page": page,
                "perPage": per_page,
                "sort": "sn_num",
                "filter": f"test_num={TEST_NUM}",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        all_items.extend(items)

        total_pages = data.get("totalPages", 1)
        if page >= total_pages:
            break
        page += 1

    return all_items


def extract_valid_records(records: list[dict]) -> list[dict]:
    valid = []
    for record in records:
        try:
            sn_num = int(record.get("sn_num"))
            voltage = float(record.get("voltage_v"))
        except (TypeError, ValueError):
            continue

        valid.append({
            "sn_num": sn_num,
            "voltage_v": voltage,
        })

    valid.sort(key=lambda x: x["sn_num"])
    return valid


def group_records_by_20(records: list[dict]) -> dict[int, list[dict]]:
    groups = {}
    for record in records:
        sn_num = record["sn_num"]
        group_idx = (sn_num - 1) // GROUP_SIZE
        groups.setdefault(group_idx, []).append(record)
    return groups


def compute_group_deltas(records: list[dict]) -> tuple[list[dict], dict[int, float]]:
    groups = group_records_by_20(records)

    group_avgs = {}
    delta_records = []

    for group_idx in sorted(groups.keys()):
        group = groups[group_idx]
        avg_v = sum(r["voltage_v"] for r in group) / len(group)
        group_avgs[group_idx] = avg_v

        for r in group:
            delta_records.append({
                "sn_num": r["sn_num"],
                "voltage_v": r["voltage_v"],
                "group_idx": group_idx,
                "delta_v": r["voltage_v"] - avg_v,
            })

    delta_records.sort(key=lambda x: x["sn_num"])
    return delta_records, group_avgs


def main():
    token = auth_superuser()
    records = fetch_all_records(token)
    valid_records = extract_valid_records(records)

    if not valid_records:
        print("No valid voltage data found.")
        return

    delta_records, group_avgs = compute_group_deltas(valid_records)

    print(f"Loaded {len(valid_records)} valid voltage records.\n")

    for group_idx in sorted(group_avgs.keys()):
        start_sn = group_idx * GROUP_SIZE + 1
        end_sn = (group_idx + 1) * GROUP_SIZE
        print(
            f"Group {group_idx + 1} ({start_sn:04d}-{end_sn:04d}) "
            f"average = {group_avgs[group_idx]:.6f} V"
        )

    sn_nums = [r["sn_num"] for r in delta_records]
    deltas = [r["delta_v"] for r in delta_records]

    plt.figure(figsize=(10, 5))
    plt.plot(sn_nums, deltas, marker="o")
    plt.axhline(0, linestyle="--")
    plt.xlabel("Cell Number")
    plt.ylabel("Voltage - Group Average (V)")
    plt.title(f"Cell Voltage Deviation from 20-Cell Group Average (test_num={TEST_NUM})")
    plt.grid(True)
    

    plt.figure(figsize=(10, 5))
    plt.hist(deltas, bins=20)
    plt.xlabel("Voltage (V)")
    plt.ylabel("Count")
    plt.title("Battery Cell Voltage Histogram")
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()