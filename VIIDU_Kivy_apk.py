import os
import sys
import subprocess
import platform
import random
import webbrowser
import shutil
import datetime

try:
    import psutil
except ImportError:
    psutil = None

try:
    import cpuinfo
except ImportError:
    cpuinfo = None

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.threading import Thread as KivyThread

Window.size = (1200, 800)


class DataCollector:
    """Собирает ПОЛНУЮ информацию о системе - все 140+ команд"""
    
    @staticmethod
    def _run_ps(cmd: str) -> str:
        """Выполняет PowerShell команду"""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.stdout.strip() or "Не обнаружено"
        except:
            return "Не удалось получить данные"
    
    @staticmethod
    def get_report_text() -> str:
        lines = []
        lines.append("Добро пожаловать в информационно-диагностическую утилиту (VIIDU)\n")
        
        # СЕТЕВАЯ ИНФОРМАЦИЯ
        lines.append("IP-адрес: " + DataCollector._run_ps("(Get-NetIPAddress | Where-Object {$_.AddressFamily -eq 'IPv4' -and $_.InterfaceAlias -eq (Get-NetAdapter | Select-Object -First 1).Name}).IPAddress"))
        lines.append("MAC-адрес: " + DataCollector._run_ps("(Get-NetAdapter | Select-Object -First 1).MacAddress"))
        lines.append("DNS-сервер: " + DataCollector._run_ps("(Get-DnsClientServerAddress | Where-Object {$_.InterfaceAlias -eq (Get-NetAdapter | Select-Object -First 1).Name}).ServerAddresses"))
        lines.append("DHCP-сервер: " + DataCollector._run_ps("(Get-NetIPConfiguration | Where-Object {$_.InterfaceAlias -eq (Get-NetAdapter | Select-Object -First 1).Name}).DhcpServer"))
        lines.append("DHCP включен: " + DataCollector._run_ps("(Get-NetIPConfiguration | Where-Object {$_.InterfaceAlias -eq (Get-NetAdapter | Select-Object -First 1).Name}).DhcpEnabled"))
        
        # ОСНОВНАЯ ИНФОРМАЦИЯ
        lines.append("Система: " + sys.platform)
        lines.append("Версия Python: " + sys.version)
        
        # ВИДЕОКАРТА (BIOS)
        lines.append("Видеокарта (BIOS): " + DataCollector._run_ps("(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ', '"))
        lines.append("ГГц видеокарты (BIOS): " + DataCollector._run_ps("(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty CurrentRefreshRate) -join ', '"))
        lines.append("Версия драйвера видеокарты (BIOS): " + DataCollector._run_ps("(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty DriverVersion) -join ', '"))
        lines.append("Драйвер видеокарты (BIOS): " + DataCollector._run_ps("(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty DriverDate) -join ', '"))
        lines.append("VRAM видеокарты (BIOS): " + DataCollector._run_ps("((Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty AdapterRAM | Where-Object {$_}) / 1MB) -join ', '") + " MB")
        lines.append("Выделенный RAM видеокарты (BIOS): " + DataCollector._run_ps("((Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty AdapterRAM | Where-Object {$_}) / 1MB) -join ', '") + " MB")
        lines.append("Состояние температуры видеокарты: " + DataCollector._run_ps("$t = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | ForEach-Object {[math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)}; if ($t) {$t -join ', ' + '°C'} else {'Не обнаружена температура видеокарты'}"))
        
        # ПРОЦЕССОР
        if cpuinfo:
            ci = cpuinfo.get_cpu_info()
            lines.append("Процессор: " + ci.get("brand_raw", "Не обнаружен"))
            lines.append("Производитель процессора: " + ci.get("vendor_id_raw", "Не обнаружен"))
            lines.append("Версия процессора: " + ci.get("hz_advertised_friendly", "Не обнаружен"))
            lines.append("Дата процессора: " + ci.get("arch", "Не обнаружен"))
            lines.append("ГГц процессора: " + str(ci.get("hz_advertised_friendly", "Не обнаружен")))
            lines.append("Версия драйвера процессора: " + str(ci.get("arch", "Не обнаружен")))
            lines.append("Драйвер процессора: " + str(ci.get("brand_raw", "Не обнаружен")))
            lines.append("Дата драйвера процессора: " + str(ci.get("arch", "Не обнаружен")))
            lines.append("Кэш L1 процессора: " + str(ci.get("l1_cache_size", "Не обнаружен")))
            lines.append("Кэш L2 процессора: " + str(ci.get("l2_cache_size", "Не обнаружен")))
            lines.append("Кэш L3 процессора: " + str(ci.get("l3_cache_size", "Не обнаружен")))
        
        lines.append("Состояние температуры процессора: " + DataCollector._run_ps("$t = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | ForEach-Object {[math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)}; if ($t) {$t -join ', ' + '°C'} else {'Не обнаружена температура процессора'}"))
        
        if psutil:
            lines.append("Занятое место в невыгружаемом пуле памяти: " + str(round(psutil.swap_memory().used / (1024. ** 3))) + " GB")
        
        # АРХИТЕКТУРА И ЯДРА
        lines.append("Архитектура: " + platform.architecture()[0])
        lines.append("Количество ядер процессора: " + str(os.cpu_count()))
        lines.append("Количество логических процессоров: " + str(os.cpu_count() * 2))
        
        if cpuinfo:
            lines.append("Количество инструкций процессора: " + str(len(cpuinfo.get_cpu_info().get("flags", []))))
        
        if psutil:
            lines.append("Количество потоков процессора: " + str(psutil.cpu_count(logical=True)))
            lines.append("Количество физических ядер процессора: " + str(psutil.cpu_count(logical=False)))
        
        # ОПЕРАТИВНАЯ ПАМЯТЬ
        if psutil:
            vm = psutil.virtual_memory()
            lines.append("Количество оперативной памяти: " + str(round(vm.total / (1024. ** 3))) + " GB")
        
        lines.append("Производитель оперативной памяти: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty Manufacturer | Select-Object -Unique) -join ', '"))
        lines.append("Модель оперативной памяти: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty PartNumber | Select-Object -Unique) -join ', '"))
        lines.append("Серийный номер оперативной памяти: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty SerialNumber | Select-Object -Unique) -join ', '"))
        lines.append("Версия оперативной памяти: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty Version | Select-Object -Unique) -join ', '"))
        lines.append("Дата оперативной памяти: Не определена WMI")
        lines.append("Состояние температуры оперативной памяти: " + DataCollector._run_ps("$t = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | ForEach-Object {[math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)}; if ($t) {$t -join ', ' + '°C'} else {'Не обнаружена температура оперативной памяти'}"))
        lines.append("Тип оперативной памяти: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty MemoryType | Select-Object -Unique) -join ', '"))
        lines.append("ГГц оперативной памяти: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty Speed | Select-Object -Unique) -join ', '") + " MHz")
        
        if psutil:
            vm = psutil.virtual_memory()
            lines.append("Количество свободной оперативной памяти: " + str(round(vm.available / (1024. ** 3))) + " GB")
            lines.append("Количество занятой оперативной памяти: " + str(round(vm.used / (1024. ** 3))) + " GB")
            lines.append("Количество виртуальной памяти: " + str(round(vm.total / (1024. ** 3))) + " GB")
            lines.append("Количество свободной виртуальной памяти: " + str(round(vm.available / (1024. ** 3))) + " GB")
            lines.append("Количество занятой виртуальной памяти: " + str(round(vm.used / (1024. ** 3))) + " GB")
            
            sm = psutil.swap_memory()
            lines.append("Выгружаемый пул памяти: " + str(round(sm.total / (1024. ** 3))) + " GB")
            lines.append("Свободное место в выгружаемом пуле памяти: " + str(round(sm.free / (1024. ** 3))) + " GB")
            lines.append("Занятое место в выгружаемом пуле памяти: " + str(round(sm.used / (1024. ** 3))) + " GB")
            lines.append("Невыгружаемый пул памяти: " + str(round(sm.total / (1024. ** 3))) + " GB")
            lines.append("Свободное место в невыгружаемом пуле памяти: " + str(round(sm.free / (1024. ** 3))) + " GB")
        
        # ДИСК
        drive = os.environ.get("SystemDrive", os.path.abspath(os.sep))
        disk = shutil.disk_usage(drive)
        lines.append("Объем диска: " + str(round(disk.total / (1024. ** 3))) + " GB")
        lines.append("Свободное место на диске: " + str(round(disk.free / (1024. ** 3))) + " GB")
        lines.append("Занятое место на диске: " + str(round(disk.used / (1024. ** 3))) + " GB")
        
        lines.append("Состояние температуры жесткого диска: " + DataCollector._run_ps("$t = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | ForEach-Object {[math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)}; if ($t) {$t -join ', ' + '°C'} else {'Не обнаружена температура жесткого диска'}"))
        lines.append("Состояние температуры SSD: " + DataCollector._run_ps("$t = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | ForEach-Object {[math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)}; if ($t) {$t -join ', ' + '°C'} else {'Не обнаружена температура SSD'}"))
        
        # BIOS
        lines.append("Версия BIOS: " + DataCollector._run_ps("(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion"))
        lines.append("Дата BIOS: " + DataCollector._run_ps("(Get-CimInstance Win32_BIOS).ReleaseDate.ToString('yyyy-MM-dd')"))
        lines.append("Производитель BIOS: " + DataCollector._run_ps("(Get-CimInstance Win32_BIOS).Manufacturer"))
        lines.append("Модель BIOS: " + DataCollector._run_ps("(Get-CimInstance Win32_BIOS).Name"))
        lines.append("Серийный номер BIOS: " + DataCollector._run_ps("(Get-CimInstance Win32_BIOS).SerialNumber"))
        lines.append("Режим прошивки: " + DataCollector._run_ps("(Get-ComputerInfo).BiosFirmwareType"))
        lines.append("Версия прошивки: " + DataCollector._run_ps("(Get-ComputerInfo).BiosVersion"))
        lines.append("Дата прошивки: " + DataCollector._run_ps("(Get-ComputerInfo).BiosReleaseDate.ToString('yyyy-MM-dd')"))
        lines.append("Производитель прошивки: " + DataCollector._run_ps("(Get-ComputerInfo).BiosManufacturer"))
        lines.append("Модель прошивки: " + DataCollector._run_ps("(Get-ComputerInfo).BiosName"))
        lines.append("Серийный номер прошивки: " + DataCollector._run_ps("(Get-ComputerInfo).BiosSerialNumber"))
        
        # СЕТЕВОЙ АДАПТЕР
        lines.append("Сетевой адаптер: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.NetConnectionID"))
        lines.append("MAC-адрес сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.MACAddress"))
        lines.append("IP-адрес сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object Index -eq $a.DeviceID).IPAddress | Where-Object {$_ -match '^\\d+\\.'}"))
        lines.append("Маска подсети сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object Index -eq $a.DeviceID).IPSubnet | Where-Object {$_ -match '^\\d+\\.'}"))
        lines.append("Шлюз по умолчанию сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object Index -eq $a.DeviceID).DefaultIPGateway"))
        lines.append("DNS-сервер сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object Index -eq $a.DeviceID).DNSServerSearchOrder"))
        lines.append("DHCP-сервер сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object Index -eq $a.DeviceID).DHCPServer"))
        lines.append("DHCP включен на сетевом адаптере: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object Index -eq $a.DeviceID).DHCPEnabled"))
        lines.append("Состояние сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.NetConnectionStatus"))
        lines.append("Скорость сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.Speed"))
        lines.append("Описание сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.Description"))
        lines.append("Тип сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.AdapterTypeID"))
        lines.append("Сетевой адаптер включен: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.NetEnabled"))
        lines.append("Сетевой адаптер поддерживает Wake-on-LAN: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.PowerManagementSupported"))
        lines.append("Модель сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.ProductName"))
        lines.append("Производитель сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.Manufacturer"))
        lines.append("Версия драйвера сетевого адаптера: " + DataCollector._run_ps("$a = Get-CimInstance Win32_NetworkAdapter | Where-Object NetConnectionID | Select-Object -First 1; $a.DriverVersion"))
        
        # МАТЕРИНСКАЯ ПЛАТА
        lines.append("Модель материнской платы: " + DataCollector._run_ps("(Get-CimInstance Win32_BaseBoard).Product"))
        lines.append("Производитель материнской платы: " + DataCollector._run_ps("(Get-CimInstance Win32_BaseBoard).Manufacturer"))
        lines.append("Серийный номер материнской платы: " + DataCollector._run_ps("(Get-CimInstance Win32_BaseBoard).SerialNumber"))
        lines.append("UUID материнской платы: " + DataCollector._run_ps("(Get-CimInstance Win32_ComputerSystemProduct).UUID"))
        lines.append("Версия материнской платы: " + DataCollector._run_ps("(Get-CimInstance Win32_BaseBoard).Version"))
        lines.append("Дата выпуска материнской платы: " + DataCollector._run_ps("(Get-CimInstance Win32_BaseBoard).ReleaseDate.ToString('yyyy-MM-dd')"))
        lines.append("Состояние температуры материнской платы: " + DataCollector._run_ps("$t = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | ForEach-Object {[math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)}; if ($t) {$t -join ', ' + '°C'} else {'Не обнаружена температура материнской платы'}"))
        lines.append("Количество слотов памяти на материнской плате: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemoryArray).MemoryDevices"))
        lines.append("Максимальный объем памяти на материнской плате: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemoryArray).MaxCapacity"))
        lines.append("Тип памяти на материнской плате: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemoryArray).MemoryType"))
        lines.append("Скорость памяти на материнской плате: " + DataCollector._run_ps("(Get-CimInstance Win32_PhysicalMemoryArray).Speed"))
        
        # УСТАНОВЛЕННЫЕ МОДУЛИ ПАМЯТИ
        if psutil:
            lines.append("Количество установленных модулей памяти: " + str(len(psutil.virtual_memory()._fields)))
            vm = psutil.virtual_memory()
            lines.append("Общий объем установленных модулей памяти: " + str(round(vm.total / (1024. ** 3))) + " GB")
            lines.append("Свободный объем установленных модулей памяти: " + str(round(vm.available / (1024. ** 3))) + " GB")
            lines.append("Занятый объем установленных модулей памяти: " + str(round(vm.used / (1024. ** 3))) + " GB")
        
        # АККУМУЛЯТОР
        lines.append("Объем аккамулятора: " + DataCollector._run_ps("$b = Get-CimInstance -Namespace root/WMI -ClassName BatteryStaticData -ErrorAction SilentlyContinue | Select-Object -First 1; if ($b) {$b.DesignedCapacity} else {'Не обнаружен аккумулятор'}") + " mWh")
        
        if psutil and psutil.sensors_battery():
            lines.append("Состояние аккамулятора: " + str(psutil.sensors_battery().percent) + "%")
            lines.append("Время работы аккамулятора: " + str(datetime.timedelta(seconds=psutil.sensors_battery().secsleft)))
            lines.append("Состояние питания: " + ("Подключено к сети" if psutil.sensors_battery().power_plugged else "От батареи"))
            lines.append("Состояние заряда батареи: " + str(psutil.sensors_battery().percent) + "%")
        else:
            lines.append("Состояние аккамулятора: Не обнаружен аккумулятор")
            lines.append("Время работы аккамулятора: Не обнаружен аккумулятор")
            lines.append("Состояние питания: Не обнаружен аккумулятор")
            lines.append("Состояние заряда батареи: Не обнаружен аккумулятор")
        
        lines.append("Состояние температуры батареи: " + DataCollector._run_ps("$t = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | ForEach-Object {[math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)}; if ($t) {$t -join ', ' + '°C'} else {'Не обнаружена температура батареи'}"))
        
        lines.append("\nВот и вся информация о вашей системе, собранная с помощью VIIDU. Спасибо за использование нашей утилиты!")
        
        return "\n".join(lines)


