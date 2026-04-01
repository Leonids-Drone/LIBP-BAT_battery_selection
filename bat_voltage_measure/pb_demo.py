import requests

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
    data = resp.json()
    return data["token"]


def create_record(token: str) -> dict:
    url = f"{PB_URL}/api/collections/{COLLECTION}/records"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    payload = {
        "name": "cell_01",
        "voltage_v": 3.912,
        "ir_mohm": 12.4,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    try:
        token = auth_superuser()
        record = create_record(token)
        print("Created record successfully:")
        print(record)
    except requests.HTTPError as e:
        print("HTTP error:", e)
        if e.response is not None:
            print("Response body:", e.response.text)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()