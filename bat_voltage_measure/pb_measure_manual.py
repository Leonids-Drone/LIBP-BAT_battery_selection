import requests

PB_URL = "http://127.0.0.1:8090"
SUPERUSER_EMAIL = "Kelvin.Ziqi.Zhao@outlook.com"
SUPERUSER_PASSWORD = "tzr!tez4bwm*UWF7mpd"

COLLECTION = "measurements"

START_CELL_ID = 20
END_CELL_ID = 80


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


def create_record(token: str, battery_cell_id: int, voltage_v: float) -> dict:
    url = f"{PB_URL}/api/collections/{COLLECTION}/records"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }

    sn = f"LIBP-BAT-{battery_cell_id:04d}"

    payload = {
        "sn": sn,
        "sn_num": battery_cell_id,
        "battery_cell_id": battery_cell_id,
        "voltage_v": voltage_v,
        "test_num": 2,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def input_voltage_for_cell(battery_cell_id: int) -> float | None:
    sn = f"LIBP-BAT-{battery_cell_id:04d}"

    while True:
        raw = input(
            f"\n请输入 cell {battery_cell_id} ({sn}) 的电压值，"
            f"输入 q 退出: "
        ).strip()

        if raw.lower() == "q":
            return None

        if not raw:
            print("输入为空，请重新输入。")
            continue

        # 允许输入类似 3.7123V / 3.7123 v
        raw = raw.replace("V", "").replace("v", "").strip()

        try:
            voltage = float(raw)
        except ValueError:
            print("输入不是有效数字，请重新输入。")
            continue

        if voltage < 0:
            print("电压不能为负数，请重新输入。")
            continue

        return voltage


def main():
    print("Hello from bat-voltage-manual-input!")

    token = auth_superuser()
    print("PocketBase auth OK")

    battery_cell_id = START_CELL_ID

    while battery_cell_id <= END_CELL_ID:
        try:
            voltage = input_voltage_for_cell(battery_cell_id)

            if voltage is None:
                print("Stopped by user.")
                break

            sn = f"LIBP-BAT-{battery_cell_id:04d}"
            print(f"Cell {battery_cell_id} [{sn}] input voltage: {voltage:.10f} V")

            record = create_record(
                token=token,
                battery_cell_id=battery_cell_id,
                voltage_v=voltage,
            )

            print("Created record successfully:")
            print(record)

            battery_cell_id += 1

        except requests.HTTPError as e:
            print("HTTP error:", e)
            if e.response is not None:
                print("Response body:", e.response.text)

        except Exception as e:
            print("Write error:", e)

    print(f"\nFinished. Next battery_cell_id would be: {battery_cell_id}")


if __name__ == "__main__":
    main()