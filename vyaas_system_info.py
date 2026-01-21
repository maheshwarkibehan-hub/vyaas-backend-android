"""
VYAAS AI - System Info Module
Get system information like CPU, RAM, Battery, Disk usage
"""

import logging
from livekit.agents import function_tool

logger = logging.getLogger("vyaas_system_info")
logger.setLevel(logging.INFO)

@function_tool()
async def get_system_info() -> str:
    """
    Get complete system information including CPU, RAM, Battery and Disk.
    Returns:
        Comprehensive system status report
    """
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # RAM
        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)
        ram_percent = ram.percent
        
        # Disk - Use C: on Windows
        disk = psutil.disk_usage('C:/')
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        disk_percent = disk.percent
        
        # Battery
        battery = psutil.sensors_battery()
        if battery:
            battery_percent = battery.percent
            battery_charging = "Charging" if battery.power_plugged else "Not Charging"
            battery_info = f"Battery: {battery_percent}% ({battery_charging})"
        else:
            battery_info = "Battery: Desktop PC (No battery)"
        
        report = f"""
System Status:
- CPU: {cpu_percent}% usage ({cpu_count} cores)
- RAM: {ram_used_gb:.1f}GB / {ram_total_gb:.1f}GB ({ram_percent}%)
- Disk: {disk_used_gb:.0f}GB / {disk_total_gb:.0f}GB ({disk_percent}%)
- {battery_info}
"""
        return report.strip()
    except ImportError:
        return "psutil module not installed. Run: pip install psutil"
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return f"Error: {str(e)}"

@function_tool()
async def get_cpu_usage() -> str:
    """
    Get current CPU usage percentage.
    Returns:
        CPU usage percentage
    """
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        return f"CPU usage: {cpu_percent}%"
    except ImportError:
        return "psutil not installed"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool()
async def get_ram_usage() -> str:
    """
    Get current RAM/memory usage.
    Returns:
        RAM usage details
    """
    try:
        import psutil
        ram = psutil.virtual_memory()
        used_gb = ram.used / (1024**3)
        total_gb = ram.total / (1024**3)
        available_gb = ram.available / (1024**3)
        return f"RAM: {used_gb:.1f}GB used / {total_gb:.1f}GB total ({ram.percent}%). Available: {available_gb:.1f}GB"
    except ImportError:
        return "psutil not installed"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool()
async def get_battery_status() -> str:
    """
    Get battery status and charging info.
    Returns:
        Battery percentage and charging status
    """
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            status = "Charging ⚡" if battery.power_plugged else "On Battery 🔋"
            time_left = ""
            if battery.secsleft > 0 and not battery.power_plugged:
                hours = battery.secsleft // 3600
                mins = (battery.secsleft % 3600) // 60
                time_left = f" - {hours}h {mins}m remaining"
            return f"Battery: {battery.percent}% ({status}){time_left}"
        else:
            return "Desktop PC - No battery detected"
    except ImportError:
        return "psutil not installed"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool()
async def get_disk_usage() -> str:
    """
    Get disk space usage.
    Returns:
        Disk usage for main drive
    """
    try:
        import psutil
        disk = psutil.disk_usage('C:/')
        used_gb = disk.used / (1024**3)
        total_gb = disk.total / (1024**3)
        free_gb = disk.free / (1024**3)
        return f"Disk: {used_gb:.0f}GB used / {total_gb:.0f}GB total ({disk.percent}%). Free: {free_gb:.0f}GB"
    except ImportError:
        return "psutil not installed"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool()
async def get_running_processes(count: int = 5) -> str:
    """
    Get top running processes by CPU usage.
    Args:
        count: Number of top processes to show (default 5)
    Returns:
        List of top processes
    """
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'] or 0,
                    'memory': proc.info['memory_percent'] or 0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and get top N
        top_processes = sorted(processes, key=lambda x: x['cpu'], reverse=True)[:count]
        
        result = f"Top {count} processes by CPU:\n"
        for i, p in enumerate(top_processes, 1):
            result += f"{i}. {p['name']}: CPU {p['cpu']:.1f}%, RAM {p['memory']:.1f}%\n"
        
        return result.strip()
    except ImportError:
        return "psutil not installed"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool()
async def get_network_info() -> str:
    """
    Get network connection information.
    Returns:
        Network stats including bytes sent/received
    """
    try:
        import psutil
        net = psutil.net_io_counters()
        sent_mb = net.bytes_sent / (1024**2)
        recv_mb = net.bytes_recv / (1024**2)
        return f"Network: Sent {sent_mb:.1f}MB, Received {recv_mb:.1f}MB"
    except ImportError:
        return "psutil not installed"
    except Exception as e:
        return f"Error: {str(e)}"
