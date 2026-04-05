import requests
import matplotlib.pyplot as plt

PB_URL = "http://127.0.0.1:8090"
SUPERUSER_EMAIL = "Kelvin.Ziqi.Zhao@outlook.com"
SUPERUSER_PASSWORD = "tzr!tez4bwm*UWF7mpd"

COLLECTION = "measurements"


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
                "sort": "sn",
                "filter": "test_num=2",
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


def extract_voltages(records: list[dict]) -> list[float]:
    voltages = []
    for record in records:
        v = record.get("voltage_v")
        if v is None:
            continue
        try:
            voltages.append(float(v))
        except (TypeError, ValueError):
            pass
    return voltages


def main():
    token = auth_superuser()
    records = fetch_all_records(token)
    voltages = extract_voltages(records)

    if not voltages:
        print("No voltage data found.")
        return

    print(f"Loaded {len(voltages)} voltage records.")


    plt.figure(figsize=(8, 5))
    plt.hist(voltages, bins=40)
    plt.xlabel("Voltage (V)")
    plt.ylabel("Count")
    plt.title("Battery Cell Voltage Histogram")
    plt.grid(True)

    '''
    plt.figure(figsize=(10, 5))
    plt.plot(voltages, marker="o")
    plt.xlabel("Cell Index")
    plt.ylabel("Voltage (V)")
    plt.title("Cell Voltage Distribution")
    plt.grid(True)
    '''

    v_sorted = sorted(voltages)

    plt.figure(figsize=(8, 5))
    plt.plot(v_sorted, marker="o")
    plt.xlabel("Rank")
    plt.ylabel("Voltage (V)")
    plt.title("Sorted Cell Voltages")
    plt.grid(True)

    plt.figure(figsize=(4, 6))
    plt.boxplot(voltages)
    plt.title("Voltage Boxplot")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    
    plt.show()


if __name__ == "__main__":
    main()