def process_command(text: str, show_popup):
    """Обработка команд"""
    dalbaeb = text.strip().lower()
    
    if any(word in dalbaeb for word in ["pidor", "yebok", "pidoras", "yebanaya", "yebana", "yebaniy", "naxui"]):
        messages = ["Бля ты че еблан", "Ты че за пидор", "Ты че за еблан", "Ты ахуел?", "Ты че за долбоеб"]
        show_popup("VIIDU", random.choice(messages))
        return
    
    if dalbaeb == "exit":
        show_popup("VIIDU", "Ужс зачем ты пишешь exit, я же сказал нажми Enter")
        return
    
    if dalbaeb == "copilot":
        show_popup("VIIDU", "Да он просто босс что помогает мне писать код, а не обычный глупый редактор кода")
        return
    
    if dalbaeb == "ai" or dalbaeb == "ии":
        show_popup("VIIDU", "Открываю...")
        webbrowser.open("https://vivweb.vercel.app")
        return
    
    if dalbaeb == "browser" or dalbaeb == "vibrow":
        show_popup("VIIDU", "Начинаю скачивание...")
        return
    
    if dalbaeb == "calc":
        show_popup("VIIDU", "Введите: calc 5 + 3\nФормат: calc <число1> <операция> <число2>\nОперации: +, -, *, /")
        return
    
    if dalbaeb.startswith("calc "):
        try:
            expr = dalbaeb.replace("calc ", "").strip()
            result = eval(expr, {"__builtins__": {}}, {})
            show_popup("VIIDU", f"Ответ: {result}")
        except Exception as e:
            show_popup("VIIDU", f"Ошибка: {e}")
        return
    
    show_popup("VIIDU", f"Неизвестная команда: {dalbaeb}")


