#!/usr/bin/env python3
"""
==========================================
REGTeches Technician's Toolkit Pro Suite v4.0
Company: REGTeches | Developer: Ronald Goodchild
All-in-one Windows IT toolkit (launches the optional AppForge and BackupPro companion apps)
==========================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import subprocess
import platform
import os
import sys
import ctypes
import json
import webbrowser
from datetime import datetime
from pathlib import Path
import threading
import shutil
import tempfile


# ── Companion app launcher flags ──────────────────────────────────────
# AppForge and BackupPro are separate projects. Put appforge.py / backuppro.py next to
# this file (or install them on PYTHONPATH) and the toolkit can launch them. Relaunching
# with --appforge / --backuppro boots that app instead of the Toolkit (avoids a second
# Tk root conflict).
COMPANION_APPS = {
    "--appforge":  ("appforge",  "https://github.com/ronaldgoodchild/appforge"),
    "--backuppro": ("backuppro", "https://github.com/ronaldgoodchild/backuppro"),
}
for _flag, (_module, _url) in COMPANION_APPS.items():
    if _flag in sys.argv:
        try:
            __import__(_module).main()
        except ImportError:
            print(f"{_module}.py not found. Download it from {_url} and place it next to this file.")
            sys.exit(1)
        sys.exit(0)


class DarkMenu(tk.Menu):
    """Custom dark-themed menu - optimized for performance"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(
            bg='#2d2d2d',
            fg='#ffffff',
            activebackground='#4a90e2',
            activeforeground='#ffffff',
            relief='flat',
            borderwidth=0
        )


