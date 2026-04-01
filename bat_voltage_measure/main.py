'''
def main():
    print("Hello from bat-voltage-measure!")


if __name__ == "__main__":
    main()
'''

import pyvisa
RESOURCE = "USB0::0x2A8D::0x1601::MY60089648::0::INSTR"

def main():
    rm = pyvisa.ResourceManager()
    print("Resources:", rm.list_resources())

    inst = rm.open_resource(RESOURCE)
    inst.timeout = 5000

    try:
        print("IDN:", inst.query("*IDN?").strip())
        voltage = float(inst.query("MEAS:VOLT:DC?"))
        print(f"DC Voltage = {voltage:.8f} V")
    finally:
        inst.close()
        rm.close()

if __name__ == "__main__":
    main()
