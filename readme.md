# 🖥️ Proxmox Manager (Dark-Themed GUI)

A **dark-themed** Python **Proxmox Manager** built with **PyQt6** for managing VMs, storage, networking, monitoring, and more. This project features:

## 🚀 Features
- **VM Management** (Start, Stop, Restart, Delete, Clone, etc.)
- **Create VMs** (with CPU, RAM, Disk, and ISO selection)
- **Live Monitoring** (CPU, Memory, Disk, Network)
- **Performance Metrics** (with interactive graphs)
- **VNC Console** (Built-in noVNC support)
- **Storage Management** (List, Upload ISOs, Manage Disks)
- **Network Management** (List network interfaces)
- **Logs Viewer** (with filtering)
- **LXC Container Management**
- **Snapshots** (Create, Restore, Delete)
- **Backup Management** (Backup and Restore VMs)
- **User Management** (List, Create Users)
- **Firewall Configuration** (Rules, IP Sets, Options)
- **Replication, Pools, High Availability (HA)**
- **Dark Mode UI** (modern dark theme with sidebar navigation)

---

## 📥 Installation

### 🔧 **Step 1: Clone the Repository**
```bash
git clone https://github.com/YOUR_USERNAME/proxmox-manager.git
cd proxmox-manager
```

📦 Step 2: Install Dependencies
Use pip to install the required dependencies:
```bash
pip install -r requirements.txt
```

▶️ Usage
Simply run the main script:

```bash
python main.py
```

This will launch the Proxmox Manager UI.

🛠️ Requirements
- Python 3.9+ (recommended)
- Proxmox VE 6+
- Dependencies (see requirements.txt)

📝 TODO / Future Features
- Add authentication/login system
- Improve VNC integration
- Add export/import VM functionality
- Implement Ceph storage graphs

🤝 Contributing
- Fork this repository 🍴
- Create a branch: git checkout -b feature-name
- Commit your changes: git commit -m "Add some feature"
- Push to the branch: git push origin feature-name
- Submit a Pull Request ✅

📜 License
- This project is licensed under the MIT License.

💬 Support
- If you find an issue, please open a GitHub issue.

🔥 Star this repo if you find it useful! ⭐

### 📄 **requirements.txt**
```yaml
Save this as `requirements.txt` in your project directory.

proxmoxer requests PyQt6 PyQt6-WebEngine
```

## ✅ **How to Use**
1. **Upload** `README.md` and `requirements.txt` to your GitHub repository.
2. **Replace** `"YOUR_USERNAME"` in the README with your actual GitHub username.
3. **Add Screenshots** by uploading images and linking them in the **"Screenshots"** section.
4. **Push your changes**:
   ```bash
   git add README.md requirements.txt
   git commit -m "Add README and requirements"
   git push origin main
```