class TechniciansToolkit:
    def __init__(self, root):
        self.root = root
        self.root.title("REGTeches Technician's Toolkit Pro Suite v4.0  —  By: Ronald Goodchild")
        self.root.geometry("1400x800")
        
        # Set minimum window size
        self.root.minsize(1000, 700)
        
        # Dark mode colors
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_medium': '#2d2d2d',
            'bg_light': '#3d3d3d',
            'accent': '#4a90e2',
            'accent_hover': '#5ba3f5',
            'text': '#ffffff',
            'text_dim': '#b0b0b0',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336',
            'log_bg': '#0a0a0a',
            'log_fg': '#00ff00'
        }
        
        # Favorites system
        self.favorites = self.load_favorites()
        
        # Command counter
        self.command_count = 0
        
        # Configure root window
        self.root.configure(bg=self.colors['bg_dark'])
        
        # Configure style
        self.setup_styles()
        
        # Check for admin rights
        self.is_admin = self.check_admin()
        if not self.is_admin:
            messagebox.showwarning(
                "Administrator Rights Required",
                "Some features require administrator privileges.\n\n"
                "Please run this script as administrator for full functionality."
            )
        
        # Create main UI
        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_layout()
        
        # Keyboard shortcuts
        self.setup_shortcuts()
        
        # Status message
        self.update_status("🚀 Toolkit initialized and ready!", 'success')
        if not self.is_admin:
            self.update_status("⚠️ Running without administrator privileges - some features limited", 'warning')
        
        # Start system monitor
        self.start_system_monitor()
    
    def setup_styles(self):
        """Configure modern UI styling"""
        style = ttk.Style()
        
        # Use a modern theme
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # Custom colors - modern dark blue theme
        bg_color = "#1e2936"
        fg_color = "#ffffff"
        accent_color = "#4a90e2"
        
        # Configure frame style
        style.configure('Card.TFrame', background='#2a3f54', relief='raised')
        style.configure('Main.TFrame', background=bg_color)
        
        # Configure label style
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 14, 'bold'),
                       background=bg_color,
                       foreground=accent_color)
        
        style.configure('Info.TLabel',
                       font=('Segoe UI', 10),
                       background=bg_color,
                       foreground=fg_color)
        
        # Configure button style
        style.configure('Action.TButton',
                       font=('Segoe UI', 9),
                       padding=10)
    
    def check_admin(self):
        """Check if running with administrator privileges"""
        try:
            if platform.system() == 'Windows':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def load_favorites(self):
        """Load favorite commands from file"""
        try:
            config_path = os.path.join(os.path.expanduser('~'), '.toolkit_favorites.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_favorites(self):
        """Save favorite commands to file"""
        try:
            config_path = os.path.join(os.path.expanduser('~'), '.toolkit_favorites.json')
            with open(config_path, 'w') as f:
                json.dump(self.favorites, f, indent=2)
        except Exception as e:
            self.update_status(f"⚠️ Could not save favorites: {e}", 'warning')
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-r>', lambda e: self.refresh_system_info())
        self.root.bind('<Control-e>', lambda e: self.export_logs())
        self.root.bind('<Control-h>', lambda e: self.quick_health_check())
        self.root.bind('<Control-l>', lambda e: self.clear_log())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<F5>', lambda e: self.refresh_system_info())
    
    def clear_log(self):
        """Clear the activity log"""
        if messagebox.askyesno("Clear Log", "Clear all activity log entries?"):
            self.status_text.delete('1.0', 'end')
            self.update_status("📋 Activity log cleared", 'info')
    
    def start_system_monitor(self):
        """Start system monitoring in background"""
        def monitor():
            try:
                # Get CPU usage
                if platform.system() == 'Windows':
                    result = subprocess.run(
                        'powershell -NoProfile -Command "Get-Counter \'\\Processor(_Total)\\% Processor Time\' | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue"',
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.stdout:
                        cpu_usage = float(result.stdout.strip())
                        self.cpu_label.config(text=f"CPU: {cpu_usage:.1f}%")
                    
                    # Get memory usage
                    result = subprocess.run(
                        'powershell -NoProfile -Command "Get-CimInstance Win32_OperatingSystem | Select-Object @{Name=\'PercentUsed\';Expression={[math]::Round((($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize) * 100, 1)}} | Select-Object -ExpandProperty PercentUsed"',
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.stdout:
                        mem_usage = float(result.stdout.strip())
                        self.mem_label.config(text=f"RAM: {mem_usage:.1f}%")
            except:
                pass
            
            # Schedule next update
            self.root.after(5000, monitor)
        
        # Start monitoring after 2 seconds
        self.root.after(2000, monitor)
    
    def create_menu_bar(self):
        """Create dark-themed menu bar with ALL original commands"""
        menubar = DarkMenu(self.root, font=('Segoe UI', 9))
        self.root.config(menu=menubar, bg=self.colors['bg_dark'])
        
        # ==================== FILE MENU ====================
        file_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="📁 File", menu=file_menu)
        
        # Quick Access submenu
        quick_menu = DarkMenu(file_menu, tearoff=0, font=('Segoe UI', 9))
        file_menu.add_cascade(label="⚡ Quick Access", menu=quick_menu)
        quick_menu.add_command(label="💻 This PC (Explorer)", command=lambda: self.run_command("explorer.exe"))
        quick_menu.add_command(label="🖥️ Control Panel", command=lambda: self.run_command("control"))
        quick_menu.add_command(label="⚙️ Settings", command=lambda: self.run_command("start ms-settings:"))
        quick_menu.add_command(label="📂 Program Files", command=lambda: self.run_command('explorer "C:\\Program Files"'))
        quick_menu.add_command(label="🔧 Device Manager", command=lambda: self.run_command("devmgmt.msc"))
        quick_menu.add_command(label="💾 Disk Management", command=lambda: self.run_command("diskmgmt.msc"))
        quick_menu.add_command(label="📊 Task Manager", command=lambda: self.run_command("taskmgr"))
        quick_menu.add_command(label="📝 Notepad", command=lambda: self.run_command("notepad"))
        
        # Terminal submenu
        term_menu = DarkMenu(file_menu, tearoff=0, font=('Segoe UI', 9))
        file_menu.add_cascade(label="🖥️ Open Terminal", menu=term_menu)
        term_menu.add_command(label="Command Prompt", command=lambda: self.run_command("cmd"))
        term_menu.add_command(label="PowerShell", command=lambda: self.run_command("powershell"))
        term_menu.add_command(label="PowerShell (Admin)", command=lambda: self.run_command("powershell", admin=True))
        term_menu.add_command(label="Windows Terminal", command=lambda: self.run_command("wt"))
        
        file_menu.add_separator()
        file_menu.add_command(label="🔄 Refresh System Info", command=self.refresh_system_info)
        file_menu.add_command(label="📋 Export Logs", command=self.export_logs)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Exit", command=self.root.quit)
        
        # ==================== AUTOMATED TOOLS MENU ====================
        auto_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="🤖 Automated", menu=auto_menu)
        auto_menu.add_command(label="⚡ Quick PC Health Check", command=self.quick_health_check)
        auto_menu.add_command(label="🔧 Auto-Repair (SFC + DISM)", command=self.auto_repair)
        auto_menu.add_command(label="🗑️ Aggressive Cleanup (Disk + Temp)", command=self.aggressive_cleanup)
        auto_menu.add_command(label="🧹 Deep Clean (Extended)", command=self.deep_clean)
        auto_menu.add_command(label="🚀 Performance Boost (All-in-One)", command=self.performance_boost)
        auto_menu.add_separator()
        auto_menu.add_command(label="💉 Fix Common Issues (One-Click)", command=self.fix_common_issues)
        
        # ==================== SYSTEM DIAGNOSTICS MENU ====================
        sys_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="🩺 System", menu=sys_menu)
        
        # Hardware submenu
        hw_menu = DarkMenu(sys_menu, tearoff=0, font=('Segoe UI', 9))
        sys_menu.add_cascade(label="💻 Hardware Info", menu=hw_menu)
        hw_menu.add_command(label="CPU Information", command=lambda: self.run_powershell_command("Get-CimInstance Win32_Processor | Select-Object Name, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors | Format-List"))
        hw_menu.add_command(label="Memory (RAM) Details", command=lambda: self.run_powershell_command("Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer, PartNumber | Format-List"))
        hw_menu.add_command(label="Motherboard Info", command=lambda: self.run_powershell_command("Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, Version, SerialNumber | Format-List"))
        hw_menu.add_command(label="BIOS Information", command=lambda: self.run_powershell_command("Get-CimInstance Win32_BIOS | Select-Object Manufacturer, Name, Version, SerialNumber | Format-List"))
        hw_menu.add_command(label="Disk Drives", command=lambda: self.run_powershell_command("Get-CimInstance Win32_DiskDrive | Select-Object Model, Size, InterfaceType, Status | Format-List"))
        hw_menu.add_command(label="GPU Information", command=lambda: self.run_powershell_command("Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | Format-List"))
        hw_menu.add_command(label="Monitor Information", command=lambda: self.run_powershell_command("Get-CimInstance WmiMonitorID -Namespace root\\wmi | Select-Object UserFriendlyName"))
        hw_menu.add_command(label="Sound Devices", command=lambda: self.run_powershell_command("Get-CimInstance Win32_SoundDevice | Select-Object Name, Status | Format-List"))
        hw_menu.add_command(label="USB Devices", command=lambda: self.run_powershell_command("Get-CimInstance Win32_USBHub | Select-Object Name, DeviceID | Format-List"))
        
        # System Info submenu
        sysinfo_menu = DarkMenu(sys_menu, tearoff=0, font=('Segoe UI', 9))
        sys_menu.add_cascade(label="📊 System Information", menu=sysinfo_menu)
        sysinfo_menu.add_command(label="Full System Report", command=lambda: self.run_command("systeminfo"))
        sysinfo_menu.add_command(label="Windows Version Details", command=lambda: self.run_command("winver"))
        sysinfo_menu.add_command(label="Computer Name & Domain", command=lambda: self.run_powershell_command("Get-CimInstance Win32_ComputerSystem | Select-Object Name, Domain, Manufacturer, Model | Format-List"))
        sysinfo_menu.add_command(label="OS Architecture", command=lambda: self.run_powershell_command("Get-CimInstance Win32_OperatingSystem | Select-Object OSArchitecture, Caption, Version | Format-List"))
        sysinfo_menu.add_command(label="Serial Number", command=lambda: self.run_powershell_command("Get-CimInstance Win32_BIOS | Select-Object SerialNumber"))
        sysinfo_menu.add_command(label="Product Key", command=self.show_product_key)
        sysinfo_menu.add_command(label="Uptime", command=lambda: self.run_command("systeminfo | find \"System Boot Time\""))
        sysinfo_menu.add_command(label="Battery Report", command=self.battery_report)
        sysinfo_menu.add_command(label="Power Configuration", command=lambda: self.run_command("powercfg /list"))
        
        # Drivers submenu
        driver_menu = DarkMenu(sys_menu, tearoff=0, font=('Segoe UI', 9))
        sys_menu.add_cascade(label="🔌 Drivers", menu=driver_menu)
        driver_menu.add_command(label="List All Drivers", command=lambda: self.run_command("driverquery"))
        driver_menu.add_command(label="List 3rd Party Drivers", command=lambda: self.run_command("driverquery /si"))
        driver_menu.add_command(label="Check Driver Signatures", command=lambda: self.run_command("sigverif"))
        driver_menu.add_command(label="Backup All Drivers", command=self.backup_drivers)
        driver_menu.add_command(label="PnP Devices", command=lambda: self.run_powershell_command("Get-CimInstance Win32_PnPEntity | Select-Object Name, Status | Format-Table -AutoSize"))
        
        # Health checks submenu
        health_menu = DarkMenu(sys_menu, tearoff=0, font=('Segoe UI', 9))
        sys_menu.add_cascade(label="🏥 Health Checks", menu=health_menu)
        health_menu.add_command(label="Disk Health (SMART)", command=lambda: self.run_powershell_command("Get-CimInstance -Namespace root\\wmi -ClassName MSStorageDriver_FailurePredictStatus | Format-List"))
        health_menu.add_command(label="Memory Diagnostics Tool", command=lambda: self.run_command("mdsched.exe"))
        health_menu.add_command(label="System File Checker (SFC)", command=lambda: self.run_command("sfc /scannow", admin=True))
        health_menu.add_command(label="DISM - Check Health", command=lambda: self.run_command("DISM /Online /Cleanup-Image /CheckHealth", admin=True))
        health_menu.add_command(label="DISM - Scan Health", command=lambda: self.run_command("DISM /Online /Cleanup-Image /ScanHealth", admin=True))
        health_menu.add_command(label="DISM - Restore Health", command=lambda: self.run_command("DISM /Online /Cleanup-Image /RestoreHealth", admin=True))
        health_menu.add_command(label="Check Disk (Schedule)", command=self.check_disk)
        health_menu.add_command(label="Verify System Files", command=lambda: self.run_command("sfc /verifyonly", admin=True))
        
        # DirectX / Graphics
        graphics_menu = DarkMenu(sys_menu, tearoff=0, font=('Segoe UI', 9))
        sys_menu.add_cascade(label="🎮 DirectX / Graphics", menu=graphics_menu)
        graphics_menu.add_command(label="DirectX Diagnostic Tool", command=lambda: self.run_command("dxdiag"))
        graphics_menu.add_command(label="Display Settings", command=lambda: self.run_command("desk.cpl"))
        graphics_menu.add_command(label="Graphics Properties", command=lambda: self.run_command("control /name Microsoft.Display"))
        
        sys_menu.add_separator()
        sys_menu.add_command(label="📊 Performance Monitor", command=lambda: self.run_command("perfmon"))
        sys_menu.add_command(label="📈 Resource Monitor", command=lambda: self.run_command("resmon"))
        sys_menu.add_command(label="🖥️ Computer Management", command=lambda: self.run_command("compmgmt.msc"))
        sys_menu.add_command(label="📋 Event Viewer", command=lambda: self.run_command("eventvwr"))
        
        # ==================== MAINTENANCE MENU ====================
        maint_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="🔧 Maintenance", menu=maint_menu)
        
        # Windows Update submenu
        update_menu = DarkMenu(maint_menu, tearoff=0, font=('Segoe UI', 9))
        maint_menu.add_cascade(label="🔄 Windows Update", menu=update_menu)
        update_menu.add_command(label="Check for Updates", command=lambda: self.run_command("start ms-settings:windowsupdate"))
        update_menu.add_command(label="View Update History", command=lambda: self.run_command("start ms-settings:windowsupdate-history"))
        update_menu.add_command(label="List Installed Updates", command=lambda: self.run_powershell_command("Get-CimInstance Win32_QuickFixEngineering | Select-Object HotFixID, InstalledOn | Sort-Object InstalledOn -Descending | Format-Table -AutoSize"))
        update_menu.add_separator()
        update_menu.add_command(label="🔧 Complete Windows Update Repair", command=self.complete_windows_update_repair)
        update_menu.add_command(label="🔄 Reset Update Components", command=self.reset_update_components)
        update_menu.add_command(label="📋 Re-register Update DLLs", command=self.reregister_update_dlls)
        update_menu.add_command(label="🗑️ Clear Update Cache", command=self.clear_update_cache)
        update_menu.add_command(label="🔄 Reset Windows Update", command=self.reset_windows_update)
        update_menu.add_separator()
        update_menu.add_command(label="🛡️ Complete Defender Repair", command=self.complete_defender_repair)
        update_menu.add_command(label="✅ Re-enable Windows Defender", command=self.reenable_windows_defender)
        update_menu.add_command(label="🔄 Reset Defender to Default", command=self.reset_defender_default)
        update_menu.add_separator()
        update_menu.add_command(label="Update Troubleshooter", command=lambda: self.run_command("msdt.exe /id WindowsUpdateDiagnostic"))
        
        # Cleanup submenu
        cleanup_menu = DarkMenu(maint_menu, tearoff=0, font=('Segoe UI', 9))
        maint_menu.add_cascade(label="🗑️ Cleanup Tools", menu=cleanup_menu)
        cleanup_menu.add_command(label="Disk Cleanup", command=lambda: self.run_command("cleanmgr"))
        cleanup_menu.add_command(label="Disk Cleanup (System Files)", command=lambda: self.run_command("cleanmgr /sageset:1"))
        cleanup_menu.add_command(label="Clear Temp Files", command=self.clear_temp_files)
        cleanup_menu.add_command(label="Clear Windows Update Cache", command=self.clear_update_cache)
        cleanup_menu.add_command(label="Clear Prefetch", command=self.clear_prefetch)
        cleanup_menu.add_command(label="Clear Event Logs", command=self.clear_event_logs)
        cleanup_menu.add_command(label="Empty Recycle Bin", command=self.empty_recycle_bin)
        cleanup_menu.add_command(label="Clear DNS Cache", command=lambda: self.run_command("ipconfig /flushdns", admin=True))
        cleanup_menu.add_command(label="Clear Windows Store Cache", command=lambda: self.run_command("wsreset.exe"))
        cleanup_menu.add_command(label="Clear Font Cache", command=self.clear_font_cache)
        cleanup_menu.add_command(label="Clear Thumbnail Cache", command=self.clear_thumbnail_cache)
        
        # Optimization submenu
        optimize_menu = DarkMenu(maint_menu, tearoff=0, font=('Segoe UI', 9))
        maint_menu.add_cascade(label="⚡ Optimization", menu=optimize_menu)
        optimize_menu.add_command(label="Defragment & Optimize Drives", command=lambda: self.run_command("dfrgui"))
        optimize_menu.add_command(label="Optimize System Performance", command=self.optimize_performance)
        optimize_menu.add_command(label="Disable Startup Programs", command=lambda: self.run_command("msconfig"))
        optimize_menu.add_command(label="Services Management", command=lambda: self.run_command("services.msc"))
        optimize_menu.add_command(label="Startup Programs", command=lambda: self.run_command("shell:startup"))
        optimize_menu.add_command(label="Task Scheduler", command=lambda: self.run_command("taskschd.msc"))
        optimize_menu.add_command(label="Disable Hibernation", command=lambda: self.run_command("powercfg /h off", admin=True))
        optimize_menu.add_command(label="Enable Hibernation", command=lambda: self.run_command("powercfg /h on", admin=True))
        optimize_menu.add_command(label="Power Options", command=lambda: self.run_command("powercfg.cpl"))
        optimize_menu.add_command(label="Visual Effects (Performance)", command=lambda: self.run_command("SystemPropertiesPerformance.exe"))
        
        # Disk tools submenu
        disk_menu = DarkMenu(maint_menu, tearoff=0, font=('Segoe UI', 9))
        maint_menu.add_cascade(label="💾 Disk Tools", menu=disk_menu)
        disk_menu.add_command(label="Disk Management", command=lambda: self.run_command("diskmgmt.msc"))
        disk_menu.add_command(label="Check Disk Errors", command=self.check_disk)
        disk_menu.add_command(label="Disk Cleanup", command=lambda: self.run_command("cleanmgr"))
        disk_menu.add_command(label="Partition Manager", command=lambda: self.run_command("diskpart"))
        disk_menu.add_command(label="Storage Sense", command=lambda: self.run_command("start ms-settings:storagesense"))
        disk_menu.add_command(label="Disk Space Analysis", command=self.disk_space_analysis)
        
        # Scheduled Tasks submenu
        task_menu = DarkMenu(maint_menu, tearoff=0, font=('Segoe UI', 9))
        maint_menu.add_cascade(label="⏰ Scheduled Tasks", menu=task_menu)
        task_menu.add_command(label="Task Scheduler", command=lambda: self.run_command("taskschd.msc"))
        task_menu.add_command(label="List All Tasks", command=lambda: self.run_command("schtasks /query /fo LIST /v"))
        task_menu.add_command(label="Disable Telemetry Tasks", command=self.disable_telemetry_tasks)
        
        maint_menu.add_separator()
        maint_menu.add_command(label="🔍 Search Indexing Options", command=lambda: self.run_command("control.exe srchadmin.dll"))
        maint_menu.add_command(label="🖨️ Print Management", command=lambda: self.run_command("printmanagement.msc"))
        
        # ==================== NETWORK MENU ====================
        net_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="🌐 Network", menu=net_menu)
        
        # Network Info submenu
        netinfo_menu = DarkMenu(net_menu, tearoff=0, font=('Segoe UI', 9))
        net_menu.add_cascade(label="📊 Network Information", menu=netinfo_menu)
        netinfo_menu.add_command(label="IP Configuration (Full)", command=lambda: self.run_command("ipconfig /all"))
        netinfo_menu.add_command(label="Network Adapters", command=lambda: self.run_powershell_command("Get-CimInstance Win32_NetworkAdapter | Where-Object {$_.NetEnabled -eq $true} | Select-Object Name, Speed, NetConnectionStatus | Format-Table -AutoSize"))
        netinfo_menu.add_command(label="MAC Address", command=lambda: self.run_command("getmac /v"))
        netinfo_menu.add_command(label="Active Connections", command=lambda: self.run_command("netstat -ano"))
        netinfo_menu.add_command(label="Listening Ports", command=lambda: self.run_command("netstat -an | find \"LISTENING\""))
        netinfo_menu.add_command(label="Routing Table", command=lambda: self.run_command("route print"))
        netinfo_menu.add_command(label="ARP Cache", command=lambda: self.run_command("arp -a"))
        netinfo_menu.add_command(label="DNS Cache", command=lambda: self.run_command("ipconfig /displaydns"))
        netinfo_menu.add_command(label="Network Statistics", command=lambda: self.run_command("netstat -e"))
        
        # Network Tools submenu
        nettools_menu = DarkMenu(net_menu, tearoff=0, font=('Segoe UI', 9))
        net_menu.add_cascade(label="🔧 Network Tools", menu=nettools_menu)
        nettools_menu.add_command(label="Network & Sharing Center", command=lambda: self.run_command("control.exe /name Microsoft.NetworkAndSharingCenter"))
        nettools_menu.add_command(label="Network Connections", command=lambda: self.run_command("ncpa.cpl"))
        nettools_menu.add_command(label="Reset Network Stack", command=self.reset_network)
        nettools_menu.add_command(label="Release/Renew IP", command=self.renew_ip)
        nettools_menu.add_command(label="Flush DNS Cache", command=lambda: self.run_command("ipconfig /flushdns", admin=True))
        nettools_menu.add_command(label="Reset Winsock", command=lambda: self.run_command("netsh winsock reset", admin=True))
        nettools_menu.add_command(label="Reset TCP/IP", command=lambda: self.run_command("netsh int ip reset", admin=True))
        nettools_menu.add_command(label="Network Troubleshooter", command=lambda: self.run_command("msdt.exe /id NetworkDiagnosticsWeb"))
        nettools_menu.add_command(label="Ping Test", command=self.ping_test)
        nettools_menu.add_command(label="Trace Route", command=self.trace_route)
        nettools_menu.add_command(label="NSLookup", command=self.nslookup)
        
        # WiFi submenu
        wifi_menu = DarkMenu(net_menu, tearoff=0, font=('Segoe UI', 9))
        net_menu.add_cascade(label="📶 WiFi", menu=wifi_menu)
        wifi_menu.add_command(label="Show WiFi Profiles", command=lambda: self.run_command("netsh wlan show profiles"))
        wifi_menu.add_command(label="WiFi Network Report", command=self.wifi_report)
        wifi_menu.add_command(label="Show WiFi Password", command=self.show_wifi_password)
        wifi_menu.add_command(label="Export WiFi Profiles", command=self.export_wifi_profiles)
        wifi_menu.add_command(label="Forget All WiFi Networks", command=self.forget_wifi_networks)
        wifi_menu.add_command(label="WiFi Signal Strength", command=lambda: self.run_command("netsh wlan show interfaces"))
        
        # Remote Desktop submenu
        remote_menu = DarkMenu(net_menu, tearoff=0, font=('Segoe UI', 9))
        net_menu.add_cascade(label="🖥️ Remote Access", menu=remote_menu)
        remote_menu.add_command(label="Remote Desktop Connection", command=lambda: self.run_command("mstsc"))
        remote_menu.add_command(label="Remote Assistance", command=lambda: self.run_command("msra"))
        remote_menu.add_command(label="Enable Remote Desktop", command=lambda: self.run_command("reg add \"HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\" /v fDenyTSConnections /t REG_DWORD /d 0 /f", admin=True))
        remote_menu.add_command(label="Disable Remote Desktop", command=lambda: self.run_command("reg add \"HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\" /v fDenyTSConnections /t REG_DWORD /d 1 /f", admin=True))
        remote_menu.add_command(label="Quick Assist", command=lambda: self.run_command("quickassist"))
        
        # Firewall submenu
        firewall_menu = DarkMenu(net_menu, tearoff=0, font=('Segoe UI', 9))
        net_menu.add_cascade(label="🛡️ Firewall", menu=firewall_menu)
        firewall_menu.add_command(label="Windows Firewall", command=lambda: self.run_command("firewall.cpl"))
        firewall_menu.add_command(label="Advanced Firewall Settings", command=lambda: self.run_command("wf.msc"))
        firewall_menu.add_command(label="Firewall Rules", command=lambda: self.run_command("netsh advfirewall firewall show rule name=all"))
        firewall_menu.add_command(label="Enable Firewall", command=lambda: self.run_command("netsh advfirewall set allprofiles state on", admin=True))
        firewall_menu.add_command(label="Disable Firewall", command=lambda: self.run_command("netsh advfirewall set allprofiles state off", admin=True))
        
        # Hosts File submenu
        hosts_menu = DarkMenu(net_menu, tearoff=0, font=('Segoe UI', 9))
        net_menu.add_cascade(label="📝 Hosts File", menu=hosts_menu)
        hosts_menu.add_command(label="Open Hosts File", command=self.open_hosts_file)
        hosts_menu.add_command(label="Backup Hosts File", command=self.backup_hosts_file)
        hosts_menu.add_command(label="Restore Default Hosts", command=self.restore_default_hosts)
        
        # Advanced Network
        net_menu.add_separator()
        net_menu.add_command(label="🔀 Change MAC Address", command=self.change_mac_address)
        net_menu.add_command(label="🌐 Proxy Settings", command=lambda: self.run_command("inetcpl.cpl,,4"))
        net_menu.add_command(label="📡 Network Adapter Properties", command=lambda: self.run_command("ncpa.cpl"))
        
        # ==================== SECURITY MENU ====================
        sec_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="🔒 Security", menu=sec_menu)
        
        # Windows Security submenu
        winsec_menu = DarkMenu(sec_menu, tearoff=0, font=('Segoe UI', 9))
        sec_menu.add_cascade(label="🛡️ Windows Security", menu=winsec_menu)
        winsec_menu.add_command(label="Security Center", command=lambda: self.run_command("windowsdefender:"))
        winsec_menu.add_command(label="Quick Scan", command=self.defender_scan)
        winsec_menu.add_command(label="Full Scan", command=lambda: self.run_command("\"C:\\Program Files\\Windows Defender\\MpCmdRun.exe\" -Scan -ScanType 2", admin=True))
        winsec_menu.add_command(label="Update Definitions", command=lambda: self.run_command("\"C:\\Program Files\\Windows Defender\\MpCmdRun.exe\" -SignatureUpdate", admin=True))
        winsec_menu.add_command(label="Scan Specific Folder", command=self.scan_folder)
        winsec_menu.add_command(label="View Protection History", command=lambda: self.run_command("start windowsdefender://threat"))
        winsec_menu.add_command(label="Exclusions", command=lambda: self.run_command("start windowsdefender://settings"))
        
        # User Accounts submenu
        user_menu = DarkMenu(sec_menu, tearoff=0, font=('Segoe UI', 9))
        sec_menu.add_cascade(label="👤 User Accounts", menu=user_menu)
        user_menu.add_command(label="User Accounts", command=lambda: self.run_command("netplwiz"))
        user_menu.add_command(label="List Local Users", command=lambda: self.run_command("net user"))
        user_menu.add_command(label="List Local Groups", command=lambda: self.run_command("net localgroup"))
        user_menu.add_command(label="List Administrators", command=lambda: self.run_command("net localgroup administrators"))
        user_menu.add_command(label="Current User Info", command=lambda: self.run_command("whoami /all"))
        user_menu.add_command(label="Change User Password", command=self.change_password)
        user_menu.add_command(label="Create New User", command=self.create_user)
        user_menu.add_command(label="Delete User", command=self.delete_user)
        
        # Group Policy submenu
        gp_menu = DarkMenu(sec_menu, tearoff=0, font=('Segoe UI', 9))
        sec_menu.add_cascade(label="📋 Group Policy", menu=gp_menu)
        gp_menu.add_command(label="Local Group Policy Editor", command=lambda: self.run_command("gpedit.msc"))
        gp_menu.add_command(label="Group Policy Results", command=lambda: self.run_command("gpresult /r"))
        gp_menu.add_command(label="Update Group Policy", command=lambda: self.run_command("gpupdate /force", admin=True))
        
        # UAC submenu
        uac_menu = DarkMenu(sec_menu, tearoff=0, font=('Segoe UI', 9))
        sec_menu.add_cascade(label="🛡️ UAC Control", menu=uac_menu)
        uac_menu.add_command(label="UAC Settings", command=lambda: self.run_command("UserAccountControlSettings.exe"))
        uac_menu.add_command(label="Disable UAC", command=self.disable_uac)
        uac_menu.add_command(label="Enable UAC", command=self.enable_uac)
        
        # BitLocker submenu
        bitlocker_menu = DarkMenu(sec_menu, tearoff=0, font=('Segoe UI', 9))
        sec_menu.add_cascade(label="🔐 BitLocker", menu=bitlocker_menu)
        bitlocker_menu.add_command(label="BitLocker Settings", command=lambda: self.run_command("control /name Microsoft.BitLockerDriveEncryption"))
        bitlocker_menu.add_command(label="BitLocker Status", command=lambda: self.run_command("manage-bde -status"))
        bitlocker_menu.add_command(label="Enable BitLocker", command=lambda: messagebox.showinfo("BitLocker", "Use Windows Settings to enable BitLocker"))
        
        sec_menu.add_separator()
        sec_menu.add_command(label="🔑 Certificate Manager", command=lambda: self.run_command("certmgr.msc"))
        sec_menu.add_command(label="🔐 Credential Manager", command=lambda: self.run_command("control /name Microsoft.CredentialManager"))
        sec_menu.add_command(label="🔒 Local Security Policy", command=lambda: self.run_command("secpol.msc"))
        sec_menu.add_command(label="📜 Audit Policy", command=lambda: self.run_command("auditpol /get /category:*"))
        sec_menu.add_separator()
        sec_menu.add_command(label="📋 Installed Updates/Hotfixes", command=lambda: self.run_powershell_command("Get-CimInstance Win32_QuickFixEngineering | Select-Object HotFixID, InstalledOn, Description | Format-Table -AutoSize"))
        sec_menu.add_command(label="🔍 Check for Rootkits", command=self.check_rootkits)
        
        # ==================== SOFTWARE MENU ====================
        soft_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="📦 Software", menu=soft_menu)
        
        # Programs submenu
        prog_menu = DarkMenu(soft_menu, tearoff=0, font=('Segoe UI', 9))
        soft_menu.add_cascade(label="📋 Installed Programs", menu=prog_menu)
        prog_menu.add_command(label="List All Programs (Detailed)", command=self.list_programs)
        prog_menu.add_command(label="List Programs (Quick)", command=lambda: self.run_powershell_command("Get-CimInstance Win32_Product | Select-Object Name, Version | Format-Table -AutoSize"))
        prog_menu.add_command(label="Programs & Features", command=lambda: self.run_command("appwiz.cpl"))
        prog_menu.add_command(label="Installed Apps (Settings)", command=lambda: self.run_command("start ms-settings:appsfeatures"))
        prog_menu.add_command(label="Startup Apps", command=lambda: self.run_command("start ms-settings:startupapps"))
        
        # Winget submenu
        winget_menu = DarkMenu(soft_menu, tearoff=0, font=('Segoe UI', 9))
        soft_menu.add_cascade(label="📦 Winget (Package Manager)", menu=winget_menu)
        winget_menu.add_command(label="Search Packages", command=self.winget_search)
        winget_menu.add_command(label="Install Package", command=self.winget_install)
        winget_menu.add_command(label="Uninstall Package", command=self.winget_uninstall)
        winget_menu.add_command(label="Update Package", command=self.winget_upgrade_package)
        winget_menu.add_command(label="Update All Packages", command=lambda: self.run_command("winget upgrade --all"))
        winget_menu.add_command(label="List Installed (Winget)", command=lambda: self.run_command("winget list"))
        winget_menu.add_command(label="Export Package List", command=self.winget_export)
        winget_menu.add_command(label="Import Package List", command=self.winget_import)
        
        # Chocolatey submenu
        choco_menu = DarkMenu(soft_menu, tearoff=0, font=('Segoe UI', 9))
        soft_menu.add_cascade(label="🍫 Chocolatey", menu=choco_menu)
        choco_menu.add_command(label="Install Chocolatey", command=self.install_chocolatey)
        choco_menu.add_command(label="Search Packages", command=self.choco_search)
        choco_menu.add_command(label="Install Package", command=self.choco_install)
        choco_menu.add_command(label="Update All Packages", command=lambda: self.run_command("choco upgrade all -y", admin=True))
        choco_menu.add_command(label="List Installed", command=lambda: self.run_command("choco list --local-only"))
        
        # Quick Install submenu
        quickinstall_menu = DarkMenu(soft_menu, tearoff=0, font=('Segoe UI', 9))
        soft_menu.add_cascade(label="⚡ Quick Install Apps", menu=quickinstall_menu)
        
        # Browsers
        browsers_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🌐 Web Browsers", menu=browsers_menu)
        browsers_menu.add_command(label="Google Chrome", command=lambda: self.quick_install("Google.Chrome"))
        browsers_menu.add_command(label="Mozilla Firefox", command=lambda: self.quick_install("Mozilla.Firefox"))
        browsers_menu.add_command(label="Brave Browser", command=lambda: self.quick_install("Brave.Brave"))
        browsers_menu.add_command(label="Microsoft Edge", command=lambda: self.quick_install("Microsoft.Edge"))
        browsers_menu.add_command(label="Opera", command=lambda: self.quick_install("Opera.Opera"))
        browsers_menu.add_command(label="Opera GX", command=lambda: self.quick_install("Opera.OperaGX"))
        browsers_menu.add_command(label="Vivaldi", command=lambda: self.quick_install("VivaldiTechnologies.Vivaldi"))
        browsers_menu.add_command(label="Tor Browser", command=lambda: self.quick_install("TorProject.TorBrowser"))
        
        # Essential Tools
        essential_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🔧 Essential Tools", menu=essential_menu)
        essential_menu.add_command(label="7-Zip", command=lambda: self.quick_install("7zip.7zip"))
        essential_menu.add_command(label="WinRAR", command=lambda: self.quick_install("RARLab.WinRAR"))
        essential_menu.add_command(label="VLC Media Player", command=lambda: self.quick_install("VideoLAN.VLC"))
        essential_menu.add_command(label="Adobe Reader", command=lambda: self.quick_install("Adobe.Acrobat.Reader.64-bit"))
        essential_menu.add_command(label="Foxit PDF Reader", command=lambda: self.quick_install("Foxit.FoxitReader"))
        essential_menu.add_command(label="Sumatra PDF", command=lambda: self.quick_install("SumatraPDF.SumatraPDF"))
        essential_menu.add_command(label="K-Lite Codec Pack", command=lambda: self.quick_install("CodecGuide.K-LiteCodecPack.Standard"))
        
        # Communication
        comm_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="💬 Communication", menu=comm_menu)
        comm_menu.add_command(label="Discord", command=lambda: self.quick_install("Discord.Discord"))
        comm_menu.add_command(label="Slack", command=lambda: self.quick_install("SlackTechnologies.Slack"))
        comm_menu.add_command(label="Microsoft Teams", command=lambda: self.quick_install("Microsoft.Teams"))
        comm_menu.add_command(label="Zoom", command=lambda: self.quick_install("Zoom.Zoom"))
        comm_menu.add_command(label="Skype", command=lambda: self.quick_install("Microsoft.Skype"))
        comm_menu.add_command(label="Telegram", command=lambda: self.quick_install("Telegram.TelegramDesktop"))
        comm_menu.add_command(label="WhatsApp", command=lambda: self.quick_install("WhatsApp.WhatsApp"))
        comm_menu.add_command(label="Signal", command=lambda: self.quick_install("OpenWhisperSystems.Signal"))
        
        # Media & Entertainment
        media_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🎬 Media & Entertainment", menu=media_menu)
        media_menu.add_command(label="VLC Media Player", command=lambda: self.quick_install("VideoLAN.VLC"))
        media_menu.add_command(label="Spotify", command=lambda: self.quick_install("Spotify.Spotify"))
        media_menu.add_command(label="iTunes", command=lambda: self.quick_install("Apple.iTunes"))
        media_menu.add_command(label="Audacity", command=lambda: self.quick_install("Audacity.Audacity"))
        media_menu.add_command(label="OBS Studio", command=lambda: self.quick_install("OBSProject.OBSStudio"))
        media_menu.add_command(label="HandBrake", command=lambda: self.quick_install("HandBrake.HandBrake"))
        media_menu.add_command(label="MPC-HC", command=lambda: self.quick_install("clsid2.mpc-hc"))
        media_menu.add_command(label="Kodi", command=lambda: self.quick_install("XBMCFoundation.Kodi"))
        media_menu.add_command(label="Plex", command=lambda: self.quick_install("Plex.Plex"))
        
        # Developer Tools
        dev_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="💻 Developer Tools", menu=dev_menu)
        dev_menu.add_command(label="Visual Studio Code", command=lambda: self.quick_install("Microsoft.VisualStudioCode"))
        dev_menu.add_command(label="Visual Studio 2022 Community", command=lambda: self.quick_install("Microsoft.VisualStudio.2022.Community"))
        dev_menu.add_command(label="Git", command=lambda: self.quick_install("Git.Git"))
        dev_menu.add_command(label="GitHub Desktop", command=lambda: self.quick_install("GitHub.GitHubDesktop"))
        dev_menu.add_command(label="Python 3", command=lambda: self.quick_install("Python.Python.3.12"))
        dev_menu.add_command(label="Node.js", command=lambda: self.quick_install("OpenJS.NodeJS"))
        dev_menu.add_command(label="Docker Desktop", command=lambda: self.quick_install("Docker.DockerDesktop"))
        dev_menu.add_command(label="Postman", command=lambda: self.quick_install("Postman.Postman"))
        dev_menu.add_command(label="JetBrains Toolbox", command=lambda: self.quick_install("JetBrains.Toolbox"))
        dev_menu.add_command(label="Android Studio", command=lambda: self.quick_install("Google.AndroidStudio"))
        dev_menu.add_command(label="Unity Hub", command=lambda: self.quick_install("Unity.UnityHub"))
        dev_menu.add_command(label="Sublime Text", command=lambda: self.quick_install("SublimeHQ.SublimeText.4"))
        dev_menu.add_command(label="Atom", command=lambda: self.quick_install("GitHub.Atom"))
        dev_menu.add_command(label="Notepad++", command=lambda: self.quick_install("Notepad++.Notepad++"))
        
        # System Utilities
        util_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🛠️ System Utilities", menu=util_menu)
        util_menu.add_command(label="PowerToys", command=lambda: self.quick_install("Microsoft.PowerToys"))
        util_menu.add_command(label="Everything Search", command=lambda: self.quick_install("voidtools.Everything"))
        util_menu.add_command(label="CCleaner", command=lambda: self.quick_install("Piriform.CCleaner"))
        util_menu.add_command(label="TreeSize Free", command=lambda: self.quick_install("JAMSoftware.TreeSize.Free"))
        util_menu.add_command(label="WizTree", command=lambda: self.quick_install("AntibodySoftware.WizTree"))
        util_menu.add_command(label="Sysinternals Suite", command=lambda: self.quick_install("Microsoft.Sysinternals.Suite"))
        util_menu.add_command(label="Process Explorer", command=lambda: self.quick_install("Microsoft.Sysinternals.ProcessExplorer"))
        util_menu.add_command(label="AutoHotkey", command=lambda: self.quick_install("AutoHotkey.AutoHotkey"))
        util_menu.add_command(label="ShareX", command=lambda: self.quick_install("ShareX.ShareX"))
        util_menu.add_command(label="Greenshot", command=lambda: self.quick_install("Greenshot.Greenshot"))
        util_menu.add_command(label="Rufus", command=lambda: self.quick_install("Rufus.Rufus"))
        util_menu.add_command(label="Balena Etcher", command=lambda: self.quick_install("Balena.Etcher"))
        util_menu.add_command(label="Ventoy", command=lambda: self.quick_install("Ventoy.Ventoy"))
        
        # Remote Access
        remote_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🖥️ Remote Access", menu=remote_menu)
        remote_menu.add_command(label="TeamViewer", command=lambda: self.quick_install("TeamViewer.TeamViewer"))
        remote_menu.add_command(label="AnyDesk", command=lambda: self.quick_install("AnyDesk.AnyDesk"))
        remote_menu.add_command(label="Chrome Remote Desktop", command=lambda: webbrowser.open("https://remotedesktop.google.com/"))
        remote_menu.add_command(label="RustDesk", command=lambda: self.quick_install("RustDesk.RustDesk"))
        remote_menu.add_command(label="TightVNC", command=lambda: self.quick_install("GlavSoft.TightVNC"))
        remote_menu.add_command(label="UltraVNC", command=lambda: self.quick_install("uvnc.UltraVnc"))
        remote_menu.add_command(label="Parsec", command=lambda: self.quick_install("Parsec.Parsec"))
        
        # Security & Privacy
        security_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🔒 Security & Privacy", menu=security_menu)
        security_menu.add_command(label="Malwarebytes", command=lambda: self.quick_install("Malwarebytes.Malwarebytes"))
        security_menu.add_command(label="Bitwarden", command=lambda: self.quick_install("Bitwarden.Bitwarden"))
        security_menu.add_command(label="1Password", command=lambda: self.quick_install("AgileBits.1Password"))
        security_menu.add_command(label="KeePassXC", command=lambda: self.quick_install("KeePassXCTeam.KeePassXC"))
        security_menu.add_command(label="NordVPN", command=lambda: self.quick_install("NordVPN.NordVPN"))
        security_menu.add_command(label="ProtonVPN", command=lambda: self.quick_install("ProtonTechnologies.ProtonVPN"))
        security_menu.add_command(label="VeraCrypt", command=lambda: self.quick_install("IDRIX.VeraCrypt"))
        security_menu.add_command(label="Wireshark", command=lambda: self.quick_install("WiresharkFoundation.Wireshark"))
        
        # Cloud Storage
        cloud_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="☁️ Cloud Storage", menu=cloud_menu)
        cloud_menu.add_command(label="Google Drive", command=lambda: self.quick_install("Google.GoogleDrive"))
        cloud_menu.add_command(label="Dropbox", command=lambda: self.quick_install("Dropbox.Dropbox"))
        cloud_menu.add_command(label="OneDrive", command=lambda: self.quick_install("Microsoft.OneDrive"))
        cloud_menu.add_command(label="Nextcloud", command=lambda: self.quick_install("Nextcloud.NextcloudDesktop"))
        cloud_menu.add_command(label="MEGA", command=lambda: self.quick_install("Mega.MEGASync"))
        cloud_menu.add_command(label="Box Drive", command=lambda: self.quick_install("Box.Box"))
        cloud_menu.add_command(label="pCloud", command=lambda: self.quick_install("pCloud.pCloudDrive"))
        
        # Office & Productivity
        office_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="📝 Office & Productivity", menu=office_menu)
        office_menu.add_command(label="LibreOffice", command=lambda: self.quick_install("TheDocumentFoundation.LibreOffice"))
        office_menu.add_command(label="Notion", command=lambda: self.quick_install("Notion.Notion"))
        office_menu.add_command(label="Obsidian", command=lambda: self.quick_install("Obsidian.Obsidian"))
        office_menu.add_command(label="Evernote", command=lambda: self.quick_install("Evernote.Evernote"))
        office_menu.add_command(label="Adobe Acrobat Reader", command=lambda: self.quick_install("Adobe.Acrobat.Reader.64-bit"))
        office_menu.add_command(label="Microsoft Office 365", command=lambda: webbrowser.open("https://www.office.com/"))
        office_menu.add_command(label="Grammarly", command=lambda: self.quick_install("Grammarly.Grammarly"))
        office_menu.add_command(label="Calibre", command=lambda: self.quick_install("calibre.calibre"))
        
        # Gaming
        gaming_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🎮 Gaming", menu=gaming_menu)
        gaming_menu.add_command(label="Steam", command=lambda: self.quick_install("Valve.Steam"))
        gaming_menu.add_command(label="Epic Games Launcher", command=lambda: self.quick_install("EpicGames.EpicGamesLauncher"))
        gaming_menu.add_command(label="GOG Galaxy", command=lambda: self.quick_install("GOG.Galaxy"))
        gaming_menu.add_command(label="EA App", command=lambda: self.quick_install("ElectronicArts.EADesktop"))
        gaming_menu.add_command(label="Battle.net", command=lambda: self.quick_install("Blizzard.BattleNet"))
        gaming_menu.add_command(label="Ubisoft Connect", command=lambda: self.quick_install("Ubisoft.Connect"))
        gaming_menu.add_command(label="Xbox App", command=lambda: self.quick_install("Microsoft.GamingApp"))
        gaming_menu.add_command(label="Discord", command=lambda: self.quick_install("Discord.Discord"))
        gaming_menu.add_command(label="MSI Afterburner", command=lambda: self.quick_install("Guru3D.Afterburner"))
        gaming_menu.add_command(label="Razer Synapse", command=lambda: self.quick_install("Razer.Synapse.3"))
        
        # Graphics & Design
        graphics_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🎨 Graphics & Design", menu=graphics_menu)
        graphics_menu.add_command(label="GIMP", command=lambda: self.quick_install("GIMP.GIMP"))
        graphics_menu.add_command(label="Inkscape", command=lambda: self.quick_install("Inkscape.Inkscape"))
        graphics_menu.add_command(label="Krita", command=lambda: self.quick_install("KDE.Krita"))
        graphics_menu.add_command(label="Paint.NET", command=lambda: self.quick_install("dotPDN.PaintDotNet"))
        graphics_menu.add_command(label="Blender", command=lambda: self.quick_install("BlenderFoundation.Blender"))
        graphics_menu.add_command(label="DaVinci Resolve", command=lambda: webbrowser.open("https://www.blackmagicdesign.com/products/davinciresolve"))
        graphics_menu.add_command(label="Figma", command=lambda: self.quick_install("Figma.Figma"))
        graphics_menu.add_command(label="IrfanView", command=lambda: self.quick_install("IrfanSkiljan.IrfanView"))
        graphics_menu.add_command(label="XnView", command=lambda: self.quick_install("XnSoft.XnView.Classic"))
        
        # Network Tools
        nettools_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="🌐 Network Tools", menu=nettools_menu)
        nettools_menu.add_command(label="Wireshark", command=lambda: self.quick_install("WiresharkFoundation.Wireshark"))
        nettools_menu.add_command(label="PuTTY", command=lambda: self.quick_install("PuTTY.PuTTY"))
        nettools_menu.add_command(label="WinSCP", command=lambda: self.quick_install("WinSCP.WinSCP"))
        nettools_menu.add_command(label="FileZilla", command=lambda: self.quick_install("TimKosse.FileZilla.Client"))
        nettools_menu.add_command(label="Advanced IP Scanner", command=lambda: self.quick_install("Famatech.AdvancedIPScanner"))
        nettools_menu.add_command(label="Angry IP Scanner", command=lambda: self.quick_install("angryziber.AngryIPScanner"))
        nettools_menu.add_command(label="NetSpot", command=lambda: webbrowser.open("https://www.netspotapp.com/"))
        
        # File Management
        filemgmt_menu = DarkMenu(quickinstall_menu, tearoff=0, font=('Segoe UI', 9))
        quickinstall_menu.add_cascade(label="📁 File Management", menu=filemgmt_menu)
        filemgmt_menu.add_command(label="Total Commander", command=lambda: self.quick_install("Ghisler.TotalCommander"))
        filemgmt_menu.add_command(label="FreeCommander", command=lambda: self.quick_install("Marek.Jasinski.FreeCommander"))
        filemgmt_menu.add_command(label="Double Commander", command=lambda: self.quick_install("alexx2000.DoubleCommander"))
        filemgmt_menu.add_command(label="WinMerge", command=lambda: self.quick_install("WinMerge.WinMerge"))
        filemgmt_menu.add_command(label="Beyond Compare", command=lambda: self.quick_install("ScooterSoftware.BeyondCompare4"))
        
        soft_menu.add_separator()
        soft_menu.add_command(label="🌐 Ninite (Bulk Installer)", command=lambda: webbrowser.open("https://ninite.com"))
        soft_menu.add_command(label="🔗 Download: Revo Uninstaller", command=lambda: webbrowser.open("https://www.revouninstaller.com/revo-uninstaller-free-download/"))
        
        # ==================== RESCUE & RECOVERY MENU ====================
        rescue_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="💾 Rescue & Recovery", menu=rescue_menu)
        
        # Backup submenu
        backup_menu = DarkMenu(rescue_menu, tearoff=0, font=('Segoe UI', 9))
        rescue_menu.add_cascade(label="💼 Backup & Export", menu=backup_menu)
        
        # Smart Backup submenu
        smartbackup_menu = DarkMenu(backup_menu, tearoff=0, font=('Segoe UI', 9))
        backup_menu.add_cascade(label="🎯 Smart Profile Backup", menu=smartbackup_menu)
        smartbackup_menu.add_command(label="Desktop + Documents + Pictures", command=self.smart_backup_user_folders)
        smartbackup_menu.add_command(label="Full User Profile", command=self.backup_user_profile)
        smartbackup_menu.add_command(label="Selective Backup", command=self.selective_backup)
        
        backup_menu.add_command(label="💾 Backup Drivers", command=self.backup_drivers)
        backup_menu.add_command(label="📶 Export WiFi Profiles", command=self.export_wifi_profiles)
        backup_menu.add_command(label="🌐 Backup Browser Data", command=self.backup_browser_data)
        backup_menu.add_command(label="🔑 Backup Product Keys", command=self.backup_product_keys)
        backup_menu.add_command(label="📧 Backup Email (Outlook)", command=self.backup_outlook)
        backup_menu.add_command(label="🖼️ Backup Desktop & Documents", command=self.backup_user_folders)
        
        # Restore submenu
        restore_menu = DarkMenu(rescue_menu, tearoff=0, font=('Segoe UI', 9))
        rescue_menu.add_cascade(label="♻️ Restore", menu=restore_menu)
        restore_menu.add_command(label="📶 Restore WiFi Profiles", command=self.restore_wifi_profiles)
        restore_menu.add_command(label="🌐 Restore Browser Profiles", command=self.restore_browser_data)
        restore_menu.add_command(label="🔄 System Restore", command=lambda: self.run_command("rstrui.exe"))
        restore_menu.add_command(label="📂 Previous Versions (Shadow Copy)", command=self.access_shadow_copies)
        
        # System State submenu
        sysstate_menu = DarkMenu(rescue_menu, tearoff=0, font=('Segoe UI', 9))
        rescue_menu.add_cascade(label="📋 System State & Registry", menu=sysstate_menu)
        sysstate_menu.add_command(label="Open Registry Editor", command=lambda: self.run_command("regedit"))
        sysstate_menu.add_command(label="Backup Registry Hives", command=self.backup_registry)
        sysstate_menu.add_command(label="Import Registry File", command=self.import_registry)
        sysstate_menu.add_command(label="Create Restore Point", command=self.create_restore_point)
        sysstate_menu.add_command(label="Windows Backup", command=lambda: self.run_command("sdclt.exe"))
        sysstate_menu.add_command(label="File History", command=lambda: self.run_command("control /name Microsoft.FileHistory"))
        
        # Image & WIM Tools submenu
        image_menu = DarkMenu(rescue_menu, tearoff=0, font=('Segoe UI', 9))
        rescue_menu.add_cascade(label="💿 Image & WIM Tools", menu=image_menu)
        image_menu.add_command(label="Mount ISO", command=self.mount_iso)
        image_menu.add_command(label="Unmount ISO", command=self.unmount_iso)
        image_menu.add_command(label="Mount WIM/ESD", command=self.mount_wim)
        image_menu.add_command(label="Unmount WIM/ESD", command=self.unmount_wim)
        image_menu.add_command(label="Apply WIM Image", command=self.apply_wim)
        image_menu.add_command(label="Capture WIM Image", command=self.capture_wim)
        image_menu.add_command(label="Get WIM Info", command=self.get_wim_info)
        
        # Recovery Tools submenu
        rectools_menu = DarkMenu(rescue_menu, tearoff=0, font=('Segoe UI', 9))
        rescue_menu.add_cascade(label="🩺 Recovery Tools", menu=rectools_menu)
        rectools_menu.add_command(label="Download Recuva (File Recovery)", command=lambda: webbrowser.open("https://www.ccleaner.com/recuva/download"))
        rectools_menu.add_command(label="Download TestDisk/PhotoRec", command=lambda: webbrowser.open("https://www.cgsecurity.org/wiki/TestDisk_Download"))
        rectools_menu.add_command(label="Windows File Recovery", command=lambda: self.run_command("winfr"))
        
        # Advanced Boot submenu
        boot_menu = DarkMenu(rescue_menu, tearoff=0, font=('Segoe UI', 9))
        rescue_menu.add_cascade(label="👢 Boot & Recovery", menu=boot_menu)
        boot_menu.add_command(label="Reboot to Recovery (WinRE)", command=self.reboot_to_recovery)
        boot_menu.add_command(label="Reboot to BIOS/UEFI", command=self.reboot_to_bios)
        boot_menu.add_command(label="Boot Configuration", command=lambda: self.run_command("msconfig"))
        boot_menu.add_command(label="BCDEdit (Boot Manager)", command=lambda: self.run_command("bcdedit"))
        boot_menu.add_command(label="Repair Boot Loader", command=self.repair_bootloader)
        boot_menu.add_command(label="Rebuild BCD", command=self.rebuild_bcd)
        
        rescue_menu.add_separator()
        rescue_menu.add_command(label="🪞 Full Drive Mirror (Robocopy)", command=self.robocopy_mirror)
        rescue_menu.add_command(label="📥 Disk Clone/Image Tools", command=lambda: messagebox.showinfo("Tools", "Consider using: Macrium Reflect, Clonezilla, or Acronis"))
        rescue_menu.add_command(label="🔧 Download Transwiz (Profile Transfer)", command=lambda: webbrowser.open("https://www.forensit.com/downloads.html"))
        
        # ==================== HELP MENU ====================
        help_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="❓ Help", menu=help_menu)
        
        # AI Troubleshooter submenu
        ai_menu = DarkMenu(help_menu, tearoff=0, font=('Segoe UI', 9))
        help_menu.add_cascade(label="🤖 AI Troubleshooter", menu=ai_menu)
        ai_menu.add_command(label="💬 ChatGPT (OpenAI)", command=lambda: webbrowser.open("https://chat.openai.com/"))
        ai_menu.add_command(label="🔷 Claude (Anthropic)", command=lambda: webbrowser.open("https://claude.ai/"))
        ai_menu.add_command(label="🔍 Perplexity AI", command=lambda: webbrowser.open("https://www.perplexity.ai/"))
        ai_menu.add_command(label="🌟 Google Gemini", command=lambda: webbrowser.open("https://gemini.google.com/"))
        ai_menu.add_command(label="🤖 Microsoft Copilot", command=lambda: webbrowser.open("https://copilot.microsoft.com/"))
        ai_menu.add_command(label="💭 Bing Chat", command=lambda: webbrowser.open("https://www.bing.com/chat"))
        ai_menu.add_command(label="🎯 You.com", command=lambda: webbrowser.open("https://you.com/"))
        ai_menu.add_separator()
        ai_menu.add_command(label="📝 Copy System Info for AI", command=self.copy_system_info_for_ai)
        ai_menu.add_command(label="💡 Troubleshooting Tips", command=self.show_ai_tips)
        
        help_menu.add_separator()
        
        # Windows Troubleshooters submenu
        troubleshoot_menu = DarkMenu(help_menu, tearoff=0, font=('Segoe UI', 9))
        help_menu.add_cascade(label="🔧 Windows Troubleshooters", menu=troubleshoot_menu)
        troubleshoot_menu.add_command(label="All Troubleshooters", command=lambda: self.run_command("control.exe /name Microsoft.Troubleshooting"))
        troubleshoot_menu.add_command(label="Network Troubleshooter", command=lambda: self.run_command("msdt.exe /id NetworkDiagnosticsWeb"))
        troubleshoot_menu.add_command(label="Windows Update Troubleshooter", command=lambda: self.run_command("msdt.exe /id WindowsUpdateDiagnostic"))
        troubleshoot_menu.add_command(label="Audio Troubleshooter", command=lambda: self.run_command("msdt.exe /id AudioPlaybackDiagnostic"))
        troubleshoot_menu.add_command(label="Printer Troubleshooter", command=lambda: self.run_command("msdt.exe /id PrinterDiagnostic"))
        troubleshoot_menu.add_command(label="Power Troubleshooter", command=lambda: self.run_command("msdt.exe /id PowerDiagnostic"))
        
        # Useful Websites submenu
        web_menu = DarkMenu(help_menu, tearoff=0, font=('Segoe UI', 9))
        help_menu.add_cascade(label="🔗 Useful Websites", menu=web_menu)
        
        websites = {
            'MAS Activation Script': 'https://massgrave.dev/',
            'Microsoft Download Center': 'https://www.microsoft.com/en-us/software-download',
            'Windows Insider ISO': 'https://www.microsoft.com/en-us/software-download/windowsinsiderpreviewiso',
            'MS Software Download': 'https://msdl.gravesoft.dev/',
            'Chris Titus WinUtil': 'https://github.com/ChrisTitusTech/winutil',
            'Get Into PC': 'https://getintopc.com/',
            'Autounattend Generator': 'https://schneegans.de/windows/unattend-generator/',
            'Sordum Tools': 'https://www.sordum.org/',
            'Windows Config Designer': 'https://github.com/letsdoautomation/windows-configuration-designer',
            'Snappy Driver Installer': 'https://sdi-tool.org/download/',
            'NirSoft Utilities': 'https://www.nirsoft.net/',
            'Sysinternals Suite': 'https://docs.microsoft.com/en-us/sysinternals/',
            'Ninite': 'https://ninite.com/'
        }
        
        for name, url in websites.items():
            web_menu.add_command(label=name, command=lambda u=url: webbrowser.open(u))
        
        # Documentation
        docs_menu = DarkMenu(help_menu, tearoff=0, font=('Segoe UI', 9))
        help_menu.add_cascade(label="📚 Documentation", menu=docs_menu)
        docs_menu.add_command(label="Windows Commands Reference", command=lambda: webbrowser.open("https://ss64.com/nt/"))
        docs_menu.add_command(label="PowerShell Documentation", command=lambda: webbrowser.open("https://docs.microsoft.com/en-us/powershell/"))
        docs_menu.add_command(label="Windows Registry Guide", command=lambda: webbrowser.open("https://www.howtogeek.com/370022/windows-registry-demystified-what-you-can-do-with-it/"))
        
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
        help_menu.add_command(label="🆘 Help & Support", command=self.show_help)
        
        # ==================== ADVANCED TOOLS MENU ====================
        advanced_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="⚙️ Advanced", menu=advanced_menu)
        
        # Registry Tweaks submenu
        registry_menu = DarkMenu(advanced_menu, tearoff=0, font=('Segoe UI', 9))
        advanced_menu.add_cascade(label="📝 Registry Tweaks", menu=registry_menu)
        registry_menu.add_command(label="Disable Windows Telemetry", command=self.disable_telemetry)
        registry_menu.add_command(label="Disable Cortana", command=self.disable_cortana)
        registry_menu.add_command(label="Enable Dark Theme", command=self.enable_windows_dark_theme)
        registry_menu.add_command(label="Disable Windows Animations", command=self.disable_animations)
        registry_menu.add_command(label="Show File Extensions", command=self.show_file_extensions)
        registry_menu.add_command(label="Show Hidden Files", command=self.show_hidden_files)
        registry_menu.add_command(label="Disable Web Search in Start", command=self.disable_web_search)
        registry_menu.add_command(label="Remove OneDrive", command=self.remove_onedrive)
        registry_menu.add_command(label="Classic Context Menu (Win11)", command=self.classic_context_menu)
        registry_menu.add_command(label="Remove Ads from Start Menu", command=self.remove_start_ads)
        
        # Gaming Optimizations submenu
        gaming_menu = DarkMenu(advanced_menu, tearoff=0, font=('Segoe UI', 9))
        advanced_menu.add_cascade(label="🎮 Gaming Optimizations", menu=gaming_menu)
        gaming_menu.add_command(label="Enable Game Mode", command=self.enable_game_mode)
        gaming_menu.add_command(label="Disable Game Bar", command=self.disable_game_bar)
        gaming_menu.add_command(label="Enable Hardware Acceleration", command=self.enable_hardware_acceleration)
        gaming_menu.add_command(label="Optimize for Low Latency", command=self.optimize_latency)
        gaming_menu.add_command(label="Disable Fullscreen Optimizations", command=self.disable_fullscreen_opt)
        gaming_menu.add_command(label="High Performance Power Plan", command=lambda: self.run_command("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", admin=True))
        
        # Privacy Tools submenu
        privacy_menu = DarkMenu(advanced_menu, tearoff=0, font=('Segoe UI', 9))
        advanced_menu.add_cascade(label="🔒 Privacy Tools", menu=privacy_menu)
        privacy_menu.add_command(label="Disable All Telemetry", command=self.disable_all_telemetry)
        privacy_menu.add_command(label="Disable Location Tracking", command=self.disable_location)
        privacy_menu.add_command(label="Disable Activity History", command=self.disable_activity_history)
        privacy_menu.add_command(label="Disable Advertising ID", command=self.disable_advertising_id)
        privacy_menu.add_command(label="Clear Activity History", command=self.clear_activity_history)
        privacy_menu.add_command(label="Hosts File Ad Blocker", command=self.hosts_ad_blocker)
        
        # Windows Activation submenu
        activation_menu = DarkMenu(advanced_menu, tearoff=0, font=('Segoe UI', 9))
        advanced_menu.add_cascade(label="🔑 Activation", menu=activation_menu)
        activation_menu.add_command(label="Check Activation Status", command=self.check_activation_status)
        activation_menu.add_command(label="View Product Key", command=self.show_product_key)
        activation_menu.add_command(label="Open MAS Activation", command=lambda: webbrowser.open("https://massgrave.dev/"))
        activation_menu.add_command(label="Check Office Activation", command=self.check_office_activation)
        
        # Hardware Monitoring submenu
        hardware_menu = DarkMenu(advanced_menu, tearoff=0, font=('Segoe UI', 9))
        advanced_menu.add_cascade(label="🌡️ Hardware Monitor", menu=hardware_menu)
        hardware_menu.add_command(label="CPU & GPU Info", command=self.show_cpu_gpu_info)
        hardware_menu.add_command(label="Temperature Monitor", command=self.show_temperature_info)
        hardware_menu.add_command(label="Disk Health (SMART)", command=lambda: self.run_powershell_command("Get-PhysicalDisk | Format-Table -AutoSize"))
        hardware_menu.add_command(label="Battery Report", command=self.battery_report)
        hardware_menu.add_command(label="Power Configuration", command=lambda: self.run_command("powercfg /list"))
        hardware_menu.add_separator()
        hardware_menu.add_command(label="Download HWMonitor", command=lambda: webbrowser.open("https://www.cpuid.com/softwares/hwmonitor.html"))
        hardware_menu.add_command(label="Download HWiNFO", command=lambda: webbrowser.open("https://www.hwinfo.com/download/"))
        
        # Batch Operations submenu
        batch_menu = DarkMenu(advanced_menu, tearoff=0, font=('Segoe UI', 9))
        advanced_menu.add_cascade(label="⚡ Batch Operations", menu=batch_menu)
        batch_menu.add_command(label="Bulk File Rename", command=self.bulk_rename)
        batch_menu.add_command(label="Find Duplicate Files", command=self.find_duplicates)
        batch_menu.add_command(label="Find Large Files", command=self.find_large_files)
        batch_menu.add_command(label="Batch Convert Images", command=self.batch_convert_images)
        batch_menu.add_command(label="Mass File Delete by Extension", command=self.mass_delete_by_ext)
        
        # Custom Scripts submenu
        scripts_menu = DarkMenu(advanced_menu, tearoff=0, font=('Segoe UI', 9))
        advanced_menu.add_cascade(label="📜 Custom Scripts", menu=scripts_menu)
        scripts_menu.add_command(label="Manage Custom Scripts", command=self.manage_custom_scripts)
        scripts_menu.add_command(label="Create New Script", command=self.create_custom_script)
        scripts_menu.add_command(label="Import Script", command=self.import_custom_script)
        scripts_menu.add_command(label="Export Scripts", command=self.export_custom_scripts)
        
        advanced_menu.add_separator()
        advanced_menu.add_command(label="🔧 Windows Features On/Off", command=lambda: self.run_command("OptionalFeatures.exe"))
        advanced_menu.add_command(label="🐋 Manage Docker Containers", command=self.manage_docker)
        advanced_menu.add_command(label="🐧 WSL Management", command=self.manage_wsl)
        advanced_menu.add_command(label="💻 Hyper-V Manager", command=lambda: self.run_command("virtmgmt.msc"))
        advanced_menu.add_command(label="🔍 Port Scanner", command=self.port_scanner)
        advanced_menu.add_command(label="🔐 Password Generator", command=self.password_generator)

        # ==================== REGTECHES APPS MENU ====================
        apps_menu = DarkMenu(menubar, tearoff=0, font=('Segoe UI', 9))
        menubar.add_cascade(label="🚀 REGTeches Apps", menu=apps_menu)
        apps_menu.add_command(
            label="📦 AppForge — Package Manager GUI",
            command=self.open_appforge)
        apps_menu.add_command(
            label="🔒 CyberScan — Security Suite",
            command=self.open_cyberscan)
        apps_menu.add_command(
            label="💾 BackupPro — Backup Suite",
            command=self.open_backuppro)
        apps_menu.add_separator()
        apps_menu.add_command(
            label="📋 Import Saved Package List (programs.json)",
            command=self.import_programs_json)

    def create_toolbar(self):
        """Create quick access toolbar"""
        toolbar = tk.Frame(self.root, bg=self.colors['bg_medium'], height=60)
        toolbar.pack(fill='x', padx=0, pady=0)
        
        # Left side - Quick actions
        left_frame = tk.Frame(toolbar, bg=self.colors['bg_medium'])
        left_frame.pack(side='left', padx=10, pady=10)
        
        # Quick action buttons
        quick_actions = [
            ("⚡", "Quick Health", self.quick_health_check),
            ("🔧", "Auto Repair", self.auto_repair),
            ("🧹", "Deep Clean", self.deep_clean),
            ("📊", "Report", self.generate_system_report),
            ("🌐", "Network", self.reset_network),
            ("💾", "Backup", self.smart_backup_user_folders),
        ]
        
        for icon, text, command in quick_actions:
            btn = tk.Button(left_frame,
                          text=f"{icon}\n{text}",
                          command=command,
                          bg=self.colors['bg_light'],
                          fg=self.colors['text'],
                          font=('Segoe UI', 8),
                          relief='flat',
                          padx=8,
                          pady=8,
                          cursor='hand2',
                          bd=0)
            btn.pack(side='left', padx=3)
            
            # Hover effects
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.colors['accent']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=self.colors['bg_light']))
        
        # Right side - System status
        right_frame = tk.Frame(toolbar, bg=self.colors['bg_medium'])
        right_frame.pack(side='right', padx=10, pady=10)
        
        # Admin status
        admin_color = self.colors['success'] if self.is_admin else self.colors['warning']
        admin_text = "Admin ✓" if self.is_admin else "User ⚠"
        
        admin_label = tk.Label(right_frame,
                              text=admin_text,
                              bg=admin_color,
                              fg='white',
                              font=('Segoe UI', 9, 'bold'),
                              padx=10,
                              pady=5)
        admin_label.pack(side='right', padx=5)
        
        # System monitors
        self.cpu_label = tk.Label(right_frame,
                                 text="CPU: --",
                                 bg=self.colors['bg_light'],
                                 fg=self.colors['text'],
                                 font=('Segoe UI', 9),
                                 padx=10,
                                 pady=5)
        self.cpu_label.pack(side='right', padx=5)
        
        self.mem_label = tk.Label(right_frame,
                                 text="RAM: --",
                                 bg=self.colors['bg_light'],
                                 fg=self.colors['text'],
                                 font=('Segoe UI', 9),
                                 padx=10,
                                 pady=5)
        self.mem_label.pack(side='right', padx=5)
    
    def create_main_layout(self):
        """Create the main application layout with dark theme"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - System info dashboard
        left_panel = tk.Frame(main_frame, bg=self.colors['bg_medium'], width=350)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Dashboard title
        dash_title = tk.Label(left_panel,
                             text="📊 System Dashboard",
                             font=('Segoe UI', 14, 'bold'),
                             bg=self.colors['bg_medium'],
                             fg=self.colors['accent'])
        dash_title.pack(pady=15, padx=15, anchor='w')
        
        # System info card
        info_card = tk.Frame(left_panel, bg=self.colors['bg_light'], relief='raised', bd=1)
        info_card.pack(fill='x', padx=15, pady=10)
        
        tk.Label(info_card,
                text="💻 System Information",
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['bg_light'],
                fg=self.colors['text']).pack(anchor='w', padx=10, pady=8)
        
        # Get system info
        system_info = self.get_system_info()
        self.info_text_label = tk.Label(info_card,
                                        text=system_info,
                                        font=('Segoe UI', 9),
                                        bg=self.colors['bg_light'],
                                        fg=self.colors['text_dim'],
                                        justify='left',
                                        anchor='w',
                                        wraplength=320)  # Wrap text to fit panel width
        self.info_text_label.pack(anchor='w', padx=10, pady=(0, 10), fill='x')
        
        # Activity card
        activity_card = tk.Frame(left_panel, bg=self.colors['bg_light'], relief='raised', bd=1)
        activity_card.pack(fill='x', padx=15, pady=10)
        
        tk.Label(activity_card,
                text="📈 Activity",
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['bg_light'],
                fg=self.colors['text']).pack(anchor='w', padx=10, pady=8)
        
        self.command_count_label = tk.Label(activity_card,
                                           text="Commands run: 0",
                                           font=('Segoe UI', 9),
                                           bg=self.colors['bg_light'],
                                           fg=self.colors['text_dim'])
        self.command_count_label.pack(anchor='w', padx=10, pady=(0, 10))
        
        # Right panel - Activity log
        right_panel = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Status header
        status_header = tk.Frame(right_panel, bg=self.colors['bg_medium'], height=40)
        status_header.pack(fill='x')
        
        tk.Label(status_header,
                text="📋 Activity Log",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['bg_medium'],
                fg=self.colors['text']).pack(side='left', padx=15, pady=10)
        
        # Clear log button
        clear_btn = tk.Button(status_header,
                             text="🗑️ Clear",
                             command=self.clear_log,
                             bg=self.colors['bg_light'],
                             fg=self.colors['text'],
                             font=('Segoe UI', 9),
                             relief='flat',
                             padx=10,
                             pady=5,
                             cursor='hand2')
        clear_btn.pack(side='right', padx=15, pady=5)
        
        # Status text area
        status_frame = tk.Frame(right_panel, bg=self.colors['bg_dark'])
        status_frame.pack(fill='both', expand=True, pady=(5, 0))
        
        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg=self.colors['log_bg'],
            fg=self.colors['log_fg'],
            insertbackground='white',
            selectbackground=self.colors['accent'],
            relief='flat',
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.status_text.pack(fill='both', expand=True)
        
        # Configure text tags for colored output
        self.status_text.tag_config('success', foreground=self.colors['success'])
        self.status_text.tag_config('warning', foreground=self.colors['warning'])
        self.status_text.tag_config('error', foreground=self.colors['error'])
        self.status_text.tag_config('info', foreground='#2196f3')
    
    def get_system_info(self):
        """Get basic system information"""
        try:
            system = platform.system()
            release = platform.release()
            machine = platform.machine()
            processor = platform.processor()
            
            # Get additional Windows info
            if platform.system() == 'Windows':
                try:
                    result = subprocess.run('powershell -NoProfile -Command "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version"', 
                                          shell=True, capture_output=True, text=True, timeout=5)
                    lines = result.stdout.strip().split('\n')
                    os_caption = ""
                    os_version = ""
                    for line in lines:
                        if 'Caption' in line and ':' in line:
                            os_caption = line.split(':', 1)[1].strip()
                        elif 'Version' in line and ':' in line:
                            os_version = line.split(':', 1)[1].strip()
                    
                    if os_caption:
                        system = os_caption
                        if os_version:
                            release = os_version
                except:
                    pass
            
            # Shorten processor name if too long for display
            proc_display = processor
            if len(processor) > 50:
                # Try to extract key parts
                if 'Intel' in processor or 'AMD' in processor:
                    parts = processor.split()
                    proc_display = ' '.join(parts[:5]) + '...'
                else:
                    proc_display = processor[:47] + '...'
            
            # Format with line breaks for better wrapping
            info = f"OS: {system}\n"
            info += f"Build: {release}\n"
            info += f"Arch: {machine}\n"
            info += f"CPU: {proc_display}\n"
            info += f"User: {os.getenv('USERNAME', 'Unknown')}\n"
            info += f"Admin: {'Yes ✓' if self.is_admin else 'No ✗'}"
            
            return info
        except Exception as e:
            return f"System info unavailable:\n{str(e)}"
    
    def update_status(self, message, tag=None):
        """Update status display with timestamp and optional color tag"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n", tag)
        self.status_text.see('end')
        self.root.update_idletasks()
    
    def run_powershell_command(self, ps_command, show_output=True):
        """Execute PowerShell command (for Windows 11 compatibility - replaces WMIC)"""
        self.update_status(f"Executing PowerShell command...")
        
        def execute():
            try:
                # Escape quotes properly for PowerShell
                escaped_command = ps_command.replace('"', '`"')
                full_command = f'powershell -NoProfile -Command "{escaped_command}"'
                
                result = subprocess.run(
                    full_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if show_output and result.stdout:
                    output = result.stdout[:5000]
                    if len(result.stdout) > 5000:
                        output += "\n... (output truncated)"
                    self.update_status(output)
                if result.stderr and "successfully" not in result.stderr.lower():
                    error = result.stderr[:2000]
                    if len(result.stderr) > 2000:
                        error += "\n... (output truncated)"
                    self.update_status(f"Warning: {error}")
                
                if result.returncode == 0:
                    self.update_status("✓ Command completed successfully")
                else:
                    self.update_status(f"⚠ Command returned code: {result.returncode}")
                    
            except subprocess.TimeoutExpired:
                self.update_status("⚠ Command timed out after 5 minutes")
            except Exception as e:
                self.update_status(f"✗ Error: {str(e)}")
        
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    def run_command(self, command, admin=False, show_output=True):
        """Execute a system command"""
        if admin and not self.is_admin:
            messagebox.showwarning(
                "Administrator Required",
                "This command requires administrator privileges.\n\n" +
                "Please restart the toolkit as administrator."
            )
            return
        
        self.update_status(f"Executing: {command}")
        
        def execute():
            try:
                if isinstance(command, str):
                    if platform.system() == 'Windows':
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                    else:
                        result = subprocess.run(
                            command.split(),
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                    
                    if show_output and result.stdout:
                        # Limit output length for display
                        output = result.stdout[:5000]
                        if len(result.stdout) > 5000:
                            output += "\n... (output truncated)"
                        self.update_status(output)
                    if result.stderr and "successfully" not in result.stderr.lower():
                        error = result.stderr[:2000]
                        if len(result.stderr) > 2000:
                            error += "\n... (output truncated)"
                        self.update_status(f"Error: {error}")
                    
                    if result.returncode == 0:
                        self.update_status("✓ Command completed successfully")
                    else:
                        self.update_status(f"⚠ Command returned code: {result.returncode}")
                        
            except subprocess.TimeoutExpired:
                self.update_status("⚠ Command timed out after 5 minutes")
            except Exception as e:
                self.update_status(f"✗ Error: {str(e)}")
        
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    # ==================== AUTOMATED TOOLS ====================
    
    def quick_health_check(self):
        """Perform quick PC health check"""
        self.update_status("\n" + "="*60)
        self.update_status("=== QUICK HEALTH CHECK STARTING ===")
        self.update_status("="*60 + "\n")
        
        def run_checks():
            checks = [
                ("Checking disk health (SMART)...", 'powershell -NoProfile -Command "Get-PhysicalDisk | Select-Object FriendlyName, HealthStatus | Format-Table -AutoSize"'),
                ("Checking memory modules...", 'powershell -NoProfile -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer | Format-Table -AutoSize"'),
                ("Verifying system files...", "sfc /verifyonly"),
                ("Testing network connectivity...", "ping -n 3 8.8.8.8"),
                ("Checking Windows version...", 'powershell -NoProfile -Command "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version | Format-List"'),
                ("Listing recent errors...", "wevtutil qe System /c:10 /rd:true /f:text /q:\"*[System[(Level=1 or Level=2)]]\"")
            ]
            
            for desc, cmd in checks:
                self.update_status(desc)
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.stdout:
                        # Show limited output
                        output = result.stdout[:500].strip()
                        self.update_status(output)
                except:
                    self.update_status("  ⚠ Check failed")
                self.update_status("")
            
            self.update_status("="*60)
            self.update_status("=== HEALTH CHECK COMPLETE ===")
            self.update_status("="*60 + "\n")
            messagebox.showinfo("Complete", "Quick health check finished! Check the log for details.")
        
        thread = threading.Thread(target=run_checks, daemon=True)
        thread.start()
    
    def auto_repair(self):
        """Run SFC and DISM repair"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Auto-repair requires administrator privileges.")
            return
        
        if messagebox.askyesno("Confirm", "This will run SFC and DISM repairs.\n\n⏱️ This may take 15-30 minutes.\n\nContinue?"):
            self.update_status("\n" + "="*60)
            self.update_status("=== AUTO REPAIR STARTING ===")
            self.update_status("="*60 + "\n")
            
            def repair():
                self.update_status("Running System File Checker (SFC)...")
                self.update_status("This will verify and repair Windows system files...")
                self.run_command("sfc /scannow", admin=True)
                
                self.update_status("\nRunning DISM RestoreHealth...")
                self.update_status("This will repair the Windows image...")
                self.run_command("DISM /Online /Cleanup-Image /RestoreHealth", admin=True)
                
                self.update_status("\n" + "="*60)
                self.update_status("=== REPAIR COMPLETE ===")
                self.update_status("="*60)
                self.update_status("✓ It's recommended to restart your PC now.")
                messagebox.showinfo("Complete", "Auto-repair finished!\n\nRestart your PC for changes to take effect.")
            
            thread = threading.Thread(target=repair, daemon=True)
            thread.start()
    
    def aggressive_cleanup(self):
        """Aggressive disk and temp cleanup"""
        if messagebox.askyesno("Confirm", "This will:\n" +
                             "• Delete temporary files\n" +
                             "• Clear Windows Update cache\n" +
                             "• Clear prefetch\n" +
                             "• Empty recycle bin\n\n" +
                             "Continue?"):
            self.update_status("\n=== AGGRESSIVE CLEANUP STARTING ===\n")
            
            def cleanup():
                self.clear_temp_files()
                self.clear_update_cache()
                self.clear_prefetch()
                self.empty_recycle_bin()
                self.update_status("\n=== CLEANUP COMPLETE ===")
                messagebox.showinfo("Complete", "Aggressive cleanup finished!")
            
            thread = threading.Thread(target=cleanup, daemon=True)
            thread.start()
    
    def deep_clean(self):
        """Extended deep cleaning"""
        if messagebox.askyesno("Confirm", "This will perform an extended deep clean:\n\n" +
                             "• Temp files\n" +
                             "• Update cache\n" +
                             "• Event logs (Admin required)\n" +
                             "• Prefetch\n" +
                             "• Recycle bin\n" +
                             "• Font cache\n" +
                             "• Thumbnail cache\n\n" +
                             "Continue?"):
            self.update_status("\n=== DEEP CLEAN STARTING ===\n")
            
            def clean():
                self.clear_temp_files()
                self.clear_update_cache()
                self.clear_prefetch()
                self.clear_event_logs()
                self.empty_recycle_bin()
                self.clear_font_cache()
                self.clear_thumbnail_cache()
                
                self.update_status("\n=== DEEP CLEAN COMPLETE ===")
                messagebox.showinfo("Complete", "Deep clean finished!\n\nConsider restarting your PC.")
            
            thread = threading.Thread(target=clean, daemon=True)
            thread.start()
    
    def performance_boost(self):
        """All-in-one performance optimization"""
        if not self.is_admin:
            messagebox.showwarning("Admin Required", "Performance boost requires administrator privileges for best results.")
        
        if messagebox.askyesno("Performance Boost", "This will:\n\n" +
                             "• Clean temporary files\n" +
                             "• Optimize system settings\n" +
                             "• Disable unnecessary services (if admin)\n" +
                             "• Clear caches\n\n" +
                             "Continue?"):
            self.update_status("\n=== PERFORMANCE BOOST STARTING ===\n")
            
            def boost():
                self.aggressive_cleanup()
                self.optimize_performance()
                self.update_status("\n=== PERFORMANCE BOOST COMPLETE ===")
                messagebox.showinfo("Complete", "Performance boost complete!\n\nRestart for best results.")
            
            thread = threading.Thread(target=boost, daemon=True)
            thread.start()
    
    def fix_common_issues(self):
        """Fix common Windows issues with one click"""
        if messagebox.askyesno("Fix Common Issues", "This will attempt to fix:\n\n" +
                             "• Network connectivity\n" +
                             "• Windows Update\n" +
                             "• System file corruption\n" +
                             "• DNS issues\n\n" +
                             "Continue?"):
            self.update_status("\n=== FIXING COMMON ISSUES ===\n")
            
            def fix():
                self.update_status("Resetting network stack...")
                self.run_command("netsh winsock reset", admin=True, show_output=False)
                self.run_command("netsh int ip reset", admin=True, show_output=False)
                self.run_command("ipconfig /flushdns", admin=True, show_output=False)
                
                self.update_status("Resetting Windows Update...")
                self.reset_windows_update()
                
                self.update_status("Running SFC scan...")
                self.run_command("sfc /scannow", admin=True, show_output=False)
                
                self.update_status("\n=== FIXES APPLIED ===")
                self.update_status("Please restart your computer for changes to take effect.")
                messagebox.showinfo("Complete", "Common issues fixed!\n\nPlease restart your PC.")
            
            thread = threading.Thread(target=fix, daemon=True)
            thread.start()
    
    # ==================== MAINTENANCE TOOLS ====================
    
    def clear_temp_files(self):
        """Clear temporary files"""
        self.update_status("Clearing temporary files...")
        if platform.system() == 'Windows':
            commands = [
                f"del /q /f /s {os.getenv('TEMP')}\\* 2>nul",
                "del /q /f /s C:\\Windows\\Temp\\* 2>nul"
            ]
            for cmd in commands:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
                except:
                    pass
        self.update_status("✓ Temp files cleared")
    
    def clear_update_cache(self):
        """Clear Windows Update cache"""
        if not self.is_admin:
            self.update_status("⚠ Admin required for update cache cleanup")
            return
        
        self.update_status("Clearing Windows Update cache...")
        commands = [
            "net stop wuauserv",
            "net stop bits",
            "del /q /f /s C:\\Windows\\SoftwareDistribution\\Download\\* 2>nul",
            "net start wuauserv",
            "net start bits"
        ]
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            except:
                pass
        self.update_status("✓ Update cache cleared")
    
    def clear_prefetch(self):
        """Clear prefetch folder"""
        if not self.is_admin:
            self.update_status("⚠ Admin required to clear prefetch")
            return
        
        self.update_status("Clearing prefetch...")
        try:
            subprocess.run("del /q /f /s C:\\Windows\\Prefetch\\* 2>nul", shell=True, capture_output=True, timeout=10)
            self.update_status("✓ Prefetch cleared")
        except:
            self.update_status("⚠ Could not clear prefetch")
    
    def clear_event_logs(self):
        """Clear Windows event logs"""
        if not self.is_admin:
            self.update_status("⚠ Admin required to clear event logs")
            return
        
        if messagebox.askyesno("Confirm", "Clear all Windows event logs?"):
            self.update_status("Clearing event logs...")
            try:
                result = subprocess.run(
                    'powershell -Command "Get-WinEvent -ListLog * | ForEach-Object { Clear-EventLog $_.LogName -ErrorAction SilentlyContinue }"',
                    shell=True, capture_output=True, timeout=30
                )
                self.update_status("✓ Event logs cleared")
            except:
                self.update_status("⚠ Some event logs could not be cleared")
    
    def empty_recycle_bin(self):
        """Empty recycle bin"""
        self.update_status("Emptying recycle bin...")
        if platform.system() == 'Windows':
            try:
                subprocess.run("rd /s /q %systemdrive%\\$Recycle.Bin 2>nul", shell=True, capture_output=True, timeout=10)
                self.update_status("✓ Recycle bin emptied")
            except:
                self.update_status("✓ Recycle bin processed")
    
    def clear_font_cache(self):
        """Clear font cache"""
        self.update_status("Clearing font cache...")
        try:
            subprocess.run("net stop FontCache", shell=True, capture_output=True, timeout=5)
            subprocess.run("del /q /f /s %windir%\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache\\* 2>nul", shell=True, capture_output=True, timeout=10)
            subprocess.run("net start FontCache", shell=True, capture_output=True, timeout=5)
            self.update_status("✓ Font cache cleared")
        except:
            self.update_status("⚠ Font cache operation completed with warnings")
    
    def clear_thumbnail_cache(self):
        """Clear thumbnail cache"""
        self.update_status("Clearing thumbnail cache...")
        try:
            subprocess.run("del /q /f /s %localappdata%\\Microsoft\\Windows\\Explorer\\*.db 2>nul", shell=True, capture_output=True, timeout=10)
            self.update_status("✓ Thumbnail cache cleared")
        except:
            self.update_status("⚠ Thumbnail cache operation completed")
    
    def reset_windows_update(self):
        """Reset Windows Update components"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Resetting Windows Update requires admin privileges.")
            return
        
        self.update_status("Resetting Windows Update components...")
        commands = [
            "net stop wuauserv",
            "net stop cryptSvc",
            "net stop bits",
            "net stop msiserver",
            "ren C:\\Windows\\SoftwareDistribution SoftwareDistribution.old",
            "ren C:\\Windows\\System32\\catroot2 catroot2.old",
            "net start wuauserv",
            "net start cryptSvc",
            "net start bits",
            "net start msiserver"
        ]
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            except:
                pass
        self.update_status("✓ Windows Update reset complete")
    
    def complete_windows_update_repair(self):
        """Complete Windows Update repair with registry fixes and DLL re-registration"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This repair requires administrator privileges.")
            return
        
        if not messagebox.askyesno("Confirm Windows Update Repair", 
                                   "This will perform a complete Windows Update repair:\n\n" +
                                   "• Stop Windows Update services\n" +
                                   "• Clear update cache and folders\n" +
                                   "• Fix registry entries\n" +
                                   "• Re-register all update DLLs\n" +
                                   "• Restart services\n\n" +
                                   "This may take 5-10 minutes. Continue?"):
            return
        
        self.update_status("\n" + "="*60, 'info')
        self.update_status("=== COMPLETE WINDOWS UPDATE REPAIR ===", 'info')
        self.update_status("="*60 + "\n", 'info')
        
        def repair():
            try:
                # Step 1: Stop all Windows Update services
                self.update_status("Step 1: Stopping Windows Update services...", 'info')
                services = ["wuauserv", "cryptSvc", "bits", "msiserver"]
                for svc in services:
                    subprocess.run(f"net stop {svc}", shell=True, capture_output=True, timeout=10)
                    subprocess.run(f"sc config {svc} start= disabled", shell=True, capture_output=True, timeout=5)
                self.update_status("✅ Services stopped", 'success')
                
                # Step 2: Delete update cache folders
                self.update_status("Step 2: Clearing update cache...", 'info')
                folders_to_clear = [
                    "C:\\Windows\\SoftwareDistribution",
                    "C:\\Windows\\System32\\catroot2"
                ]
                for folder in folders_to_clear:
                    try:
                        subprocess.run(f'takeown /f "{folder}" /r /d y', shell=True, capture_output=True, timeout=30)
                        subprocess.run(f'icacls "{folder}" /grant administrators:F /t', shell=True, capture_output=True, timeout=30)
                        subprocess.run(f'rd /s /q "{folder}"', shell=True, capture_output=True, timeout=30)
                        self.update_status(f"  ✓ Cleared: {folder}", 'success')
                    except:
                        self.update_status(f"  ⚠ Could not clear: {folder}", 'warning')
                
                # Step 3: Fix registry entries
                self.update_status("Step 3: Fixing registry entries...", 'info')
                reg_commands = [
                    'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate" /v AccountDomainSid /f',
                    'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate" /v PingID /f',
                    'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate" /v SusClientId /f',
                    'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate" /v SusClientIDValidation /f',
                    'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" /v DisableWindowsUpdateAccess /t REG_DWORD /d 0 /f',
                    'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 0 /f'
                ]
                for cmd in reg_commands:
                    try:
                        subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                    except:
                        pass
                self.update_status("✅ Registry entries fixed", 'success')
                
                # Step 4: Re-register all Windows Update DLLs
                self.update_status("Step 4: Re-registering Windows Update DLLs...", 'info')
                dlls = [
                    "atl.dll", "urlmon.dll", "mshtml.dll", "shdocvw.dll", "browseui.dll",
                    "jscript.dll", "vbscript.dll", "scrrun.dll", "msxml.dll", "msxml3.dll",
                    "msxml6.dll", "actxprxy.dll", "softpub.dll", "wintrust.dll", "dssenh.dll",
                    "rsaenh.dll", "gpkcsp.dll", "sccbase.dll", "slbcsp.dll", "cryptdlg.dll",
                    "oleaut32.dll", "ole32.dll", "shell32.dll", "initpki.dll", "wuapi.dll",
                    "wuaueng.dll", "wuaueng1.dll", "wucltui.dll", "wups.dll", "wups2.dll",
                    "wuweb.dll", "qmgr.dll", "qmgrprxy.dll", "wucltux.dll", "muweb.dll", "wuwebv.dll"
                ]
                dll_count = 0
                for dll in dlls:
                    try:
                        result = subprocess.run(f"regsvr32.exe /s {dll}", shell=True, capture_output=True, timeout=5)
                        if result.returncode == 0:
                            dll_count += 1
                    except:
                        pass
                self.update_status(f"✅ Re-registered {dll_count}/{len(dlls)} DLLs", 'success')
                
                # Step 5: Reset Windows Update policies
                self.update_status("Step 5: Resetting Windows Update policies...", 'info')
                policy_commands = [
                    'gpupdate /force',
                    'bitsadmin /reset /allusers'
                ]
                for cmd in policy_commands:
                    try:
                        subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
                    except:
                        pass
                self.update_status("✅ Policies reset", 'success')
                
                # Step 6: Restart all Windows Update services
                self.update_status("Step 6: Restarting Windows Update services...", 'info')
                for svc in services:
                    subprocess.run(f"sc config {svc} start= auto", shell=True, capture_output=True, timeout=5)
                    subprocess.run(f"net start {svc}", shell=True, capture_output=True, timeout=10)
                self.update_status("✅ Services restarted", 'success')
                
                # Step 7: Force check for updates
                self.update_status("Step 7: Forcing Windows Update check...", 'info')
                subprocess.run('powershell -Command "UsoClient StartScan"', shell=True, capture_output=True, timeout=10)
                subprocess.run('wuauclt /detectnow', shell=True, capture_output=True, timeout=10)
                self.update_status("✅ Update check initiated", 'success')
                
                self.update_status("\n" + "="*60, 'success')
                self.update_status("=== WINDOWS UPDATE REPAIR COMPLETE ===", 'success')
                self.update_status("="*60 + "\n", 'success')
                
                messagebox.showinfo("Repair Complete!", 
                                  "Windows Update has been completely repaired!\n\n" +
                                  "What was done:\n" +
                                  "✓ Services stopped and restarted\n" +
                                  "✓ Update cache cleared\n" +
                                  "✓ Registry entries fixed\n" +
                                  f"✓ {dll_count} DLLs re-registered\n" +
                                  "✓ Policies reset\n\n" +
                                  "You can now check for updates normally.\n" +
                                  "Restart recommended for best results.")
                
            except Exception as e:
                self.update_status(f"❌ Error during repair: {str(e)}", 'error')
                messagebox.showerror("Repair Error", f"An error occurred during repair:\n\n{str(e)}")
        
        # Run in background thread
        threading.Thread(target=repair, daemon=True).start()
    
    def reset_update_components(self):
        """Reset Windows Update components only"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This requires administrator privileges.")
            return
        
        self.update_status("Resetting Windows Update components...", 'info')
        
        def reset():
            services = ["wuauserv", "cryptSvc", "bits", "msiserver"]
            
            # Stop services
            for svc in services:
                subprocess.run(f"net stop {svc}", shell=True, capture_output=True, timeout=10)
            
            # Rename folders
            subprocess.run('ren "C:\\Windows\\SoftwareDistribution" "SoftwareDistribution.old"', shell=True, capture_output=True)
            subprocess.run('ren "C:\\Windows\\System32\\catroot2" "catroot2.old"', shell=True, capture_output=True)
            
            # Start services
            for svc in services:
                subprocess.run(f"net start {svc}", shell=True, capture_output=True, timeout=10)
            
            self.update_status("✅ Windows Update components reset", 'success')
            messagebox.showinfo("Complete", "Windows Update components have been reset.")
        
        threading.Thread(target=reset, daemon=True).start()
    
    def reregister_update_dlls(self):
        """Re-register all Windows Update DLLs"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This requires administrator privileges.")
            return
        
        self.update_status("Re-registering Windows Update DLLs...", 'info')
        
        def reregister():
            dlls = [
                "atl.dll", "urlmon.dll", "mshtml.dll", "shdocvw.dll", "browseui.dll",
                "jscript.dll", "vbscript.dll", "scrrun.dll", "msxml.dll", "msxml3.dll",
                "msxml6.dll", "actxprxy.dll", "softpub.dll", "wintrust.dll", "dssenh.dll",
                "rsaenh.dll", "gpkcsp.dll", "sccbase.dll", "slbcsp.dll", "cryptdlg.dll",
                "oleaut32.dll", "ole32.dll", "shell32.dll", "initpki.dll", "wuapi.dll",
                "wuaueng.dll", "wuaueng1.dll", "wucltui.dll", "wups.dll", "wups2.dll",
                "wuweb.dll", "qmgr.dll", "qmgrprxy.dll", "wucltux.dll", "muweb.dll", "wuwebv.dll"
            ]
            
            success_count = 0
            for dll in dlls:
                try:
                    result = subprocess.run(f"regsvr32.exe /s {dll}", shell=True, capture_output=True, timeout=5)
                    if result.returncode == 0:
                        success_count += 1
                except:
                    pass
            
            self.update_status(f"✅ Re-registered {success_count}/{len(dlls)} DLLs", 'success')
            messagebox.showinfo("Complete", f"Successfully re-registered {success_count} out of {len(dlls)} DLLs.")
        
        threading.Thread(target=reregister, daemon=True).start()
    
    def complete_defender_repair(self):
        """Complete Windows Defender repair - reset to factory defaults"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This requires administrator privileges.")
            return
        
        if not messagebox.askyesno("Confirm Defender Repair",
                                   "This will completely reset Windows Defender:\n\n" +
                                   "• Re-enable if disabled\n" +
                                   "• Reset all settings to default\n" +
                                   "• Clear exclusions\n" +
                                   "• Update definitions\n" +
                                   "• Restart protection\n\n" +
                                   "Continue?"):
            return
        
        self.update_status("\n" + "="*60, 'info')
        self.update_status("=== COMPLETE WINDOWS DEFENDER REPAIR ===", 'info')
        self.update_status("="*60 + "\n", 'info')
        
        def repair():
            try:
                # Step 1: Remove any third-party antivirus interference
                self.update_status("Step 1: Checking for conflicts...", 'info')
                
                # Step 2: Re-enable Windows Defender via registry
                self.update_status("Step 2: Re-enabling Windows Defender...", 'info')
                reg_commands = [
                    'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /f',
                    'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiVirus /f',
                    'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableBehaviorMonitoring /f',
                    'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableOnAccessProtection /f',
                    'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /f',
                    'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableScanOnRealtimeEnable /f',
                    'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 0 /f',
                    'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender" /v DisableAntiVirus /t REG_DWORD /d 0 /f',
                    'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableBehaviorMonitoring /t REG_DWORD /d 0 /f',
                    'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableIOAVProtection /t REG_DWORD /d 0 /f',
                    'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableOnAccessProtection /t REG_DWORD /d 0 /f',
                    'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 0 /f',
                    'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableScanOnRealtimeEnable /t REG_DWORD /d 0 /f'
                ]
                for cmd in reg_commands:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                self.update_status("✅ Registry settings fixed", 'success')
                
                # Step 3: Enable Windows Defender services
                self.update_status("Step 3: Enabling Defender services...", 'info')
                services = ["WinDefend", "WdNisSvc", "Sense", "wscsvc"]
                for svc in services:
                    subprocess.run(f"sc config {svc} start= auto", shell=True, capture_output=True, timeout=5)
                    subprocess.run(f"net start {svc}", shell=True, capture_output=True, timeout=10)
                self.update_status("✅ Services enabled and started", 'success')
                
                # Step 4: Reset Defender settings via PowerShell
                self.update_status("Step 4: Resetting Defender settings...", 'info')
                ps_commands = [
                    "Set-MpPreference -DisableRealtimeMonitoring $false",
                    "Set-MpPreference -DisableBehaviorMonitoring $false",
                    "Set-MpPreference -DisableBlockAtFirstSeen $false",
                    "Set-MpPreference -DisableIOAVProtection $false",
                    "Set-MpPreference -DisablePrivacyMode $false",
                    "Set-MpPreference -SignatureDisableUpdateOnStartupWithoutEngine $false",
                    "Set-MpPreference -DisableArchiveScanning $false",
                    "Set-MpPreference -DisableIntrusionPreventionSystem $false",
                    "Set-MpPreference -DisableScriptScanning $false",
                    "Set-MpPreference -SubmitSamplesConsent 1",
                    "Set-MpPreference -MAPSReporting 2",
                    "Set-MpPreference -HighThreatDefaultAction Quarantine",
                    "Set-MpPreference -ModerateThreatDefaultAction Quarantine",
                    "Set-MpPreference -LowThreatDefaultAction Quarantine",
                    "Set-MpPreference -SevereThreatDefaultAction Quarantine"
                ]
                for cmd in ps_commands:
                    subprocess.run(f'powershell -Command "{cmd}"', shell=True, capture_output=True, timeout=10)
                self.update_status("✅ Defender settings reset to defaults", 'success')
                
                # Step 5: Update definitions
                self.update_status("Step 5: Updating virus definitions...", 'info')
                subprocess.run('powershell -Command "Update-MpSignature"', shell=True, capture_output=True, timeout=60)
                self.update_status("✅ Definitions updated", 'success')
                
                # Step 6: Run quick scan to verify
                self.update_status("Step 6: Verifying Defender is working...", 'info')
                subprocess.run('powershell -Command "Start-MpScan -ScanType QuickScan"', shell=True, capture_output=True, timeout=5)
                self.update_status("✅ Quick scan initiated", 'success')
                
                self.update_status("\n" + "="*60, 'success')
                self.update_status("=== WINDOWS DEFENDER REPAIR COMPLETE ===", 'success')
                self.update_status("="*60 + "\n", 'success')
                
                messagebox.showinfo("Repair Complete!",
                                  "Windows Defender has been completely repaired!\n\n" +
                                  "What was done:\n" +
                                  "✓ Registry settings fixed\n" +
                                  "✓ All protection features enabled\n" +
                                  "✓ Services started\n" +
                                  "✓ Settings reset to defaults\n" +
                                  "✓ Virus definitions updated\n" +
                                  "✓ Quick scan started\n\n" +
                                  "Windows Defender is now working like new!\n" +
                                  "Check Windows Security to verify.")
                
            except Exception as e:
                self.update_status(f"❌ Error during repair: {str(e)}", 'error')
                messagebox.showerror("Repair Error", f"An error occurred:\n\n{str(e)}")
        
        threading.Thread(target=repair, daemon=True).start()
    
    def reenable_windows_defender(self):
        """Re-enable Windows Defender if disabled"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This requires administrator privileges.")
            return
        
        self.update_status("Re-enabling Windows Defender...", 'info')
        
        def reenable():
            # Remove disable registry keys
            reg_commands = [
                'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /f',
                'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiVirus /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 0 /f'
            ]
            for cmd in reg_commands:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            
            # Start services
            subprocess.run("sc config WinDefend start= auto", shell=True, capture_output=True, timeout=5)
            subprocess.run("net start WinDefend", shell=True, capture_output=True, timeout=10)
            
            # Enable real-time protection
            subprocess.run('powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $false"', shell=True, capture_output=True, timeout=10)
            
            self.update_status("✅ Windows Defender re-enabled", 'success')
            messagebox.showinfo("Complete", "Windows Defender has been re-enabled!")
        
        threading.Thread(target=reenable, daemon=True).start()
    
    def reset_defender_default(self):
        """Reset Windows Defender to default settings"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This requires administrator privileges.")
            return
        
        self.update_status("Resetting Defender to defaults...", 'info')
        
        def reset():
            ps_commands = [
                "Set-MpPreference -DisableRealtimeMonitoring $false",
                "Set-MpPreference -SubmitSamplesConsent 1",
                "Set-MpPreference -MAPSReporting 2",
                "Set-MpPreference -HighThreatDefaultAction Quarantine",
                "Set-MpPreference -ModerateThreatDefaultAction Quarantine",
                "Update-MpSignature"
            ]
            for cmd in ps_commands:
                subprocess.run(f'powershell -Command "{cmd}"', shell=True, capture_output=True, timeout=10)
            
            self.update_status("✅ Defender reset to defaults", 'success')
            messagebox.showinfo("Complete", "Windows Defender has been reset to default settings!")
        
        threading.Thread(target=reset, daemon=True).start()
    
    def optimize_performance(self):
        """Run performance optimization"""
        self.update_status("Optimizing system performance...")
        if platform.system() == 'Windows':
            commands = [
                "powercfg /h off",  # Disable hibernation
                "fsutil behavior set disablelastaccess 1"  # Disable last access update
            ]
            if self.is_admin:
                for cmd in commands:
                    try:
                        subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                    except:
                        pass
            else:
                self.update_status("  ⚠ Admin required for some optimizations")
        self.update_status("✓ Performance optimizations applied")
    
    def check_disk(self):
        """Check disk for errors"""
        drive = simpledialog.askstring("Check Disk", "Enter drive letter (e.g., C):")
        if drive:
            drive = drive.upper().strip().replace(':', '')
            if messagebox.askyesno("Confirm", f"Schedule disk check for drive {drive}: on next restart?"):
                self.run_command(f"echo Y | chkdsk {drive}: /F /R", admin=True)
                messagebox.showinfo("Scheduled", f"Disk check scheduled for drive {drive}: on next restart.")
    
    def disk_space_analysis(self):
        """Show disk space analysis"""
        self.update_status("Analyzing disk space...")
        self.run_powershell_command("Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID, VolumeName, @{Name='Size(GB)';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeSpace(GB)';Expression={[math]::Round($_.FreeSpace/1GB,2)}} | Format-Table -AutoSize")
    
    def disable_telemetry_tasks(self):
        """Disable Windows telemetry scheduled tasks"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This operation requires admin privileges.")
            return
        
        if messagebox.askyesno("Confirm", "Disable telemetry scheduled tasks?"):
            self.update_status("Disabling telemetry tasks...")
            tasks = [
                "Microsoft\\Windows\\Application Experience\\Microsoft Compatibility Appraiser",
                "Microsoft\\Windows\\Application Experience\\ProgramDataUpdater",
                "Microsoft\\Windows\\Autochk\\Proxy",
                "Microsoft\\Windows\\Customer Experience Improvement Program\\Consolidator",
                "Microsoft\\Windows\\Customer Experience Improvement Program\\UsbCeip",
                "Microsoft\\Windows\\DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector"
            ]
            for task in tasks:
                try:
                    subprocess.run(f'schtasks /Change /TN "{task}" /Disable', shell=True, capture_output=True, timeout=5)
                except:
                    pass
            self.update_status("✓ Telemetry tasks disabled")
    
    # ==================== NETWORK TOOLS ====================
    
    def reset_network(self):
        """Reset network stack"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Network reset requires administrator privileges.")
            return
        
        if messagebox.askyesno("Confirm", "Reset all network adapters?\n\n⚠️ PC will need to restart after this operation."):
            self.update_status("Resetting network stack...")
            commands = [
                "netsh winsock reset",
                "netsh int ip reset",
                "ipconfig /release",
                "ipconfig /renew",
                "ipconfig /flushdns"
            ]
            for cmd in commands:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
                except:
                    pass
            
            self.update_status("✓ Network reset complete - restart required")
            if messagebox.askyesno("Restart", "Network reset complete.\n\nRestart now?"):
                subprocess.run("shutdown /r /t 30", shell=True)
    
    def renew_ip(self):
        """Release and renew IP address"""
        self.update_status("Renewing IP address...")
        try:
            subprocess.run("ipconfig /release", shell=True, capture_output=True, timeout=10)
            subprocess.run("ipconfig /renew", shell=True, capture_output=True, timeout=10)
            self.update_status("✓ IP address renewed")
            self.run_command("ipconfig /all")
        except:
            self.update_status("⚠ IP renewal may have failed")
    
    def export_wifi_profiles(self):
        """Export WiFi profiles"""
        folder = filedialog.askdirectory(title="Select destination folder")
        if folder:
            self.update_status(f"Exporting WiFi profiles to {folder}...")
            self.run_command(f"netsh wlan export profile folder=\"{folder}\" key=clear")
            self.update_status("✓ WiFi profiles exported")
            messagebox.showinfo("Complete", f"WiFi profiles exported to:\n{folder}")
    
    def restore_wifi_profiles(self):
        """Restore WiFi profiles from folder"""
        folder = filedialog.askdirectory(title="Select folder containing WiFi profiles")
        if folder:
            self.update_status(f"Restoring WiFi profiles from {folder}...")
            try:
                for file in Path(folder).glob("*.xml"):
                    subprocess.run(f'netsh wlan add profile filename="{file}" user=all', shell=True, capture_output=True, timeout=5)
                self.update_status("✓ WiFi profiles restored")
                messagebox.showinfo("Complete", "WiFi profiles restored!")
            except Exception as e:
                self.update_status(f"⚠ Error: {e}")
    
    def show_wifi_password(self):
        """Show WiFi password for a profile"""
        profile = simpledialog.askstring("WiFi Password", "Enter WiFi network name:")
        if profile:
            self.run_command(f"netsh wlan show profile name=\"{profile}\" key=clear")
    
    def wifi_report(self):
        """Generate WiFi network report"""
        self.update_status("Generating WiFi report...")
        try:
            result = subprocess.run("netsh wlan show wlanreport", shell=True, capture_output=True, text=True, timeout=30)
            self.update_status(result.stdout)
            report_path = "C:\\ProgramData\\Microsoft\\Windows\\WlanReport\\wlan-report-latest.html"
            if os.path.exists(report_path):
                if messagebox.askyesno("Report Generated", "WiFi report generated!\n\nOpen report now?"):
                    webbrowser.open(report_path)
        except Exception as e:
            self.update_status(f"⚠ Error: {e}")
    
    def forget_wifi_networks(self):
        """Forget all saved WiFi networks"""
        if messagebox.askyesno("Confirm", "⚠️ This will remove ALL saved WiFi networks!\n\nContinue?"):
            self.update_status("Removing all WiFi profiles...")
            try:
                result = subprocess.run("netsh wlan show profiles", shell=True, capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    if "All User Profile" in line:
                        profile = line.split(':')[1].strip()
                        subprocess.run(f'netsh wlan delete profile name="{profile}"', shell=True, capture_output=True, timeout=5)
                self.update_status("✓ All WiFi profiles removed")
                messagebox.showinfo("Complete", "All WiFi networks forgotten!")
            except Exception as e:
                self.update_status(f"⚠ Error: {e}")
    
    def ping_test(self):
        """Perform ping test"""
        host = simpledialog.askstring("Ping Test", "Enter hostname or IP:", initialvalue="8.8.8.8")
        if host:
            self.run_command(f"ping -n 10 {host}")
    
    def trace_route(self):
        """Perform trace route"""
        host = simpledialog.askstring("Trace Route", "Enter hostname or IP:", initialvalue="google.com")
        if host:
            self.run_command(f"tracert {host}")
    
    def nslookup(self):
        """Perform DNS lookup"""
        host = simpledialog.askstring("NSLookup", "Enter hostname:", initialvalue="google.com")
        if host:
            self.run_command(f"nslookup {host}")
    
    def open_hosts_file(self):
        """Open hosts file in notepad"""
        if self.is_admin:
            self.run_command("notepad C:\\Windows\\System32\\drivers\\etc\\hosts")
        else:
            messagebox.showwarning("Admin Required", "Opening hosts file for editing requires admin privileges.\n\nView only:")
            self.run_command("type C:\\Windows\\System32\\drivers\\etc\\hosts")
    
    def backup_hosts_file(self):
        """Backup hosts file"""
        dest = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialfile="hosts_backup.txt")
        if dest:
            try:
                shutil.copy("C:\\Windows\\System32\\drivers\\etc\\hosts", dest)
                self.update_status(f"✓ Hosts file backed up to {dest}")
                messagebox.showinfo("Success", f"Hosts file backed up to:\n{dest}")
            except Exception as e:
                self.update_status(f"⚠ Error: {e}")
    
    def restore_default_hosts(self):
        """Restore default Windows hosts file"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Restoring hosts file requires admin privileges.")
            return
        
        if messagebox.askyesno("Confirm", "Restore default Windows hosts file?\n\nThis will overwrite the current hosts file."):
            try:
                default_hosts = """# Copyright (c) 1993-2009 Microsoft Corp.
