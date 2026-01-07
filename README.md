# 🖥️ PC Power Control: The Complete Setup Guide

**Control your Windows PC from your phone via Raspberry Pi & Tailscale.**

## 📑 1. Prerequisites

Ensure you have the following ready:

* **Raspberry Pi** with Raspberry Pi OS installed.
* **Tailscale** installed and active on both the Pi and the Windows PC.
* **Windows PC** connected via **Ethernet** (Highly recommended for Wake-on-LAN stability).
* **Python tool `uv**` installed on the Pi.

---

## 🛠️ 2. BIOS/UEFI Configuration (The Foundation)

Before the software can wake the PC, the motherboard hardware must be told to listen for the "Magic Packet" while asleep.

1. **Enter BIOS:** Restart your PC and repeatedly tap **Del**, **F2**, or **F12** (depending on your motherboard).
2. **Enable WoL Settings:** Look for a section named **Advanced**, **Power Management**, or **ACPI**. You are looking for settings like:
* **Wake on LAN** → `Enabled`
* **Power On By PCI-E/PCI** → `Enabled`
* **Resume by LAN** → `Enabled`
* **ErP Ready** → `Disabled` (ErP cuts power too deeply for WoL to work).


3. **Save and Exit:** Usually **F10**.

---

## 🛠️ 3. Raspberry Pi Setup (The Server)

### A. Clone the Project

Navigate to your home directory and pull your code directly from GitHub:

```bash
git clone https://github.com/FadhelHaidar/pc-power-app
cd pc-power-app

```

### B. Install System Dependencies

The backend requires these utilities to send magic packets and handle SSH passwords:

```bash
sudo apt update
sudo apt install wakeonlan sshpass -y

```

### C. Set Up Python Environment (uv)

Create the virtual environment and install the required Python libraries:

```bash
uv venv
uv pip install flask python-dotenv

```

### D. Configure Environment Variables

Create the `.env` file to store your credentials:

```bash
nano .env

```

Paste and edit the following:

```text
PC_MAC=AA:BB:CC:DD:EE:FF      # Your PC's Ethernet MAC Address
PC_IP=100.XX.XXX.XXX          # Your PC's Tailscale IP
PC_USER=username                # Your Windows Username
DEV_MODE=False                # Set to False for real operation

```

### E. Deploy as a System Service (Systemd)

To make the app run 24/7 and start on boot:

```bash
sudo nano /etc/systemd/system/pc-power.service

```

Paste this configuration:

```ini
[Unit]
Description=PC Power Control PWA (uv)
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/pc-power-app
ExecStart=/home/pi/pc-power-app/.venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

```

**Activate it:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pc-power.service

```

---

## 🏁 4. Windows PC Configuration (The Target)

### A. Enable OpenSSH Server

Open **PowerShell (Admin)** and run:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

```

### B. Crucial Windows Settings

1. **Disable Fast Startup:** (Control Panel > Power Options > Choose what power buttons do > Uncheck "Fast Startup").
2. **Enable WoL in Device Manager:** (Network Adapters > Properties > Power Management > Check "Allow this device to wake the computer").
3. **Allow Remote Shutdown:** Run `secpol.msc` > Local Policies > User Rights Assignment > Add your user to **"Force shutdown from a remote system"**.

### C. The "First Handshake" (Don't skip!)

You **must** manually connect from the Pi once to save the PC's identity.

```bash
ssh username@100.XX.XXX.XXX  

```

* Type **`yes`** when asked about the fingerprint.
* Log in with your **Microsoft Account Password** (Not your PIN).
* Type `exit` once successful.

---

## 📱 5. Mobile Access & PWA

1. Connect your phone to **Tailscale**.
2. Open your browser to `http://100.x.x.x:5000` (Your Pi's Tailscale IP).
3. **Install as App:**
* **iOS:** Share Icon > "Add to Home Screen".
* **Android:** Menu (⋮) > "Install App".



---

## 🔍 6. Useful Management Commands

| Action | Command |
| --- | --- |
| **Check if App is Running** | `sudo systemctl status pc-power.service` |
| **Restart App** (after code changes) | `sudo systemctl restart pc-power.service` |
| **View Live Logs** (for debugging) | `journalctl -u pc-power.service -f` |
| **Test Wake-on-LAN manually** | `wakeonlan [YOUR_MAC_ADDRESS]` |
| **Check Port 22 (SSH) status** | `nc -zv 100.x.x.x 22` |

---

### ⚠️ Troubleshooting "Permission Denied"

If the shutdown button still asks for a password even with the right one:

1. On Windows, check `C:\ProgramData\ssh\sshd_config`.
2. Scroll to the bottom and comment out (`#`) the `Match Group administrators` block.
3. Restart the OpenSSH service in Windows `services.msc`.
