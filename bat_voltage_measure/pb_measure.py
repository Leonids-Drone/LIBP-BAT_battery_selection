import requests
import pyvisa

PB_URL = "http://127.0.0.1:8090"
SUPERUSER_EMAIL = "Kelvin.Ziqi.Zhao@outlook.com"
SUPERUSER_PASSWORD = "tzr!tez4bwm*UWF7mpd"

COLLECTION = "measurements"
RESOURCE = "USB0::0x2A8D::0x1601::MY60089648::0::INSTR"

START_CELL_ID = 1
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
    data = resp.json()
    return data["token"]


def create_record(token: str, battery_cell_id: int, voltage_v: float, ir_mohm: float | None = None) -> dict:
    url = f"{PB_URL}/api/collections/{COLLECTION}/records"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }

    payload = {
        "name": f"cell_{battery_cell_id:02d}",
        "battery_cell_id": battery_cell_id,
        "voltage_v": voltage_v,
    }

    if ir_mohm is not None:
        payload["ir_mohm"] = ir_mohm

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def measure_voltage(inst) -> float:
    return float(inst.query("MEAS:VOLT:DC?"))


def main():
    print("Hello from bat-voltage-measure!")

    token = auth_superuser()
    print("PocketBase auth OK")

    rm = pyvisa.ResourceManager()
    print("Resources:", rm.list_resources())

    inst = rm.open_resource(RESOURCE)
    inst.timeout = 5000

    try:
        print("IDN:", inst.query("*IDN?").strip())

        battery_cell_id = START_CELL_ID

        while battery_cell_id <= END_CELL_ID:
            cmd = input(
                f"\nPress Enter to measure cell {battery_cell_id}, "
                f"or type 'q' to quit: "
            ).strip().lower()

            if cmd == "q":
                print("Stopped by user.")
                break

            try:
                voltage = measure_voltage(inst)
                print(f"Cell {battery_cell_id}: {voltage:.10f} V")

                record = create_record(
                    token=token,
                    battery_cell_id=battery_cell_id,
                    voltage_v=voltage,
                    ir_mohm=None,  # 以后有内阻仪再填
                )

                print("Created record successfully:")
                print(record)

                battery_cell_id += 1

            except requests.HTTPError as e:
                print("HTTP error:", e)
                if e.response is not None:
                    print("Response body:", e.response.text)

            except Exception as e:
                print("Measurement/write error:", e)

        print(f"\nFinished. Next battery_cell_id would be: {battery_cell_id}")

    finally:
        inst.close()
        rm.close()


if __name__ == "__main__":
    main()