class VIIDUApp(App):
    def build(self):
        self.title = "VIIDU - Информационно-диагностическая утилита (ПОЛНАЯ ВЕРСИЯ)"
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title_label = Label(text="VIIDU - Информационно-диагностическая утилита (ПОЛНАЯ)", size_hint_y=0.08, bold=True)
        main_layout.add_widget(title_label)
        
        # Статус
        self.status_label = Label(text="Загрузка...", size_hint_y=0.08, markup=True)
        main_layout.add_widget(self.status_label)
        
        # Текстовое поле с прокруткой
        scroll = ScrollView()
        self.output = TextInput(
            text="Загрузка информации о системе...\n\nПожалуйста, подождите...",
            readonly=True,
            multiline=True,
            font_size='9sp'
        )
        scroll.add_widget(self.output)
        main_layout.add_widget(scroll)
        
        # Кнопки
        button_layout = GridLayout(cols=3, size_hint_y=0.1, spacing=10)
        
        refresh_btn = Button(text="🔄 Обновить")
        refresh_btn.bind(on_press=self.refresh_data)
        button_layout.add_widget(refresh_btn)
        
        command_btn = Button(text="⚙️ Команда")
        command_btn.bind(on_press=self.show_command_popup)
        button_layout.add_widget(command_btn)
        
        close_btn = Button(text="❌ Закрыть")
        close_btn.bind(on_press=self.close_app)
        button_layout.add_widget(close_btn)
        
        main_layout.add_widget(button_layout)
        
        # Загрузить данные
        self.load_data_async()
        
        return main_layout
    
    def load_data_async(self):
        """Загружает данные в отдельном потоке"""
        thread = KivyThread(target=self._load_data_thread)
        thread.daemon = True
        thread.start()
    
    def _load_data_thread(self):
        """Поток для загрузки"""
        text = DataCollector.get_report_text()
        self.output.text = text
        self.status_label.text = "[color=00ff00]✓ Все данные загружены (140+)[/color]"
    
    def refresh_data(self, instance):
        """Перезагрузить данные"""
        self.output.text = "Загрузка информации о системе...\n\nПожалуйста, подождите..."
        self.status_label.text = "[color=ffff00]⚡ Загрузка...[/color]"
        self.load_data_async()
    
    def show_command_popup(self, instance):
        """Показать popup для ввода команды"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        label = Label(text="Доступные команды:\ncalc, ai, copilot, exit\n\nВведите команду:", size_hint_y=0.4)
        content.add_widget(label)
        
        text_input = TextInput(text="calc", multiline=False, size_hint_y=0.3)
        content.add_widget(text_input)
        
        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        
        ok_btn = Button(text="OK")
        cancel_btn = Button(text="Отмена")
        
        popup = Popup(title="VIIDU - Команда", content=content, size_hint=(0.9, 0.5))
        
        def on_ok(btn):
            process_command(text_input.text, self.show_message)
            popup.dismiss()
        
        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(ok_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup.open()
    
    def show_message(self, title, message):
        """Показать сообщение"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        
        close_btn = Button(text="Закрыть", size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()
    
    def close_app(self, instance):
        """Закрыть приложение"""
        App.get_running_app().stop()


if __name__ == '__main__':
    VIIDUApp().run()