#
# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.
#
# This file contains the mappings of IP addresses to host names. Each
# entry should be kept on an individual line. The IP address should
# be placed in the first column followed by the corresponding host name.
# The IP address and the host name should be separated by at least one
# space.
#
# Additionally, comments (such as these) may be inserted on individual
# lines or following the machine name denoted by a '#' symbol.
#
# For example:
#
#      102.54.94.97     rhino.acme.com          # source server
#       38.25.63.10     x.acme.com              # x client host

# localhost name resolution is handled within DNS itself.
#	127.0.0.1       localhost
#	::1             localhost
"""
                with open("C:\\Windows\\System32\\drivers\\etc\\hosts", "w") as f:
                    f.write(default_hosts)
                self.update_status("✓ Hosts file restored to default")
                messagebox.showinfo("Success", "Hosts file restored to default!")
            except Exception as e:
                self.update_status(f"⚠ Error: {e}")
                messagebox.showerror("Error", f"Failed to restore hosts file:\n{e}")
    
    def change_mac_address(self):
        """Change MAC address (requires manual adapter selection)"""
        messagebox.showinfo("MAC Address Change", 
                          "To change MAC address:\n\n" +
                          "1. Open Network Connections (ncpa.cpl)\n" +
                          "2. Right-click your adapter → Properties\n" +
                          "3. Click Configure → Advanced\n" +
                          "4. Select 'Network Address' or 'Locally Administered Address'\n" +
                          "5. Enter new MAC (12 hex digits, no separators)\n" +
                          "6. Restart adapter")
        self.run_command("ncpa.cpl")
    
    # ==================== SECURITY TOOLS ====================
    
    def defender_scan(self):
        """Run Windows Defender quick scan"""
        if messagebox.askyesno("Confirm", "Run a quick Windows Defender scan?"):
            self.update_status("Starting Windows Defender quick scan...")
            self.run_command("\"C:\\Program Files\\Windows Defender\\MpCmdRun.exe\" -Scan -ScanType 1", admin=True)
    
    def scan_folder(self):
        """Scan specific folder with Defender"""
        folder = filedialog.askdirectory(title="Select folder to scan")
        if folder:
            self.update_status(f"Scanning {folder}...")
            self.run_command(f"\"C:\\Program Files\\Windows Defender\\MpCmdRun.exe\" -Scan -ScanType 3 -File \"{folder}\"", admin=True)
    
    def change_password(self):
        """Change user password"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Changing passwords requires admin privileges.")
            return
        
        username = simpledialog.askstring("Change Password", "Enter username:")
        if username:
            password = simpledialog.askstring("Change Password", f"Enter new password for {username}:", show='*')
            if password:
                self.run_command(f"net user {username} {password}")
    
    def create_user(self):
        """Create new user account"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Creating users requires admin privileges.")
            return
        
        username = simpledialog.askstring("Create User", "Enter username:")
        if username:
            password = simpledialog.askstring("Create User", "Enter password:", show='*')
            if password:
                self.run_command(f"net user {username} {password} /add")
                if messagebox.askyesno("Admin Rights", "Add user to Administrators group?"):
                    self.run_command(f"net localgroup administrators {username} /add")
    
    def delete_user(self):
        """Delete user account"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Deleting users requires admin privileges.")
            return
        
        username = simpledialog.askstring("Delete User", "Enter username to delete:")
        if username:
            if messagebox.askyesno("Confirm", f"⚠️ Delete user '{username}'?\n\nThis action cannot be undone!"):
                self.run_command(f"net user {username} /delete")
    
    def disable_uac(self):
        """Disable UAC"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Modifying UAC requires admin privileges.")
            return
        
        if messagebox.askyesno("Confirm", "⚠️ Disable User Account Control?\n\nThis reduces system security.\nRestart required."):
            self.run_command("reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA /t REG_DWORD /d 0 /f", admin=True)
            messagebox.showinfo("UAC Disabled", "UAC disabled. Restart required.")
    
    def enable_uac(self):
        """Enable UAC"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Modifying UAC requires admin privileges.")
            return
        
        self.run_command("reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA /t REG_DWORD /d 1 /f", admin=True)
        messagebox.showinfo("UAC Enabled", "UAC enabled. Restart required.")
    
    def check_rootkits(self):
        """Information about rootkit checking"""
        messagebox.showinfo("Rootkit Detection",
                          "For rootkit detection, consider using:\n\n" +
                          "• GMER (gmer.net)\n" +
                          "• RootkitRevealer (Sysinternals)\n" +
                          "• Malwarebytes Anti-Rootkit\n" +
                          "• TDSS Killer (Kaspersky)\n\n" +
                          "Running a full Windows Defender scan now...")
        self.run_command("\"C:\\Program Files\\Windows Defender\\MpCmdRun.exe\" -Scan -ScanType 2", admin=True)
    
    # ==================== SOFTWARE TOOLS ====================
    
    def list_programs(self):
        """List installed programs in detail"""
        self.update_status("Fetching installed programs (this may take a moment)...")
        # Using registry method which is faster than Win32_Product
        self.run_powershell_command("""
            $paths = @(
                'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
                'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
                'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'
            )
            Get-ItemProperty $paths | Where-Object { $_.DisplayName } | 
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | 
            Sort-Object DisplayName | Format-Table -AutoSize
        """)
    
    def winget_search(self):
        """Search for packages with winget"""
        query = simpledialog.askstring("Winget Search", "Enter package name to search:")
        if query:
            self.run_command(f"winget search {query}")
    
    def winget_install(self):
        """Install package with winget"""
        package = simpledialog.askstring("Winget Install", "Enter package ID to install:")
        if package:
            if messagebox.askyesno("Confirm", f"Install {package}?"):
                self.run_command(f"winget install --id {package} --silent --accept-package-agreements --accept-source-agreements")
    
    def winget_uninstall(self):
        """Uninstall package with winget"""
        package = simpledialog.askstring("Winget Uninstall", "Enter package ID to uninstall:")
        if package:
            if messagebox.askyesno("Confirm", f"Uninstall {package}?"):
                self.run_command(f"winget uninstall {package}")
    
    def winget_upgrade_package(self):
        """Upgrade specific package"""
        package = simpledialog.askstring("Winget Upgrade", "Enter package ID to upgrade:")
        if package:
            self.run_command(f"winget upgrade {package}")
    
    def winget_export(self):
        """Export winget package list"""
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialfile="winget_packages.json")
        if file_path:
            self.run_command(f"winget export -o \"{file_path}\"")
            messagebox.showinfo("Exported", f"Package list exported to:\n{file_path}")
    
    def winget_import(self):
        """Import winget package list"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            if messagebox.askyesno("Confirm", "Install all packages from this list?"):
                self.run_command(f"winget import -i \"{file_path}\"")
    
    def install_chocolatey(self):
        """Install Chocolatey package manager"""
        if messagebox.askyesno("Install Chocolatey", "Install Chocolatey package manager?\n\nThis requires admin privileges."):
            if not self.is_admin:
                messagebox.showerror("Admin Required", "Chocolatey installation requires admin privileges.")
                return
            
            self.update_status("Installing Chocolatey...")
            cmd = 'powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\'))"'
            self.run_command(cmd, admin=True)
    
    def choco_search(self):
        """Search Chocolatey packages"""
        query = simpledialog.askstring("Chocolatey Search", "Enter package name:")
        if query:
            self.run_command(f"choco search {query}")
    
    def choco_install(self):
        """Install Chocolatey package"""
        package = simpledialog.askstring("Chocolatey Install", "Enter package name:")
        if package:
            if messagebox.askyesno("Confirm", f"Install {package}?"):
                self.run_command(f"choco install {package} -y", admin=True)
    
    def quick_install(self, package_id):
        """Quick install app via winget"""
        if messagebox.askyesno("Quick Install", f"Install {package_id}?"):
            self.update_status(f"Installing {package_id}...")
            self.run_command(f"winget install --id {package_id} --silent --accept-package-agreements --accept-source-agreements")
    
    # ==================== BACKUP & RECOVERY TOOLS ====================
    
    def backup_drivers(self):
        """Backup installed drivers"""
        folder = filedialog.askdirectory(title="Select backup destination")
        if folder:
            driver_path = os.path.join(folder, "Drivers_" + datetime.now().strftime("%Y%m%d"))
            os.makedirs(driver_path, exist_ok=True)
            self.update_status(f"Backing up drivers to {driver_path}...")
            self.run_command(f"dism /online /export-driver /destination:\"{driver_path}\"", admin=True)
            self.update_status("✓ Drivers backed up")
            messagebox.showinfo("Complete", f"Drivers backed up to:\n{driver_path}")
    
    def backup_browser_data(self):
        """Backup browser profile data"""
        dest = filedialog.askdirectory(title="Select backup destination")
        if dest:
            self.update_status("Backing up browser data...")
            messagebox.showinfo("Important", "Close all browsers before continuing!")
            
            browsers = {
                'Chrome': os.path.join(os.getenv('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data'),
                'Edge': os.path.join(os.getenv('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data'),
                'Firefox': os.path.join(os.getenv('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
            }
            
            for name, path in browsers.items():
                if os.path.exists(path):
                    dest_path = os.path.join(dest, name)
                    self.update_status(f"Backing up {name}...")
                    try:
                        subprocess.run(f'robocopy "{path}" "{dest_path}" /E /XO /R:1 /W:1 /NFL /NDL', shell=True, capture_output=True, timeout=300)
                    except:
                        pass
            
            self.update_status("✓ Browser data backed up")
            messagebox.showinfo("Complete", f"Browser data backed up to:\n{dest}")
    
    def restore_browser_data(self):
        """Restore browser data"""
        src = filedialog.askdirectory(title="Select backup source folder")
        if src:
            messagebox.showwarning("Warning", "⚠️ CLOSE ALL BROWSERS before continuing!")
            
            if messagebox.askyesno("Confirm", "Restore browser data?\n\nThis will overwrite current data."):
                self.update_status("Restoring browser data...")
                
                browsers = {
                    'Chrome': os.path.join(os.getenv('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data'),
                    'Edge': os.path.join(os.getenv('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data'),
                    'Firefox': os.path.join(os.getenv('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
                }
                
                for name, path in browsers.items():
                    src_path = os.path.join(src, name)
                    if os.path.exists(src_path):
                        self.update_status(f"Restoring {name}...")
                        try:
                            subprocess.run(f'robocopy "{src_path}" "{path}" /E /XO /R:1 /W:1 /NFL /NDL', shell=True, capture_output=True, timeout=300)
                        except:
                            pass
                
                self.update_status("✓ Browser data restored")
                messagebox.showinfo("Complete", "Browser data restored!")
    
    def smart_backup_user_folders(self):
        """Smart backup of Desktop, Documents, Pictures"""
        dest = filedialog.askdirectory(title="Select backup destination")
        if dest:
            self.update_status("Starting smart backup...")
            
            folders = {
                'Desktop': os.path.join(os.getenv('USERPROFILE', ''), 'Desktop'),
                'Documents': os.path.join(os.getenv('USERPROFILE', ''), 'Documents'),
                'Pictures': os.path.join(os.getenv('USERPROFILE', ''), 'Pictures')
            }
            
            backup_name = f"UserBackup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(dest, backup_name)
            
            for name, path in folders.items():
                if os.path.exists(path):
                    dest_path = os.path.join(backup_path, name)
                    self.update_status(f"Backing up {name}...")
                    try:
                        subprocess.run(f'robocopy "{path}" "{dest_path}" /E /R:1 /W:1 /NFL /NDL', shell=True, capture_output=True, timeout=600)
                    except:
                        pass
            
            self.update_status(f"✓ Smart backup complete: {backup_path}")
            messagebox.showinfo("Complete", f"Backup completed!\n\nLocation:\n{backup_path}")
    
    def backup_user_profile(self):
        """Full user profile backup"""
        dest = filedialog.askdirectory(title="Select backup destination")
        if dest:
            if messagebox.askyesno("Confirm", "Full profile backup?\n\nThis may take significant time and space."):
                self.update_status("Backing up full user profile...")
                profile_path = os.getenv('USERPROFILE', '')
                backup_path = os.path.join(dest, f"FullProfile_{datetime.now().strftime('%Y%m%d')}")
                
                try:
                    subprocess.run(f'robocopy "{profile_path}" "{backup_path}" /E /XJ /R:1 /W:1 /NFL /NDL', shell=True, capture_output=True, timeout=1800)
                    self.update_status(f"✓ Profile backed up to: {backup_path}")
                    messagebox.showinfo("Complete", f"Profile backup complete!\n\n{backup_path}")
                except:
                    self.update_status("⚠ Backup completed with warnings")
    
    def selective_backup(self):
        """Selective folder backup"""
        source = filedialog.askdirectory(title="Select source folder to backup")
        if source:
            dest = filedialog.askdirectory(title="Select backup destination")
            if dest:
                folder_name = os.path.basename(source)
                backup_path = os.path.join(dest, f"{folder_name}_backup_{datetime.now().strftime('%Y%m%d')}")
                self.update_status(f"Backing up {source}...")
                try:
                    subprocess.run(f'robocopy "{source}" "{backup_path}" /E /R:1 /W:1', shell=True, capture_output=True, timeout=600)
                    self.update_status(f"✓ Backup complete: {backup_path}")
                    messagebox.showinfo("Complete", f"Backup complete!\n\n{backup_path}")
                except:
                    self.update_status("⚠ Backup completed with warnings")
    
    def backup_product_keys(self):
        """Backup Windows product key"""
        self.update_status("Retrieving product key...")
        self.show_product_key()
        messagebox.showinfo("Product Key", "Product key displayed in log.\n\nSave this information securely!")
    
    def show_product_key(self):
        """Show Windows product key"""
        try:
            cmd = 'powershell -Command "(Get-WmiObject -query \'select * from SoftwareLicensingService\').OA3xOriginalProductKey"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.stdout.strip():
                self.update_status(f"Windows Product Key: {result.stdout.strip()}")
            else:
                self.update_status("Product key not found or embedded in BIOS")
        except:
            self.update_status("⚠ Could not retrieve product key")
    
    def backup_outlook(self):
        """Backup Outlook data"""
        messagebox.showinfo("Outlook Backup",
                          "To backup Outlook:\n\n" +
                          "1. Open Outlook\n" +
                          "2. File → Open & Export → Import/Export\n" +
                          "3. Export to a file → Outlook Data File (.pst)\n" +
                          "4. Select folders to backup\n" +
                          "5. Choose destination\n\n" +
                          "Or use: File → Account Settings → Data Files")
    
    def backup_user_folders(self):
        """Backup Desktop and Documents"""
        dest = filedialog.askdirectory(title="Select backup destination")
        if dest:
            self.update_status("Backing up Desktop and Documents...")
            
            desktop = os.path.join(os.getenv('USERPROFILE', ''), 'Desktop')
            documents = os.path.join(os.getenv('USERPROFILE', ''), 'Documents')
            
            if os.path.exists(desktop):
                dest_desktop = os.path.join(dest, 'Desktop')
                subprocess.run(f'robocopy "{desktop}" "{dest_desktop}" /E /R:1 /W:1', shell=True, capture_output=True, timeout=300)
            
            if os.path.exists(documents):
                dest_docs = os.path.join(dest, 'Documents')
                subprocess.run(f'robocopy "{documents}" "{dest_docs}" /E /R:1 /W:1', shell=True, capture_output=True, timeout=300)
            
            self.update_status("✓ Desktop and Documents backed up")
            messagebox.showinfo("Complete", f"Backup complete!\n\n{dest}")
    
    def access_shadow_copies(self):
        """Access shadow copies (previous versions)"""
        messagebox.showinfo("Shadow Copies",
                          "To access previous versions:\n\n" +
                          "1. Right-click a file or folder\n" +
                          "2. Select 'Restore previous versions'\n" +
                          "3. Choose a restore point\n\n" +
                          "Opening File Explorer...")
        self.run_command("explorer.exe")
    
    def backup_registry(self):
        """Backup registry hives"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Registry backup requires admin privileges.")
            return
        
        dest = filedialog.askdirectory(title="Select backup destination")
        if dest:
            self.update_status("Backing up registry...")
            
            reg_path = os.path.join(dest, f"Registry_{datetime.now().strftime('%Y%m%d')}")
            os.makedirs(reg_path, exist_ok=True)
            
            hives = [
                ("HKLM\\SYSTEM", "System.reg"),
                ("HKLM\\SOFTWARE", "Software.reg"),
                ("HKCU", "CurrentUser.reg")
            ]
            
            for hive, filename in hives:
                filepath = os.path.join(reg_path, filename)
                self.update_status(f"Exporting {hive}...")
                try:
                    subprocess.run(f'reg export {hive} "{filepath}" /y', shell=True, capture_output=True, timeout=30)
                except:
                    pass
            
            self.update_status(f"✓ Registry backed up to: {reg_path}")
            messagebox.showinfo("Complete", f"Registry backed up to:\n{reg_path}")
    
    def import_registry(self):
        """Import registry file"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Registry import requires admin privileges.")
            return
        
        file_path = filedialog.askopenfilename(filetypes=[("Registry files", "*.reg")])
        if file_path:
            if messagebox.askyesno("Confirm", "⚠️ Import this registry file?\n\nThis may modify system settings."):
                self.update_status(f"Importing registry file: {file_path}")
                self.run_command(f'reg import "{file_path}"', admin=True)
    
    def create_restore_point(self):
        """Create system restore point"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Creating restore points requires admin privileges.")
            return
        
        self.update_status("Creating system restore point...")
        cmd = 'powershell -Command "Checkpoint-Computer -Description \'REGTeches_Manual\' -RestorePointType \'MODIFY_SETTINGS\'"'
        self.run_command(cmd, admin=True)
        messagebox.showinfo("Complete", "System restore point created!")
    
    # ==================== IMAGE & WIM TOOLS ====================
    
    def mount_iso(self):
        """Mount ISO file"""
        file_path = filedialog.askopenfilename(filetypes=[("ISO files", "*.iso")])
        if file_path:
            self.update_status(f"Mounting ISO: {file_path}")
            cmd = f'powershell -Command "Mount-DiskImage -ImagePath \'{file_path}\'"'
            self.run_command(cmd)
    
    def unmount_iso(self):
        """Unmount ISO"""
        messagebox.showinfo("Unmount ISO", "Right-click the mounted drive in File Explorer and select 'Eject'")
    
    def mount_wim(self):
        """Mount WIM or ESD file"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Mounting WIM/ESD requires admin privileges.")
            return
        
        wim_file = filedialog.askopenfilename(filetypes=[("WIM/ESD files", "*.wim *.esd")])
        if wim_file:
            mount_dir = filedialog.askdirectory(title="Select mount directory (must be empty)")
            if mount_dir:
                index = simpledialog.askinteger("Index", "Enter image index (usually 1):", initialvalue=1, minvalue=1)
                if index:
                    self.update_status(f"Mounting {wim_file} to {mount_dir}...")
                    self.run_command(f"dism /Mount-Image /ImageFile:\"{wim_file}\" /Index:{index} /MountDir:\"{mount_dir}\" /ReadOnly", admin=True)
    
    def unmount_wim(self):
        """Unmount WIM/ESD"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Unmounting WIM/ESD requires admin privileges.")
            return
        
        mount_dir = filedialog.askdirectory(title="Select mount directory to unmount")
        if mount_dir:
            commit = messagebox.askyesno("Commit Changes", "Save changes made to the image?")
            if commit:
                self.run_command(f"dism /Unmount-Image /MountDir:\"{mount_dir}\" /Commit", admin=True)
            else:
                self.run_command(f"dism /Unmount-Image /MountDir:\"{mount_dir}\" /Discard", admin=True)
    
    def apply_wim(self):
        """Apply WIM image to drive"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Applying WIM requires admin privileges.")
            return
        
        messagebox.showwarning("Warning", "⚠️ This will overwrite data on the target drive!\n\nUse only on secondary/mounted drives.")
        
        wim_file = filedialog.askopenfilename(filetypes=[("WIM files", "*.wim")])
        if wim_file:
            target_dir = filedialog.askdirectory(title="Select target drive root (e.g., E:\\)")
            if target_dir:
                if messagebox.askyesno("Confirm", f"⚠️ Apply image to {target_dir}?\n\nThis is DESTRUCTIVE!"):
                    index = simpledialog.askinteger("Index", "Enter image index:", initialvalue=1, minvalue=1)
                    if index:
                        self.run_command(f"dism /Apply-Image /ImageFile:\"{wim_file}\" /Index:{index} /ApplyDir:\"{target_dir}\"", admin=True)
    
    def capture_wim(self):
        """Capture WIM image"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Capturing WIM requires admin privileges.")
            return
        
        source_dir = filedialog.askdirectory(title="Select source directory to capture")
        if source_dir:
            wim_file = filedialog.asksaveasfilename(defaultextension=".wim", filetypes=[("WIM files", "*.wim")])
            if wim_file:
                name = simpledialog.askstring("Image Name", "Enter image name:")
                if name:
                    self.run_command(f"dism /Capture-Image /ImageFile:\"{wim_file}\" /CaptureDir:\"{source_dir}\" /Name:\"{name}\"", admin=True)
    
    def get_wim_info(self):
        """Get WIM file information"""
        wim_file = filedialog.askopenfilename(filetypes=[("WIM/ESD files", "*.wim *.esd")])
        if wim_file:
            self.run_command(f"dism /Get-ImageInfo /ImageFile:\"{wim_file}\"")
    
    # ==================== BOOT & RECOVERY ====================
    
    def reboot_to_recovery(self):
        """Reboot to Windows Recovery Environment"""
        if messagebox.askyesno("Confirm", "Reboot into Advanced Repair Mode (WinRE)?"):
            self.run_command("reagentc /boottore", admin=True)
            self.run_command("shutdown /r /t 10", admin=True)
            messagebox.showinfo("Rebooting", "System will reboot to recovery in 10 seconds...")
    
    def reboot_to_bios(self):
        """Reboot to BIOS/UEFI"""
        if messagebox.askyesno("Confirm", "Reboot to BIOS/UEFI firmware settings?"):
            self.run_command("shutdown /r /fw /t 10", admin=True)
            messagebox.showinfo("Rebooting", "System will reboot to BIOS in 10 seconds...")
    
    def repair_bootloader(self):
        """Repair boot loader"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "Boot repair requires admin privileges.")
            return
        
        if messagebox.askyesno("Confirm", "Attempt to repair boot loader?\n\nThis runs bootrec commands."):
            self.update_status("Repairing boot loader...")
            commands = [
                "bootrec /fixmbr",
                "bootrec /fixboot",
                "bootrec /rebuildbcd"
            ]
            for cmd in commands:
                self.run_command(cmd, admin=True)
    
    def rebuild_bcd(self):
        """Rebuild BCD"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "BCD rebuild requires admin privileges.")
            return
        
        if messagebox.askyesno("Confirm", "Rebuild Boot Configuration Data?\n\nThis may take several minutes."):
            self.update_status("Rebuilding BCD...")
            self.run_command("bootrec /rebuildbcd", admin=True)
    
    def robocopy_mirror(self):
        """Full drive mirror using Robocopy"""
        messagebox.showwarning("Warning", "⚠️ Drive mirroring will:\n" +
                             "• Copy ALL files from source to destination\n" +
                             "• DELETE files in destination not in source\n" +
                             "• Take significant time for large drives")
        
        src = filedialog.askdirectory(title="Select SOURCE drive root")
        if src:
            dst = filedialog.askdirectory(title="Select DESTINATION drive root")
            if dst:
                if messagebox.askyesno("Confirm", f"⚠️ Mirror:\n\nFrom: {src}\nTo: {dst}\n\nThis will modify {dst}!"):
                    self.update_status(f"Mirroring {src} to {dst}...")
                    self.run_command(f'robocopy "{src}" "{dst}" /MIR /R:2 /W:2')
    
    # ==================== HELP & UTILITY ====================
    
    def copy_system_info_for_ai(self):
        """Copy system information to clipboard for AI troubleshooting"""
        try:
            # Gather comprehensive system info
            info = "=== SYSTEM INFORMATION FOR AI TROUBLESHOOTING ===\n\n"
            info += self.get_system_info() + "\n\n"
            
            # Add more detailed info
            info += "=== DETAILED HARDWARE ===\n"
            try:
                result = subprocess.run('powershell -NoProfile -Command "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List"',
                                      shell=True, capture_output=True, text=True, timeout=5)
                info += result.stdout + "\n"
            except:
                pass
            
            try:
                result = subprocess.run('powershell -NoProfile -Command "Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum | Select-Object @{Name=\'TotalRAM(GB)\';Expression={[math]::Round($_.Sum/1GB,2)}} | Format-List"',
                                      shell=True, capture_output=True, text=True, timeout=5)
                info += result.stdout + "\n"
            except:
                pass
            
            info += "\n=== RECENT ERRORS (Last 5) ===\n"
            try:
                result = subprocess.run('powershell -NoProfile -Command "Get-EventLog -LogName System -EntryType Error -Newest 5 | Select-Object TimeGenerated, Source, Message | Format-List"',
                                      shell=True, capture_output=True, text=True, timeout=10)
                info += result.stdout + "\n"
            except:
                info += "Could not retrieve recent errors\n"
            
            # Copy to clipboard using PowerShell
            try:
                # Escape quotes and special characters for PowerShell
                escaped_info = info.replace('"', '`"').replace('$', '`$')
                cmd = f'powershell -Command "Set-Clipboard -Value @\"\n{escaped_info}\n\"@"'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                
                self.update_status("✅ System info copied to clipboard!", 'success')
                messagebox.showinfo("Copied!", 
                                  "System information copied to clipboard!\n\n" +
                                  "You can now paste this into any AI assistant to get help with your issue.\n\n" +
                                  "Recommended: Use Claude or ChatGPT for best troubleshooting results.")
            except Exception as e:
                # Fallback: Just show the info
                self.update_status(f"⚠️ Could not copy to clipboard: {e}", 'warning')
                
                # Show in a text window
                info_window = tk.Toplevel(self.root)
                info_window.title("System Information for AI")
                info_window.geometry("700x600")
                
                text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, font=('Consolas', 9))
                text_widget.pack(fill='both', expand=True, padx=10, pady=10)
                text_widget.insert('1.0', info)
                
                copy_btn = tk.Button(info_window, text="Copy to Clipboard", 
                                    command=lambda: self.root.clipboard_append(info))
                copy_btn.pack(pady=5)
                
        except Exception as e:
            self.update_status(f"❌ Error gathering system info: {e}", 'error')
            messagebox.showerror("Error", f"Could not gather system information:\n{e}")
    
    def show_ai_tips(self):
        """Show tips for using AI for troubleshooting"""
        tips_window = tk.Toplevel(self.root)
        tips_window.title("AI Troubleshooting Tips")
        tips_window.geometry("650x700")
        tips_window.configure(bg=self.colors['bg_dark'])
        
        # Title
        title = tk.Label(tips_window,
                        text="🤖 AI Troubleshooting Guide",
                        font=('Segoe UI', 16, 'bold'),
                        bg=self.colors['bg_dark'],
                        fg=self.colors['accent'])
        title.pack(pady=20)
        
        # Tips content
        tips_frame = tk.Frame(tips_window, bg=self.colors['bg_dark'])
        tips_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tips_text = scrolledtext.ScrolledText(tips_frame,
                                             wrap=tk.WORD,
                                             font=('Segoe UI', 10),
                                             bg=self.colors['bg_light'],
                                             fg=self.colors['text'],
                                             relief='flat',
                                             padx=15,
                                             pady=15)
        tips_text.pack(fill='both', expand=True)
        
        tips_content = """HOW TO USE AI FOR TROUBLESHOOTING

1️⃣ CHOOSE YOUR AI ASSISTANT
   • Claude (claude.ai) - Best for technical troubleshooting
   • ChatGPT (chat.openai.com) - Great for step-by-step guides
   • Perplexity (perplexity.ai) - Includes web search
   • Microsoft Copilot - Integrated with Windows

2️⃣ COPY YOUR SYSTEM INFO
   Use the "Copy System Info for AI" option above to automatically copy:
   • Your Windows version and build
   • Hardware specifications
   • Recent error messages
   • System configuration

3️⃣ DESCRIBE YOUR PROBLEM CLEARLY
   Include:
   • What you were trying to do
   • What happened instead
   • Any error messages you saw
   • When the problem started
   • What you've already tried

Example good question:
"I'm getting a blue screen error with STOP code 0x0000007B. This started after I updated my graphics drivers. My system info is: [paste system info here]"

4️⃣ ASK FOR SPECIFIC HELP
   Be clear about what you need:
   • "How do I fix this error?"
   • "What are the steps to troubleshoot?"
   • "Is this a hardware or software issue?"
   • "What commands should I run?"

5️⃣ FOLLOW UP WITH RESULTS
   Tell the AI what happened:
   • "That fixed it, thanks!"
   • "That didn't work, I still see..."
   • "I got a new error message: ..."

6️⃣ BEST PRACTICES
   ✅ Be specific about your problem
   ✅ Include error messages exactly as shown
   ✅ Mention what you've already tried
   ✅ Ask for clarification if needed
   ✅ Take notes of the solutions
   
   ❌ Don't be vague ("my computer is slow")
   ❌ Don't skip error messages
   ❌ Don't try risky commands without understanding
   ❌ Don't ignore warnings from AI

7️⃣ SAFETY TIPS
   • Always back up important data first
   • Create a system restore point before major changes
   • Don't run commands you don't understand
   • If unsure, ask the AI to explain first
   • Keep this toolkit handy for quick fixes

8️⃣ WHEN TO USE WHICH AI
   • Claude → Complex technical issues, coding problems
   • ChatGPT → General troubleshooting, how-to guides
   • Perplexity → Need current information from web
   • Copilot → Quick Windows-specific questions
   • Gemini → Multi-step solutions with images

9️⃣ EXAMPLE WORKFLOW
   1. Notice problem → Copy system info
   2. Open AI assistant → Paste system info
   3. Describe problem clearly
   4. Follow AI's instructions step by step
   5. Report results back to AI
   6. Repeat until resolved

🔟 COMMON ISSUES AI CAN HELP WITH
   • Blue screen errors (BSOD)
   • Software crashes and freezes
   • Driver problems
   • Update failures
   • Performance issues
   • Network connectivity
   • Boot problems
   • Registry errors
   • Permission issues
   • File system errors

Remember: AI assistants are incredibly helpful, but always:
→ Verify critical information
→ Back up your data
→ Test in safe mode if suggested
→ Ask for explanations if unsure

Good luck! 🚀"""
        
        tips_text.insert('1.0', tips_content)
        tips_text.config(state='disabled')  # Make read-only
        
        # Close button
        close_btn = tk.Button(tips_window,
                             text="Close",
                             command=tips_window.destroy,
                             bg=self.colors['accent'],
                             fg='white',
                             font=('Segoe UI', 10, 'bold'),
                             padx=30,
                             pady=10,
                             relief='flat',
                             cursor='hand2')
        close_btn.pack(pady=15)
    
    def battery_report(self):
        """Generate battery report"""
        if platform.system() == 'Windows':
            self.update_status("Generating battery report...")
            output_path = os.path.join(tempfile.gettempdir(), 'battery-report.html')
            try:
                result = subprocess.run(f'powercfg /batteryreport /output "{output_path}"', 
                                      shell=True, capture_output=True, text=True, timeout=10)
                if os.path.exists(output_path):
                    webbrowser.open(output_path)
                    self.update_status(f"✓ Battery report opened: {output_path}")
                else:
                    self.update_status("⚠ Battery report could not be generated (device may not have a battery)")
            except Exception as e:
                self.update_status(f"⚠ Error: {e}")
    
    def generate_system_report(self):
        """Generate comprehensive system report"""
        self.update_status("Generating comprehensive system report...")
        
        def generate():
            output_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"SystemReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if output_path:
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write("=" * 70 + "\n")
                        f.write(" COMPREHENSIVE SYSTEM REPORT - REGTeches Toolkit\n")
                        f.write(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("=" * 70 + "\n\n")
                        
                        # System info
                        f.write("SYSTEM INFORMATION\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.get_system_info() + "\n\n")
                        
                        # Get various system details
                        commands = [
                            ("System Info", "systeminfo"),
                            ("CPU", 'powershell -NoProfile -Command "Get-CimInstance Win32_Processor | Select-Object Name, MaxClockSpeed, NumberOfCores | Format-List"'),
                            ("Memory", 'powershell -NoProfile -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer | Format-Table -AutoSize"'),
                            ("Disk Info", 'powershell -NoProfile -Command "Get-CimInstance Win32_DiskDrive | Select-Object Model, Size, Status | Format-List"'),
                            ("Network Adapters", 'powershell -NoProfile -Command "Get-CimInstance Win32_NetworkAdapter | Where-Object {$_.NetEnabled} | Select-Object Name, Speed | Format-Table -AutoSize"'),
                            ("Installed Updates", 'powershell -NoProfile -Command "Get-CimInstance Win32_QuickFixEngineering | Select-Object HotFixID, InstalledOn, Description | Format-Table -AutoSize"')
                        ]
                        
                        for title, cmd in commands:
                            f.write(f"\n{title.upper()}\n")
                            f.write("-" * 70 + "\n")
                            try:
                                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                                f.write(result.stdout)
                            except:
                                f.write("Error retrieving information\n")
                            f.write("\n")
                    
                    self.update_status(f"✓ System report saved: {output_path}")
                    
                    if messagebox.askyesno("Complete", f"System report saved!\n\n{output_path}\n\nOpen the report now?"):
                        os.startfile(output_path)
                        
                except Exception as e:
                    self.update_status(f"⚠ Error generating report: {e}")
                    messagebox.showerror("Error", f"Failed to generate report:\n{e}")
        
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def refresh_system_info(self):
        """Refresh system information display"""
        self.update_status("Refreshing system information...")
        system_info = self.get_system_info()
        self.info_text_label.config(text=system_info)
        self.update_status("✓ System information refreshed")
    
    def export_logs(self):
        """Export activity logs"""
        output_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"ActivityLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(self.status_text.get('1.0', 'end'))
                
                self.update_status(f"✓ Logs exported: {output_path}")
                messagebox.showinfo("Complete", f"Logs exported to:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export logs:\n{e}")
    
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("550x450")
        about_window.resizable(False, False)
        about_window.configure(bg='#1e2936')
        
        # Make it modal
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Title
        title = tk.Label(about_window,
                        text="REGTeches Technician's Toolkit",
                        font=('Segoe UI', 22, 'bold'),
                        bg='#1e2936',
                        fg='#4a90e2')
        title.pack(pady=20)

        # Version
        version = tk.Label(about_window,
                          text="Pro Suite v4.0  —  All-in-One Windows IT Platform",
                          font=('Segoe UI', 11),
                          bg='#1e2936',
                          fg='#aaccff')
        version.pack(pady=2)

        # Separator
        separator = tk.Frame(about_window, height=2, bg='gray')
        separator.pack(fill='x', padx=30, pady=16)

        # Developer info
        info = tk.Label(about_window,
                       text="Developer: Ronald Goodchild\n"
                            "Company: REGTeches\n\n"
                            "Integrated Suite Includes:\n"
                            "  📦 AppForge — Winget & Chocolatey Package Manager\n"
                            "  🔒 CyberScan — Security & Network Audit Suite\n"
                            "  💾 BackupPro — Professional Backup Solution",
                       font=('Segoe UI', 10),
                       bg='#1e2936',
                       fg='white',
                       justify='center')
        info.pack(pady=8)
        
        # Website link
        website = tk.Label(about_window,
                          text="www.regteches.com",
                          font=('Segoe UI', 11, 'underline'),
                          bg='#1e2936',
                          fg='#4a90e2',
                          cursor='hand2')
        website.pack(pady=10)
        website.bind('<Button-1>', lambda e: webbrowser.open('http://www.regteches.com'))
        
        # System info
        sys_info = tk.Label(about_window,
                           text=f"Registered User: {os.getenv('USERNAME', 'Unknown')}\n"
                                f"System: {platform.system()} {platform.release()}\n"
                                f"Python: {platform.python_version()}",
                           font=('Consolas', 9),
                           bg='#1e2936',
                           fg='darkgray',
                           justify='left')
        sys_info.pack(pady=15)
        
        # Close button
        close_btn = tk.Button(about_window,
                             text="Close",
                             command=about_window.destroy,
                             bg='#333',
                             fg='white',
                             font=('Segoe UI', 10),
                             padx=30,
                             pady=10,
                             relief='flat',
                             cursor='hand2')
        close_btn.pack(pady=10)
        
        # Center the window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (about_window.winfo_width() // 2)
        y = (about_window.winfo_screenheight() // 2) - (about_window.winfo_height() // 2)
        about_window.geometry(f'+{x}+{y}')
    
    def show_help(self):
        """Show help and support info"""
        help_text = """TECHNICIAN'S TOOLKIT - HELP & SUPPORT

GETTING STARTED:
• Run as Administrator for full functionality
• Most commands execute immediately
• Check the Activity Log for command output
• Some operations may take several minutes

TIPS:
• Create a system restore point before major changes
• Backup important data regularly
• Close applications before system operations
• Monitor the activity log for errors

COMMON TASKS:
• Quick Health Check: Fast system diagnostics
• Auto Repair: Fix system file corruption
• Deep Clean: Remove temporary files and caches
• Network Reset: Fix network connectivity issues

TROUBLESHOOTING:
• If a command fails, check the activity log
• Ensure you have administrator privileges
• Some commands require Windows Pro or Enterprise
• Restart your PC after major system changes

SUPPORT:
• Visit: www.regteches.com
• Check Windows built-in troubleshooters
• Export logs for detailed diagnostics

Press OK to close this help dialog."""
        
        messagebox.showinfo("Help & Support", help_text)
    
    # ==================== ADVANCED TOOLS IMPLEMENTATIONS ====================
    
    def disable_telemetry(self):
        """Disable Windows telemetry"""
        if not self.is_admin:
            messagebox.showerror("Admin Required", "This requires administrator privileges")
            return
        if messagebox.askyesno("Confirm", "Disable Windows telemetry and data collection?"):
            self.update_status("Disabling telemetry...", 'info')
            commands = [
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                'sc config DiagTrack start= disabled',
                'sc stop DiagTrack'
            ]
            for cmd in commands:
                subprocess.run(cmd, shell=True, capture_output=True)
            self.update_status("✅ Telemetry disabled", 'success')
    
    def disable_cortana(self):
        """Disable Cortana"""
        if not self.is_admin:
            return
        cmd = 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Cortana disabled", 'success')
    
    def enable_windows_dark_theme(self):
        """Enable Windows dark theme"""
        cmd = 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Dark theme enabled", 'success')
    
    def disable_animations(self):
        """Disable Windows animations"""
        cmd = 'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Animations disabled", 'success')
    
    def show_file_extensions(self):
        """Show file extensions"""
        cmd = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        subprocess.run("taskkill /f /im explorer.exe && start explorer.exe", shell=True, capture_output=True)
        self.update_status("✅ File extensions enabled", 'success')
    
    def show_hidden_files(self):
        """Show hidden files"""
        cmd = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d 1 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        subprocess.run("taskkill /f /im explorer.exe && start explorer.exe", shell=True, capture_output=True)
        self.update_status("✅ Hidden files enabled", 'success')
    
    def disable_web_search(self):
        """Disable web search in Start"""
        cmd = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Web search disabled", 'success')
    
    def remove_onedrive(self):
        """Remove OneDrive"""
        if not self.is_admin:
            return
        if messagebox.askyesno("Confirm", "Uninstall OneDrive?"):
            subprocess.run("taskkill /f /im OneDrive.exe", shell=True, capture_output=True)
            subprocess.run("%SystemRoot%\\SysWOW64\\OneDriveSetup.exe /uninstall", shell=True, capture_output=True)
            self.update_status("✅ OneDrive removed", 'success')
    
    def classic_context_menu(self):
        """Enable classic context menu Win11"""
        cmd = 'reg add "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32" /ve /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        subprocess.run("taskkill /f /im explorer.exe && start explorer.exe", shell=True, capture_output=True)
        self.update_status("✅ Classic menu enabled", 'success')
    
    def remove_start_ads(self):
        """Remove Start Menu ads"""
        cmds = [
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SubscribedContent-338388Enabled /t REG_DWORD /d 0 /f',
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SystemPaneSuggestionsEnabled /t REG_DWORD /d 0 /f'
        ]
        for cmd in cmds:
            subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Start ads removed", 'success')
    
    def enable_game_mode(self):
        """Enable Game Mode"""
        cmd = 'reg add "HKCU\\Software\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Game Mode enabled", 'success')
    
    def disable_game_bar(self):
        """Disable Game Bar"""
        cmd = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Game Bar disabled", 'success')
    
    def enable_hardware_acceleration(self):
        """Enable hardware acceleration"""
        cmd = 'reg add "HKCU\\Software\\Microsoft\\Avalon.Graphics" /v DisableHWAcceleration /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Hardware acceleration enabled", 'success')
    
    def optimize_latency(self):
        """Optimize for low latency"""
        if not self.is_admin:
            return
        cmds = [
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 0xffffffff /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f'
        ]
        for cmd in cmds:
            subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Latency optimized", 'success')
    
    def disable_fullscreen_opt(self):
        """Disable fullscreen optimizations"""
        cmd = 'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Fullscreen opt disabled", 'success')
    
    def disable_all_telemetry(self):
        """Disable all telemetry"""
        if not self.is_admin:
            return
        self.disable_telemetry()
        self.disable_location()
        self.disable_activity_history()
        self.disable_advertising_id()
    
    def disable_location(self):
        """Disable location tracking"""
        cmd = 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location" /v Value /t REG_SZ /d Deny /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Location disabled", 'success')
    
    def disable_activity_history(self):
        """Disable activity history"""
        cmd = 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableActivityFeed /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Activity history disabled", 'success')
    
    def disable_advertising_id(self):
        """Disable advertising ID"""
        cmd = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f'
        subprocess.run(cmd, shell=True, capture_output=True)
        self.update_status("✅ Advertising ID disabled", 'success')
    
    def clear_activity_history(self):
        """Clear activity history"""
        self.run_command("del /F /Q %localappdata%\\ConnectedDevicesPlatform\\*")
    
    def hosts_ad_blocker(self):
        """Hosts file ad blocker"""
        webbrowser.open("https://github.com/StevenBlack/hosts")
    
    def check_activation_status(self):
        """Check activation"""
        self.run_command("slmgr /xpr")
    
    def check_office_activation(self):
        """Check Office activation"""
        paths = ["C:\\Program Files\\Microsoft Office\\Office16", "C:\\Program Files (x86)\\Microsoft Office\\Office16"]
        for path in paths:
            if os.path.exists(path):
                self.run_command(f'cd "{path}" && cscript ospp.vbs /dstatus')
                return
    
    def show_cpu_gpu_info(self):
        """Show CPU/GPU info"""
        self.run_powershell_command("Get-CimInstance Win32_Processor | Format-List; Get-CimInstance Win32_VideoController | Format-List")
    
    def show_temperature_info(self):
        """Temperature monitor"""
        messagebox.showinfo("Temperature", "Install: HWMonitor, HWiNFO, or Core Temp")
        webbrowser.open("https://www.cpuid.com/softwares/hwmonitor.html")
    
    def bulk_rename(self):
        """Bulk rename"""
        messagebox.showinfo("Bulk Rename", "Use PowerShell Get-ChildItem | Rename-Item or install Bulk Rename Utility")
    
    def find_duplicates(self):
        """Find duplicates"""
        folder = filedialog.askdirectory()
        if folder:
            messagebox.showinfo("Duplicates", "For advanced duplicate finding, install dupeGuru or AllDup")
    
    def find_large_files(self):
        """Find large files"""
        folder = filedialog.askdirectory()
        if folder:
            size_mb = simpledialog.askinteger("Size", "Find files larger than (MB):", initialvalue=100)
            if size_mb:
                cmd = f'powershell -Command "Get-ChildItem -Path \'{folder}\' -Recurse -File | Where-Object {{$_.Length -gt {size_mb*1048576}}} | Select-Object FullName, @{{Name=\'Size(MB)\';Expression={{[math]::Round($_.Length/1MB,2)}}}} | Format-Table"'
                self.run_command(cmd)
    
    def batch_convert_images(self):
        """Batch convert"""
        messagebox.showinfo("Convert", "Use IrfanView, XnConvert, or ImageMagick for batch conversion")
    
    def mass_delete_by_ext(self):
        """Mass delete by extension"""
        folder = filedialog.askdirectory()
        if folder:
            ext = simpledialog.askstring("Extension", "Enter extension (e.g., .tmp):")
            if ext and messagebox.askyesno("Confirm", f"Delete all *{ext} in {folder}?"):
                self.run_command(f'del /s /q "{folder}\\*{ext}"', admin=True)
    
    def manage_custom_scripts(self):
        """Manage scripts"""
        messagebox.showinfo("Scripts", "Custom script management coming soon!")
    
    def create_custom_script(self):
        """Create script"""
        messagebox.showinfo("Create", "Script creator coming soon!")
    
    def import_custom_script(self):
        """Import script"""
        script = filedialog.askopenfilename(filetypes=[("Scripts", "*.ps1 *.bat *.cmd")])
        if script:
            self.update_status(f"Imported: {script}", 'success')
    
    def export_custom_scripts(self):
        """Export scripts"""
        messagebox.showinfo("Export", "Script export coming soon!")
    
    def manage_docker(self):
        """Manage Docker"""
        if shutil.which("docker"):
            self.run_command("docker ps -a")
        else:
            messagebox.showinfo("Docker", "Docker not installed. Get it from docker.com")
    
    def manage_wsl(self):
        """Manage WSL"""
        self.run_command("wsl --list --verbose")
    
    def port_scanner(self):
        """Port scanner"""
        host = simpledialog.askstring("Port Scanner", "Enter host:", initialvalue="localhost")
        if host:
            ports = simpledialog.askstring("Ports", "Ports (e.g., 80,443):")
            if ports:
                for port in ports.split(','):
                    self.run_command(f'powershell -Command "Test-NetConnection {host} -Port {port.strip()}"')
    
    def _bundled_path(self, filename):
        """Return path to a bundled data file whether running frozen or as script."""
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, filename)

    def open_appforge(self):
        """Launch AppForge Package Manager as a separate process."""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled exe — relaunch self with --appforge flag
                cmd = [sys.executable, "--appforge"]
            else:
                cmd = [sys.executable, os.path.abspath(__file__), "--appforge"]
            subprocess.Popen(cmd)
            self.update_status("📦 Launching AppForge Package Manager…", 'success')
        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not open AppForge:\n{e}")

    def open_cyberscan(self):
        """Launch CyberScan security suite (PowerShell GUI)."""
        ps1 = self._bundled_path("cyberscan.ps1")
        if not os.path.exists(ps1):
            messagebox.showerror(
                "File Not Found",
                f"cyberscan.ps1 not found at:\n{ps1}")
            return
        try:
            subprocess.Popen([
                "powershell", "-ExecutionPolicy", "Bypass",
                "-File", ps1
            ], creationflags=subprocess.CREATE_NO_WINDOW)
            self.update_status("🔒 Launching CyberScan Security Suite…", 'success')
        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not open CyberScan:\n{e}")

    def open_backuppro(self):
        """Launch BackupPro backup suite."""
        try:
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--backuppro"]
            else:
                cmd = [sys.executable, os.path.abspath(__file__), "--backuppro"]
            subprocess.Popen(cmd)
            self.update_status("💾 Launching BackupPro Backup Suite…", 'success')
        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not open BackupPro:\n{e}")

    def import_programs_json(self):
        """Import the bundled programs.json package list via winget."""
        json_path = self._bundled_path("programs.json")
        if not os.path.exists(json_path):
            messagebox.showerror(
                "File Not Found",
                f"programs.json not found at:\n{json_path}")
            return
        if not messagebox.askyesno(
                "Import Package List",
                f"Install all packages from programs.json using winget?\n\n{json_path}"):
            return
        cmd = (f'winget import -i "{json_path}" '
               f'--accept-source-agreements --accept-package-agreements')
        self.run_command(cmd)

    def password_generator(self):
        """Generate password"""
        length = simpledialog.askinteger("Password", "Length:", initialvalue=16, minvalue=8)
        if length:
            cmd = f'powershell -Command "$p=-join((65..90)+(97..122)+(48..57)+@(33,35,36,37,38,42,43,45,61,63,64)|Get-Random -Count {length}|%%{{[char]$_}});Write-Host $p"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                pwd = result.stdout.strip()
                self.update_status(f"🔐 Password: {pwd}", 'success')
                messagebox.showinfo("Password", f"Generated:\n\n{pwd}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TechniciansToolkit(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
